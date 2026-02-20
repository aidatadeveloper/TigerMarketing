"""
Initialize SQLite database for Tiger Marketing CRM (PythonAnywhere deployment).
Creates all tables and optionally seeds with data exported from SQL Server.
"""

import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'tiger_crm.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def create_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS CONTACTS (
            CONTACT_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            FIRST_NAME TEXT DEFAULT '',
            LAST_NAME TEXT DEFAULT '',
            COMPANY TEXT DEFAULT '',
            JOB_TITLE TEXT DEFAULT '',
            EMAIL TEXT DEFAULT '',
            PHONE TEXT DEFAULT '',
            ADDRESS TEXT DEFAULT '',
            CITY TEXT DEFAULT 'Auburn',
            STATE TEXT DEFAULT 'AL',
            ZIP TEXT DEFAULT '',
            NEIGHBORHOOD TEXT DEFAULT '',
            CONTACT_TYPE TEXT DEFAULT 'Lead',
            LEAD_SOURCE TEXT DEFAULT '',
            LEAD_STATUS TEXT DEFAULT 'New',
            INTEREST_SERVICES TEXT DEFAULT '',
            PROPERTY_TYPE TEXT DEFAULT '',
            ESTIMATED_VALUE REAL,
            RATING INTEGER,
            NOTES TEXT DEFAULT '',
            ASSIGNED_TO TEXT DEFAULT '',
            DO_NOT_CONTACT INTEGER DEFAULT 0,
            CREATED_DATE TEXT DEFAULT (datetime('now')),
            UPDATED_DATE TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS DEALS (
            DEAL_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            CONTACT_ID INTEGER,
            DEAL_NAME TEXT DEFAULT '',
            SERVICE_TYPE TEXT DEFAULT '',
            STAGE TEXT DEFAULT 'Prospect',
            AMOUNT REAL,
            CLOSE_DATE TEXT,
            PROBABILITY REAL,
            RECURRING INTEGER DEFAULT 0,
            RECURRING_FREQUENCY TEXT DEFAULT '',
            NOTES TEXT DEFAULT '',
            WON_DATE TEXT,
            LOST_REASON TEXT DEFAULT '',
            CREATED_DATE TEXT DEFAULT (datetime('now')),
            UPDATED_DATE TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (CONTACT_ID) REFERENCES CONTACTS(CONTACT_ID)
        );

        CREATE TABLE IF NOT EXISTS INTERACTIONS (
            INTERACTION_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            CONTACT_ID INTEGER,
            INTERACTION_TYPE TEXT DEFAULT '',
            DIRECTION TEXT DEFAULT '',
            SUBJECT TEXT DEFAULT '',
            NOTES TEXT DEFAULT '',
            OUTCOME TEXT DEFAULT '',
            FOLLOW_UP_DATE TEXT,
            CREATED_BY TEXT DEFAULT 'Jason',
            CREATED_DATE TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (CONTACT_ID) REFERENCES CONTACTS(CONTACT_ID)
        );

        CREATE TABLE IF NOT EXISTS TASKS (
            TASK_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            CONTACT_ID INTEGER,
            DEAL_ID INTEGER,
            TASK_TYPE TEXT DEFAULT '',
            DESCRIPTION TEXT DEFAULT '',
            DUE_DATE TEXT,
            PRIORITY TEXT DEFAULT 'Normal',
            STATUS TEXT DEFAULT 'Pending',
            ASSIGNED_TO TEXT DEFAULT 'Jason',
            COMPLETED_DATE TEXT,
            CREATED_DATE TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (CONTACT_ID) REFERENCES CONTACTS(CONTACT_ID),
            FOREIGN KEY (DEAL_ID) REFERENCES DEALS(DEAL_ID)
        );

        CREATE TABLE IF NOT EXISTS CAMPAIGNS (
            CAMPAIGN_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            CAMPAIGN_NAME TEXT DEFAULT '',
            CAMPAIGN_TYPE TEXT DEFAULT '',
            TARGET_AREA TEXT DEFAULT '',
            START_DATE TEXT,
            END_DATE TEXT,
            BUDGET REAL,
            LEADS_GENERATED INTEGER,
            DEALS_WON INTEGER,
            REVENUE_GENERATED REAL,
            STATUS TEXT DEFAULT 'Planned',
            NOTES TEXT DEFAULT '',
            CREATED_DATE TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS CAMPAIGN_CONTACTS (
            CAMPAIGN_CONTACT_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            CAMPAIGN_ID INTEGER,
            CONTACT_ID INTEGER,
            CREATED_DATE TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (CAMPAIGN_ID) REFERENCES CAMPAIGNS(CAMPAIGN_ID),
            FOREIGN KEY (CONTACT_ID) REFERENCES CONTACTS(CONTACT_ID)
        );

        CREATE TABLE IF NOT EXISTS COMPETITORS (
            COMPETITOR_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            COMPANY_NAME TEXT DEFAULT '',
            CATEGORY TEXT DEFAULT '',
            ADDRESS TEXT DEFAULT '',
            CITY TEXT DEFAULT '',
            STATE TEXT DEFAULT '',
            PHONE TEXT DEFAULT '',
            WEBSITE TEXT DEFAULT '',
            RATING REAL,
            REVIEW_COUNT INTEGER,
            PRICE_RANGE TEXT DEFAULT '',
            STRENGTHS TEXT DEFAULT '',
            WEAKNESSES TEXT DEFAULT '',
            NOTES TEXT DEFAULT '',
            GOOGLE_PLACE_ID TEXT DEFAULT '',
            LATITUDE REAL,
            LONGITUDE REAL,
            CREATED_DATE TEXT DEFAULT (datetime('now'))
        );
    """)

    conn.commit()
    print("All tables created successfully!")

    # Show table counts
    tables = ['CONTACTS', 'DEALS', 'INTERACTIONS', 'TASKS', 'CAMPAIGNS', 'COMPETITORS']
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  {t}: {cur.fetchone()[0]} rows")

    conn.close()


def export_from_sqlserver():
    """Export data from local SQL Server to JSON files for cloud import."""
    try:
        import pyodbc
    except ImportError:
        print("pyodbc not available - skip SQL Server export")
        return

    ss_conn = pyodbc.connect(
        'DRIVER={SQL Server};SERVER=localhost;DATABASE=TIGER_MARKETING;Trusted_Connection=yes;',
        timeout=30
    )
    cur = ss_conn.cursor()

    export_dir = os.path.join(os.path.dirname(__file__), 'data_export')
    os.makedirs(export_dir, exist_ok=True)

    tables = {
        'CONTACTS': 'SELECT * FROM CONTACTS ORDER BY CONTACT_ID',
        'DEALS': 'SELECT * FROM DEALS ORDER BY DEAL_ID',
        'INTERACTIONS': 'SELECT * FROM INTERACTIONS ORDER BY INTERACTION_ID',
        'TASKS': 'SELECT * FROM TASKS ORDER BY TASK_ID',
        'CAMPAIGNS': 'SELECT * FROM CAMPAIGNS ORDER BY CAMPAIGN_ID',
        'COMPETITORS': 'SELECT * FROM COMPETITORS ORDER BY COMPETITOR_ID',
    }

    for table_name, query in tables.items():
        try:
            cur.execute(query)
            columns = [col[0] for col in cur.description]
            rows = []
            for row in cur.fetchall():
                d = {}
                for col, val in zip(columns, row):
                    if val is not None and hasattr(val, 'isoformat'):
                        val = val.isoformat()
                    elif isinstance(val, (int, float, str, bool)):
                        pass
                    elif val is not None:
                        val = str(val)
                    d[col] = val
                rows.append(d)

            filepath = os.path.join(export_dir, f'{table_name}.json')
            with open(filepath, 'w') as f:
                json.dump(rows, f, indent=2, default=str)
            print(f"  Exported {table_name}: {len(rows)} rows -> {filepath}")
        except Exception as e:
            print(f"  Error exporting {table_name}: {e}")

    ss_conn.close()
    print("Export complete!")


def import_to_sqlite():
    """Import JSON data files into SQLite."""
    export_dir = os.path.join(os.path.dirname(__file__), 'data_export')
    if not os.path.exists(export_dir):
        print("No data_export folder found. Run export_from_sqlserver() first.")
        return

    conn = get_db()
    cur = conn.cursor()

    # Order matters for foreign keys
    tables = ['CONTACTS', 'DEALS', 'INTERACTIONS', 'TASKS', 'CAMPAIGNS', 'COMPETITORS']

    for table_name in tables:
        filepath = os.path.join(export_dir, f'{table_name}.json')
        if not os.path.exists(filepath):
            print(f"  {table_name}: no export file found, skipping")
            continue

        with open(filepath, 'r') as f:
            rows = json.load(f)

        if not rows:
            print(f"  {table_name}: 0 rows")
            continue

        # Get columns from first row (skip auto-increment ID)
        columns = list(rows[0].keys())

        for row in rows:
            cols = [c for c in columns if row.get(c) is not None]
            placeholders = ', '.join(['?' for _ in cols])
            col_names = ', '.join(cols)
            values = [row[c] for c in cols]

            try:
                cur.execute(f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})", values)
            except Exception as e:
                print(f"  Error inserting into {table_name}: {e}")

        conn.commit()
        print(f"  Imported {table_name}: {len(rows)} rows")

    conn.close()
    print("Import complete!")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'export':
            print("Exporting from SQL Server...")
            export_from_sqlserver()
        elif cmd == 'import':
            print("Creating tables...")
            create_tables()
            print("Importing data...")
            import_to_sqlite()
        elif cmd == 'full':
            print("Full pipeline: export -> create -> import")
            export_from_sqlserver()
            create_tables()
            import_to_sqlite()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python init_db.py [export|import|full]")
    else:
        print("Creating SQLite database...")
        create_tables()
        print(f"\nDatabase created at: {DB_PATH}")
        print("\nTo export from SQL Server:  python init_db.py export")
        print("To import into SQLite:      python init_db.py import")
        print("To do both:                 python init_db.py full")
