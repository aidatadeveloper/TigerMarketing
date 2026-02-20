"""
WSGI entry point for PythonAnywhere deployment.
This file is referenced in the PythonAnywhere Web tab configuration.
"""

import os
import sys

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Force SQLite mode for cloud deployment
os.environ['USE_SQLITE'] = '1'
os.environ['SECRET_KEY'] = 'tiger-marketing-crm-production-2026'

# Initialize database if needed
db_path = os.path.join(project_dir, 'tiger_crm.db')
if not os.path.exists(db_path):
    from init_db import create_tables
    create_tables()

from app import app as application
