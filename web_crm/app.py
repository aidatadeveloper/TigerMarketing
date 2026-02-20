"""
Tiger Marketing CRM - Web Application
Flask-based CRM connected to TIGER_MARKETING SQL Server database
"""

import os
import pyodbc
import logging
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from decimal import Decimal

# --- Logging Setup ---
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f'web_crm_{datetime.now():%Y%m%d}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'tiger-marketing-crm-2026'

DB_CONN_STR = 'DRIVER={SQL Server};SERVER=localhost;DATABASE=TIGER_MARKETING;Trusted_Connection=yes;'


def get_db():
    """Get database connection."""
    return pyodbc.connect(DB_CONN_STR, timeout=30)


def row_to_dict(cursor, row):
    """Convert a pyodbc row to a dictionary."""
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    d = {}
    for col, val in zip(columns, row):
        if isinstance(val, Decimal):
            val = float(val)
        elif isinstance(val, datetime):
            val = val.isoformat()
        elif isinstance(val, date):
            val = val.isoformat()
        d[col] = val
    return d


def rows_to_list(cursor, rows):
    """Convert multiple pyodbc rows to a list of dicts."""
    return [row_to_dict(cursor, row) for row in rows]


# ============================================================
# DASHBOARD
# ============================================================
@app.route('/')
def dashboard():
    """Main dashboard with key metrics."""
    conn = get_db()
    cur = conn.cursor()
    try:
        # Key metrics
        cur.execute("SELECT COUNT(*) FROM CONTACTS")
        total_contacts = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM CONTACTS WHERE LEAD_STATUS = 'New'")
        new_leads = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM DEALS WHERE STAGE NOT IN ('Won', 'Lost')")
        active_deals = cur.fetchone()[0]

        cur.execute("SELECT ISNULL(SUM(AMOUNT), 0) FROM DEALS WHERE STAGE NOT IN ('Won', 'Lost')")
        pipeline_value = float(cur.fetchone()[0])

        cur.execute("SELECT ISNULL(SUM(AMOUNT), 0) FROM DEALS WHERE STAGE = 'Won'")
        won_revenue = float(cur.fetchone()[0])

        cur.execute("SELECT COUNT(*) FROM DEALS WHERE STAGE = 'Won'")
        won_deals = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM TASKS WHERE STATUS != 'Completed'")
        open_tasks = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM TASKS WHERE STATUS != 'Completed' AND DUE_DATE <= CAST(GETDATE() AS DATE)")
        overdue_tasks = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM CAMPAIGNS WHERE STATUS = 'Active'")
        active_campaigns = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM COMPETITORS")
        total_competitors = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM INTERACTIONS")
        total_interactions = cur.fetchone()[0]

        # Recent contacts
        cur.execute("SELECT TOP 5 * FROM CONTACTS ORDER BY CREATED_DATE DESC")
        recent_contacts = rows_to_list(cur, cur.fetchall())

        # Recent deals
        cur.execute("""
            SELECT TOP 5 d.*, c.FIRST_NAME + ' ' + c.LAST_NAME AS CONTACT_NAME
            FROM DEALS d
            LEFT JOIN CONTACTS c ON d.CONTACT_ID = c.CONTACT_ID
            ORDER BY d.CREATED_DATE DESC
        """)
        recent_deals = rows_to_list(cur, cur.fetchall())

        # Upcoming tasks
        cur.execute("""
            SELECT TOP 5 t.*, c.FIRST_NAME + ' ' + c.LAST_NAME AS CONTACT_NAME
            FROM TASKS t
            LEFT JOIN CONTACTS c ON t.CONTACT_ID = c.CONTACT_ID
            WHERE t.STATUS != 'Completed'
            ORDER BY t.DUE_DATE ASC
        """)
        upcoming_tasks = rows_to_list(cur, cur.fetchall())

        # Pipeline by stage
        cur.execute("""
            SELECT STAGE, COUNT(*) AS CNT, ISNULL(SUM(AMOUNT), 0) AS TOTAL
            FROM DEALS
            WHERE STAGE NOT IN ('Won', 'Lost')
            GROUP BY STAGE
            ORDER BY CASE STAGE
                WHEN 'Prospect' THEN 1
                WHEN 'Quoted' THEN 2
                WHEN 'Negotiation' THEN 3
                WHEN 'Scheduled' THEN 4
                ELSE 5
            END
        """)
        pipeline_stages = rows_to_list(cur, cur.fetchall())

        # Contacts by lead status
        cur.execute("""
            SELECT LEAD_STATUS, COUNT(*) AS CNT
            FROM CONTACTS
            GROUP BY LEAD_STATUS
            ORDER BY CNT DESC
        """)
        leads_by_status = rows_to_list(cur, cur.fetchall())

        return render_template('dashboard.html',
            total_contacts=total_contacts,
            new_leads=new_leads,
            active_deals=active_deals,
            pipeline_value=pipeline_value,
            won_revenue=won_revenue,
            won_deals=won_deals,
            open_tasks=open_tasks,
            overdue_tasks=overdue_tasks,
            active_campaigns=active_campaigns,
            total_competitors=total_competitors,
            total_interactions=total_interactions,
            recent_contacts=recent_contacts,
            recent_deals=recent_deals,
            upcoming_tasks=upcoming_tasks,
            pipeline_stages=pipeline_stages,
            leads_by_status=leads_by_status
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('dashboard.html', error=str(e))
    finally:
        conn.close()


# ============================================================
# CONTACTS
# ============================================================
@app.route('/contacts')
def contacts_list():
    """List all contacts with filtering."""
    conn = get_db()
    cur = conn.cursor()
    try:
        status_filter = request.args.get('status', '')
        type_filter = request.args.get('type', '')
        search = request.args.get('search', '')

        query = "SELECT * FROM CONTACTS WHERE 1=1"
        params = []

        if status_filter:
            query += " AND LEAD_STATUS = ?"
            params.append(status_filter)
        if type_filter:
            query += " AND CONTACT_TYPE = ?"
            params.append(type_filter)
        if search:
            query += " AND (FIRST_NAME LIKE ? OR LAST_NAME LIKE ? OR COMPANY LIKE ? OR EMAIL LIKE ? OR PHONE LIKE ?)"
            s = f'%{search}%'
            params.extend([s, s, s, s, s])

        query += " ORDER BY CREATED_DATE DESC"
        cur.execute(query, params)
        contacts = rows_to_list(cur, cur.fetchall())

        # Get distinct values for filters
        cur.execute("SELECT DISTINCT LEAD_STATUS FROM CONTACTS WHERE LEAD_STATUS IS NOT NULL ORDER BY LEAD_STATUS")
        statuses = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT DISTINCT CONTACT_TYPE FROM CONTACTS WHERE CONTACT_TYPE IS NOT NULL ORDER BY CONTACT_TYPE")
        types = [r[0] for r in cur.fetchall()]

        return render_template('contacts.html', contacts=contacts, statuses=statuses,
                             types=types, status_filter=status_filter, type_filter=type_filter, search=search)
    except Exception as e:
        logger.error(f"Contacts list error: {e}")
        return render_template('contacts.html', contacts=[], error=str(e))
    finally:
        conn.close()


@app.route('/contacts/new', methods=['GET', 'POST'])
def contact_new():
    """Create a new contact."""
    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO CONTACTS (FIRST_NAME, LAST_NAME, COMPANY, JOB_TITLE, EMAIL, PHONE,
                    ADDRESS, CITY, STATE, ZIP, NEIGHBORHOOD, CONTACT_TYPE, LEAD_SOURCE,
                    LEAD_STATUS, INTEREST_SERVICES, PROPERTY_TYPE, ESTIMATED_VALUE, RATING,
                    NOTES, ASSIGNED_TO, DO_NOT_CONTACT, CREATED_DATE, UPDATED_DATE)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            """, (
                request.form.get('first_name', ''),
                request.form.get('last_name', ''),
                request.form.get('company', ''),
                request.form.get('job_title', ''),
                request.form.get('email', ''),
                request.form.get('phone', ''),
                request.form.get('address', ''),
                request.form.get('city', 'Auburn'),
                request.form.get('state', 'AL'),
                request.form.get('zip', ''),
                request.form.get('neighborhood', ''),
                request.form.get('contact_type', 'Lead'),
                request.form.get('lead_source', ''),
                request.form.get('lead_status', 'New'),
                request.form.get('interest_services', ''),
                request.form.get('property_type', ''),
                request.form.get('estimated_value') or None,
                request.form.get('rating') or None,
                request.form.get('notes', ''),
                request.form.get('assigned_to', ''),
                1 if request.form.get('do_not_contact') else 0
            ))
            conn.commit()
            flash('Contact created successfully!', 'success')
            return redirect(url_for('contacts_list'))
        except Exception as e:
            logger.error(f"Create contact error: {e}")
            flash(f'Error creating contact: {e}', 'error')
        finally:
            conn.close()
    return render_template('contact_form.html', contact=None, mode='new')


@app.route('/contacts/<int:contact_id>')
def contact_detail(contact_id):
    """View contact detail with deals, interactions, tasks."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM CONTACTS WHERE CONTACT_ID = ?", (contact_id,))
        contact = row_to_dict(cur, cur.fetchone())
        if not contact:
            flash('Contact not found', 'error')
            return redirect(url_for('contacts_list'))

        cur.execute("SELECT * FROM DEALS WHERE CONTACT_ID = ? ORDER BY CREATED_DATE DESC", (contact_id,))
        deals = rows_to_list(cur, cur.fetchall())

        cur.execute("SELECT * FROM INTERACTIONS WHERE CONTACT_ID = ? ORDER BY CREATED_DATE DESC", (contact_id,))
        interactions = rows_to_list(cur, cur.fetchall())

        cur.execute("SELECT * FROM TASKS WHERE CONTACT_ID = ? ORDER BY DUE_DATE ASC", (contact_id,))
        tasks = rows_to_list(cur, cur.fetchall())

        return render_template('contact_detail.html', contact=contact, deals=deals,
                             interactions=interactions, tasks=tasks)
    except Exception as e:
        logger.error(f"Contact detail error: {e}")
        flash(f'Error: {e}', 'error')
        return redirect(url_for('contacts_list'))
    finally:
        conn.close()


@app.route('/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
def contact_edit(contact_id):
    """Edit a contact."""
    conn = get_db()
    cur = conn.cursor()
    try:
        if request.method == 'POST':
            cur.execute("""
                UPDATE CONTACTS SET
                    FIRST_NAME=?, LAST_NAME=?, COMPANY=?, JOB_TITLE=?, EMAIL=?, PHONE=?,
                    ADDRESS=?, CITY=?, STATE=?, ZIP=?, NEIGHBORHOOD=?, CONTACT_TYPE=?,
                    LEAD_SOURCE=?, LEAD_STATUS=?, INTEREST_SERVICES=?, PROPERTY_TYPE=?,
                    ESTIMATED_VALUE=?, RATING=?, NOTES=?, ASSIGNED_TO=?, DO_NOT_CONTACT=?,
                    UPDATED_DATE=GETDATE()
                WHERE CONTACT_ID=?
            """, (
                request.form.get('first_name', ''),
                request.form.get('last_name', ''),
                request.form.get('company', ''),
                request.form.get('job_title', ''),
                request.form.get('email', ''),
                request.form.get('phone', ''),
                request.form.get('address', ''),
                request.form.get('city', ''),
                request.form.get('state', ''),
                request.form.get('zip', ''),
                request.form.get('neighborhood', ''),
                request.form.get('contact_type', ''),
                request.form.get('lead_source', ''),
                request.form.get('lead_status', ''),
                request.form.get('interest_services', ''),
                request.form.get('property_type', ''),
                request.form.get('estimated_value') or None,
                request.form.get('rating') or None,
                request.form.get('notes', ''),
                request.form.get('assigned_to', ''),
                1 if request.form.get('do_not_contact') else 0,
                contact_id
            ))
            conn.commit()
            flash('Contact updated!', 'success')
            return redirect(url_for('contact_detail', contact_id=contact_id))

        cur.execute("SELECT * FROM CONTACTS WHERE CONTACT_ID = ?", (contact_id,))
        contact = row_to_dict(cur, cur.fetchone())
        return render_template('contact_form.html', contact=contact, mode='edit')
    except Exception as e:
        logger.error(f"Edit contact error: {e}")
        flash(f'Error: {e}', 'error')
        return redirect(url_for('contacts_list'))
    finally:
        conn.close()


@app.route('/contacts/<int:contact_id>/delete', methods=['POST'])
def contact_delete(contact_id):
    """Delete a contact."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM INTERACTIONS WHERE CONTACT_ID = ?", (contact_id,))
        cur.execute("DELETE FROM TASKS WHERE CONTACT_ID = ?", (contact_id,))
        cur.execute("DELETE FROM DEALS WHERE CONTACT_ID = ?", (contact_id,))
        cur.execute("DELETE FROM CAMPAIGN_CONTACTS WHERE CONTACT_ID = ?", (contact_id,))
        cur.execute("DELETE FROM CONTACTS WHERE CONTACT_ID = ?", (contact_id,))
        conn.commit()
        flash('Contact deleted.', 'success')
    except Exception as e:
        logger.error(f"Delete contact error: {e}")
        flash(f'Error: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('contacts_list'))


# ============================================================
# DEALS
# ============================================================
@app.route('/deals')
def deals_list():
    """List all deals / pipeline view."""
    conn = get_db()
    cur = conn.cursor()
    try:
        stage_filter = request.args.get('stage', '')
        query = """
            SELECT d.*, c.FIRST_NAME + ' ' + c.LAST_NAME AS CONTACT_NAME
            FROM DEALS d
            LEFT JOIN CONTACTS c ON d.CONTACT_ID = c.CONTACT_ID
            WHERE 1=1
        """
        params = []
        if stage_filter:
            query += " AND d.STAGE = ?"
            params.append(stage_filter)
        query += " ORDER BY d.CREATED_DATE DESC"
        cur.execute(query, params)
        deals = rows_to_list(cur, cur.fetchall())

        cur.execute("SELECT DISTINCT STAGE FROM DEALS WHERE STAGE IS NOT NULL ORDER BY STAGE")
        stages = [r[0] for r in cur.fetchall()]

        # Pipeline summary
        cur.execute("""
            SELECT STAGE, COUNT(*) AS CNT, ISNULL(SUM(AMOUNT), 0) AS TOTAL
            FROM DEALS GROUP BY STAGE
        """)
        pipeline = rows_to_list(cur, cur.fetchall())

        return render_template('deals.html', deals=deals, stages=stages,
                             stage_filter=stage_filter, pipeline=pipeline)
    except Exception as e:
        logger.error(f"Deals list error: {e}")
        return render_template('deals.html', deals=[], error=str(e))
    finally:
        conn.close()


@app.route('/deals/new', methods=['GET', 'POST'])
def deal_new():
    """Create a new deal."""
    conn = get_db()
    cur = conn.cursor()
    try:
        if request.method == 'POST':
            cur.execute("""
                INSERT INTO DEALS (CONTACT_ID, DEAL_NAME, SERVICE_TYPE, STAGE, AMOUNT,
                    CLOSE_DATE, PROBABILITY, RECURRING, RECURRING_FREQUENCY, NOTES,
                    CREATED_DATE, UPDATED_DATE)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            """, (
                request.form.get('contact_id') or None,
                request.form.get('deal_name', ''),
                request.form.get('service_type', ''),
                request.form.get('stage', 'Prospect'),
                request.form.get('amount') or None,
                request.form.get('close_date') or None,
                request.form.get('probability') or None,
                1 if request.form.get('recurring') else 0,
                request.form.get('recurring_frequency', ''),
                request.form.get('notes', '')
            ))
            conn.commit()
            flash('Deal created!', 'success')
            return redirect(url_for('deals_list'))

        cur.execute("SELECT CONTACT_ID, FIRST_NAME + ' ' + LAST_NAME AS NAME FROM CONTACTS ORDER BY FIRST_NAME")
        contacts = rows_to_list(cur, cur.fetchall())
        return render_template('deal_form.html', deal=None, contacts=contacts, mode='new')
    except Exception as e:
        logger.error(f"Create deal error: {e}")
        flash(f'Error: {e}', 'error')
        return redirect(url_for('deals_list'))
    finally:
        conn.close()


@app.route('/deals/<int:deal_id>/edit', methods=['GET', 'POST'])
def deal_edit(deal_id):
    """Edit a deal."""
    conn = get_db()
    cur = conn.cursor()
    try:
        if request.method == 'POST':
            cur.execute("""
                UPDATE DEALS SET
                    CONTACT_ID=?, DEAL_NAME=?, SERVICE_TYPE=?, STAGE=?, AMOUNT=?,
                    CLOSE_DATE=?, PROBABILITY=?, RECURRING=?, RECURRING_FREQUENCY=?, NOTES=?,
                    WON_DATE=?, LOST_REASON=?, UPDATED_DATE=GETDATE()
                WHERE DEAL_ID=?
            """, (
                request.form.get('contact_id') or None,
                request.form.get('deal_name', ''),
                request.form.get('service_type', ''),
                request.form.get('stage', ''),
                request.form.get('amount') or None,
                request.form.get('close_date') or None,
                request.form.get('probability') or None,
                1 if request.form.get('recurring') else 0,
                request.form.get('recurring_frequency', ''),
                request.form.get('notes', ''),
                request.form.get('won_date') or None,
                request.form.get('lost_reason', ''),
                deal_id
            ))
            conn.commit()
            flash('Deal updated!', 'success')
            return redirect(url_for('deals_list'))

        cur.execute("SELECT * FROM DEALS WHERE DEAL_ID = ?", (deal_id,))
        deal = row_to_dict(cur, cur.fetchone())
        cur.execute("SELECT CONTACT_ID, FIRST_NAME + ' ' + LAST_NAME AS NAME FROM CONTACTS ORDER BY FIRST_NAME")
        contacts = rows_to_list(cur, cur.fetchall())
        return render_template('deal_form.html', deal=deal, contacts=contacts, mode='edit')
    except Exception as e:
        logger.error(f"Edit deal error: {e}")
        flash(f'Error: {e}', 'error')
        return redirect(url_for('deals_list'))
    finally:
        conn.close()


@app.route('/deals/<int:deal_id>/delete', methods=['POST'])
def deal_delete(deal_id):
    """Delete a deal."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM DEALS WHERE DEAL_ID = ?", (deal_id,))
        conn.commit()
        flash('Deal deleted.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('deals_list'))


# ============================================================
# INTERACTIONS
# ============================================================
@app.route('/interactions')
def interactions_list():
    """List all interactions."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT i.*, c.FIRST_NAME + ' ' + c.LAST_NAME AS CONTACT_NAME
            FROM INTERACTIONS i
            LEFT JOIN CONTACTS c ON i.CONTACT_ID = c.CONTACT_ID
            ORDER BY i.CREATED_DATE DESC
        """)
        interactions = rows_to_list(cur, cur.fetchall())
        return render_template('interactions.html', interactions=interactions)
    except Exception as e:
        logger.error(f"Interactions error: {e}")
        return render_template('interactions.html', interactions=[], error=str(e))
    finally:
        conn.close()


@app.route('/interactions/new', methods=['GET', 'POST'])
def interaction_new():
    """Log a new interaction."""
    conn = get_db()
    cur = conn.cursor()
    try:
        if request.method == 'POST':
            cur.execute("""
                INSERT INTO INTERACTIONS (CONTACT_ID, INTERACTION_TYPE, DIRECTION, SUBJECT,
                    NOTES, OUTCOME, FOLLOW_UP_DATE, CREATED_BY, CREATED_DATE)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                request.form.get('contact_id') or None,
                request.form.get('interaction_type', ''),
                request.form.get('direction', ''),
                request.form.get('subject', ''),
                request.form.get('notes', ''),
                request.form.get('outcome', ''),
                request.form.get('follow_up_date') or None,
                request.form.get('created_by', 'Jason')
            ))
            conn.commit()
            flash('Interaction logged!', 'success')
            # Redirect back to contact if came from one
            contact_id = request.form.get('contact_id')
            if contact_id:
                return redirect(url_for('contact_detail', contact_id=contact_id))
            return redirect(url_for('interactions_list'))

        cur.execute("SELECT CONTACT_ID, FIRST_NAME + ' ' + LAST_NAME AS NAME FROM CONTACTS ORDER BY FIRST_NAME")
        contacts = rows_to_list(cur, cur.fetchall())
        preselect_contact = request.args.get('contact_id', '')
        return render_template('interaction_form.html', contacts=contacts, preselect_contact=preselect_contact)
    except Exception as e:
        logger.error(f"Create interaction error: {e}")
        flash(f'Error: {e}', 'error')
        return redirect(url_for('interactions_list'))
    finally:
        conn.close()


# ============================================================
# TASKS
# ============================================================
@app.route('/tasks')
def tasks_list():
    """List all tasks."""
    conn = get_db()
    cur = conn.cursor()
    try:
        status_filter = request.args.get('status', '')
        query = """
            SELECT t.*, c.FIRST_NAME + ' ' + c.LAST_NAME AS CONTACT_NAME
            FROM TASKS t
            LEFT JOIN CONTACTS c ON t.CONTACT_ID = c.CONTACT_ID
            WHERE 1=1
        """
        params = []
        if status_filter:
            query += " AND t.STATUS = ?"
            params.append(status_filter)
        query += " ORDER BY CASE WHEN t.STATUS = 'Completed' THEN 1 ELSE 0 END, t.DUE_DATE ASC"
        cur.execute(query, params)
        tasks = rows_to_list(cur, cur.fetchall())
        return render_template('tasks.html', tasks=tasks, status_filter=status_filter)
    except Exception as e:
        logger.error(f"Tasks error: {e}")
        return render_template('tasks.html', tasks=[], error=str(e))
    finally:
        conn.close()


@app.route('/tasks/new', methods=['GET', 'POST'])
def task_new():
    """Create a new task."""
    conn = get_db()
    cur = conn.cursor()
    try:
        if request.method == 'POST':
            cur.execute("""
                INSERT INTO TASKS (CONTACT_ID, DEAL_ID, TASK_TYPE, DESCRIPTION, DUE_DATE,
                    PRIORITY, STATUS, ASSIGNED_TO, CREATED_DATE)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                request.form.get('contact_id') or None,
                request.form.get('deal_id') or None,
                request.form.get('task_type', ''),
                request.form.get('description', ''),
                request.form.get('due_date') or None,
                request.form.get('priority', 'Normal'),
                request.form.get('status', 'Pending'),
                request.form.get('assigned_to', 'Jason')
            ))
            conn.commit()
            flash('Task created!', 'success')
            contact_id = request.form.get('contact_id')
            if contact_id:
                return redirect(url_for('contact_detail', contact_id=contact_id))
            return redirect(url_for('tasks_list'))

        cur.execute("SELECT CONTACT_ID, FIRST_NAME + ' ' + LAST_NAME AS NAME FROM CONTACTS ORDER BY FIRST_NAME")
        contacts = rows_to_list(cur, cur.fetchall())
        cur.execute("SELECT DEAL_ID, DEAL_NAME FROM DEALS ORDER BY DEAL_NAME")
        deals = rows_to_list(cur, cur.fetchall())
        preselect_contact = request.args.get('contact_id', '')
        return render_template('task_form.html', contacts=contacts, deals=deals, preselect_contact=preselect_contact)
    except Exception as e:
        logger.error(f"Create task error: {e}")
        flash(f'Error: {e}', 'error')
        return redirect(url_for('tasks_list'))
    finally:
        conn.close()


@app.route('/tasks/<int:task_id>/complete', methods=['POST'])
def task_complete(task_id):
    """Mark a task as completed."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE TASKS SET STATUS = 'Completed', COMPLETED_DATE = GETDATE() WHERE TASK_ID = ?", (task_id,))
        conn.commit()
        flash('Task completed!', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    finally:
        conn.close()
    return redirect(request.referrer or url_for('tasks_list'))


@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
def task_delete(task_id):
    """Delete a task."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM TASKS WHERE TASK_ID = ?", (task_id,))
        conn.commit()
        flash('Task deleted.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('tasks_list'))


# ============================================================
# CAMPAIGNS
# ============================================================
@app.route('/campaigns')
def campaigns_list():
    """List all campaigns."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM CAMPAIGNS ORDER BY CREATED_DATE DESC")
        campaigns = rows_to_list(cur, cur.fetchall())
        return render_template('campaigns.html', campaigns=campaigns)
    except Exception as e:
        logger.error(f"Campaigns error: {e}")
        return render_template('campaigns.html', campaigns=[], error=str(e))
    finally:
        conn.close()


@app.route('/campaigns/new', methods=['GET', 'POST'])
def campaign_new():
    """Create a new campaign."""
    conn = get_db()
    cur = conn.cursor()
    try:
        if request.method == 'POST':
            cur.execute("""
                INSERT INTO CAMPAIGNS (CAMPAIGN_NAME, CAMPAIGN_TYPE, TARGET_AREA, START_DATE,
                    END_DATE, BUDGET, STATUS, NOTES, CREATED_DATE)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                request.form.get('campaign_name', ''),
                request.form.get('campaign_type', ''),
                request.form.get('target_area', ''),
                request.form.get('start_date') or None,
                request.form.get('end_date') or None,
                request.form.get('budget') or None,
                request.form.get('status', 'Planned'),
                request.form.get('notes', '')
            ))
            conn.commit()
            flash('Campaign created!', 'success')
            return redirect(url_for('campaigns_list'))

        return render_template('campaign_form.html', campaign=None, mode='new')
    except Exception as e:
        logger.error(f"Create campaign error: {e}")
        flash(f'Error: {e}', 'error')
        return redirect(url_for('campaigns_list'))
    finally:
        conn.close()


@app.route('/campaigns/<int:campaign_id>/edit', methods=['GET', 'POST'])
def campaign_edit(campaign_id):
    """Edit a campaign."""
    conn = get_db()
    cur = conn.cursor()
    try:
        if request.method == 'POST':
            cur.execute("""
                UPDATE CAMPAIGNS SET
                    CAMPAIGN_NAME=?, CAMPAIGN_TYPE=?, TARGET_AREA=?, START_DATE=?,
                    END_DATE=?, BUDGET=?, LEADS_GENERATED=?, DEALS_WON=?,
                    REVENUE_GENERATED=?, STATUS=?, NOTES=?
                WHERE CAMPAIGN_ID=?
            """, (
                request.form.get('campaign_name', ''),
                request.form.get('campaign_type', ''),
                request.form.get('target_area', ''),
                request.form.get('start_date') or None,
                request.form.get('end_date') or None,
                request.form.get('budget') or None,
                request.form.get('leads_generated') or None,
                request.form.get('deals_won') or None,
                request.form.get('revenue_generated') or None,
                request.form.get('status', ''),
                request.form.get('notes', ''),
                campaign_id
            ))
            conn.commit()
            flash('Campaign updated!', 'success')
            return redirect(url_for('campaigns_list'))

        cur.execute("SELECT * FROM CAMPAIGNS WHERE CAMPAIGN_ID = ?", (campaign_id,))
        campaign = row_to_dict(cur, cur.fetchone())
        return render_template('campaign_form.html', campaign=campaign, mode='edit')
    except Exception as e:
        logger.error(f"Edit campaign error: {e}")
        flash(f'Error: {e}', 'error')
        return redirect(url_for('campaigns_list'))
    finally:
        conn.close()


# ============================================================
# COMPETITORS
# ============================================================
@app.route('/competitors')
def competitors_list():
    """List all competitors."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM COMPETITORS ORDER BY RATING DESC")
        competitors = rows_to_list(cur, cur.fetchall())
        return render_template('competitors.html', competitors=competitors)
    except Exception as e:
        logger.error(f"Competitors error: {e}")
        return render_template('competitors.html', competitors=[], error=str(e))
    finally:
        conn.close()


# ============================================================
# API ENDPOINTS (for AJAX/JS)
# ============================================================
@app.route('/api/contacts/search')
def api_contacts_search():
    """Quick search contacts (for autocomplete)."""
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify([])
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT TOP 10 CONTACT_ID, FIRST_NAME + ' ' + LAST_NAME AS NAME, COMPANY, PHONE
            FROM CONTACTS
            WHERE FIRST_NAME LIKE ? OR LAST_NAME LIKE ? OR COMPANY LIKE ?
            ORDER BY FIRST_NAME
        """, (f'%{q}%', f'%{q}%', f'%{q}%'))
        return jsonify(rows_to_list(cur, cur.fetchall()))
    finally:
        conn.close()


@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    """Get dashboard stats as JSON (for auto-refresh)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM CONTACTS")
        total_contacts = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM DEALS WHERE STAGE NOT IN ('Won', 'Lost')")
        active_deals = cur.fetchone()[0]
        cur.execute("SELECT ISNULL(SUM(AMOUNT), 0) FROM DEALS WHERE STAGE NOT IN ('Won', 'Lost')")
        pipeline_value = float(cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM TASKS WHERE STATUS != 'Completed'")
        open_tasks = cur.fetchone()[0]
        return jsonify({
            'total_contacts': total_contacts,
            'active_deals': active_deals,
            'pipeline_value': pipeline_value,
            'open_tasks': open_tasks
        })
    finally:
        conn.close()


# ============================================================
# RUN
# ============================================================
if __name__ == '__main__':
    logger.info("Starting Tiger Marketing CRM on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
