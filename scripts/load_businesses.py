"""
Load Auburn businesses from JSON into TIGER_MARKETING database
"""
import json
import os
import sys
import pyodbc
import logging
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'load_businesses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_CONN_STR = 'DRIVER={SQL Server};SERVER=localhost;DATABASE=TIGER_MARKETING;Trusted_Connection=yes;'

def load_businesses(json_file):
    """Load businesses from JSON into TIGER_MARKETING.BUSINESSES"""
    with open(json_file, 'r', encoding='utf-8') as f:
        businesses = json.load(f)

    logger.info(f"Loaded {len(businesses)} businesses from {json_file}")

    conn = pyodbc.connect(DB_CONN_STR, timeout=30)
    cursor = conn.cursor()

    # Check existing count
    cursor.execute("SELECT COUNT(*) FROM BUSINESSES")
    existing = cursor.fetchone()[0]
    logger.info(f"Existing rows in BUSINESSES: {existing}")

    inserted = 0
    skipped = 0

    for biz in businesses:
        name = biz.get('name', '').strip()
        if not name:
            continue

        # Check for duplicate by name + category
        cursor.execute("SELECT COUNT(*) FROM BUSINESSES WHERE NAME = ? AND CATEGORY = ?",
                       name, biz.get('category', ''))
        if cursor.fetchone()[0] > 0:
            skipped += 1
            continue

        lat = biz.get('lat', None)
        lon = biz.get('lon', None)

        # Convert empty strings to None
        if lat == '':
            lat = None
        if lon == '':
            lon = None

        try:
            cursor.execute("""
                INSERT INTO BUSINESSES (NAME, CATEGORY, ADDRESS, CITY, STATE, ZIP,
                                       LATITUDE, LONGITUDE, PHONE, WEBSITE, SOURCE, CREATED_DATE)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OpenStreetMap', GETDATE())
            """,
                name,
                biz.get('category', ''),
                biz.get('full_address', ''),
                biz.get('city', 'Auburn'),
                biz.get('state', 'AL'),
                biz.get('zip', ''),
                lat,
                lon,
                biz.get('phone', ''),
                biz.get('website', '')
            )
            inserted += 1
        except Exception as e:
            logger.error(f"Failed to insert {name}: {e}")

    conn.commit()
    conn.close()

    logger.info(f"Done! Inserted: {inserted}, Skipped (duplicates): {skipped}")
    print(f"\nLoaded into TIGER_MARKETING.BUSINESSES:")
    print(f"  Inserted: {inserted}")
    print(f"  Skipped:  {skipped}")
    print(f"  Total in DB: {inserted + existing}")

    return inserted


if __name__ == '__main__':
    # Find the JSON file
    json_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'OpenClaw', 'auburn_businesses')
    json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
    if not json_files:
        print("No JSON file found in auburn_businesses/")
        sys.exit(1)

    json_file = os.path.join(json_dir, sorted(json_files)[-1])
    print(f"Using: {json_file}")
    load_businesses(json_file)
