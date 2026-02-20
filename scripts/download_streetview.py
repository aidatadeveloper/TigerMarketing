"""
Google Street View Image Downloader for Auburn Businesses
Downloads Street View images for each business using lat/lon coordinates.
Uses Google Maps Street View Static API.
"""

import json
import os
import sys
import time
import logging
import requests
import re
import pyodbc
from datetime import datetime

# --- Config ---
API_KEY = "AIzaSyBtUAnT5vQLaH1TLA7POPD0toSV_FJriJo"
STREETVIEW_URL = "https://maps.googleapis.com/maps/api/streetview"
IMAGE_SIZE = "600x400"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images', 'streetview')
DELAY_BETWEEN_REQUESTS = 0.2  # seconds between API calls (be nice to API)

# --- Logging ---
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'streetview_download_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def sanitize_filename(name):
    """Make business name safe for filename"""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    name = name[:80]  # max length
    return name


def check_api_key():
    """Test if API key works with Street View"""
    test_url = f"{STREETVIEW_URL}/metadata"
    params = {
        'location': '32.6010,-85.4876',  # Auburn University
        'key': API_KEY
    }
    try:
        resp = requests.get(test_url, params=params, timeout=10)
        data = resp.json()
        logger.info(f"API key test response: {data}")
        if data.get('status') == 'REQUEST_DENIED':
            logger.error(f"API key denied: {data.get('error_message', 'Unknown error')}")
            return False
        return True
    except Exception as e:
        logger.error(f"API key test failed: {e}")
        return False


def download_streetview(name, lat, lon, category, output_dir):
    """Download Street View image for a single business"""
    if not lat or not lon:
        logger.warning(f"  SKIP (no coordinates): {name}")
        return False

    safe_name = sanitize_filename(name)
    safe_cat = sanitize_filename(category)

    # Create category subfolder
    cat_dir = os.path.join(output_dir, safe_cat)
    os.makedirs(cat_dir, exist_ok=True)

    filename = f"{safe_name}.jpg"
    filepath = os.path.join(cat_dir, filename)

    # Skip if already downloaded
    if os.path.exists(filepath) and os.path.getsize(filepath) > 5000:
        logger.info(f"  SKIP (exists): {name}")
        return True

    params = {
        'size': IMAGE_SIZE,
        'location': f'{lat},{lon}',
        'key': API_KEY,
        'fov': 90,       # field of view
        'heading': 0,     # facing direction (0 = north)
        'pitch': 10,      # slight upward angle
        'source': 'outdoor'
    }

    try:
        # First check metadata to see if image exists
        meta_resp = requests.get(f"{STREETVIEW_URL}/metadata", params={
            'location': f'{lat},{lon}',
            'key': API_KEY
        }, timeout=10)
        meta = meta_resp.json()

        if meta.get('status') != 'OK':
            logger.warning(f"  NO IMAGE: {name} (status: {meta.get('status')})")
            return False

        # Download actual image
        resp = requests.get(STREETVIEW_URL, params=params, timeout=15)

        if resp.status_code == 200 and len(resp.content) > 5000:
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            logger.info(f"  OK: {name} -> {filepath} ({len(resp.content):,} bytes)")
            return True
        else:
            logger.warning(f"  FAIL: {name} (status={resp.status_code}, size={len(resp.content)})")
            return False

    except requests.Timeout:
        logger.warning(f"  TIMEOUT: {name}")
        return False
    except Exception as e:
        logger.error(f"  ERROR: {name} -> {e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Download Street View images for Auburn businesses')
    parser.add_argument('--json', type=str, help='Path to business JSON file')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of downloads (0=all)')
    parser.add_argument('--test', action='store_true', help='Test API key only')
    args = parser.parse_args()

    # Find JSON file
    if args.json:
        json_file = args.json
    else:
        # Find JSON in data/ folder
        biz_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
        json_files = [f for f in os.listdir(biz_dir) if f.endswith('.json')]
        if not json_files:
            logger.error("No JSON file found. Run pull_businesses.py first.")
            sys.exit(1)
        json_file = os.path.join(biz_dir, sorted(json_files)[-1])

    logger.info(f"Loading businesses from: {json_file}")

    # Test API key first
    if not check_api_key():
        print("\nAPI KEY ERROR: Street View Static API may not be enabled.")
        print("To fix:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Enable 'Street View Static API'")
        print("  3. Make sure billing is enabled")
        print("  4. Update API_KEY in this script if needed")
        if args.test:
            sys.exit(1)
        # Continue anyway - some keys return metadata errors but still serve images

    if args.test:
        print("API key test passed!")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        businesses = json.load(f)

    logger.info(f"Loaded {len(businesses)} businesses")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    success = 0
    fail = 0
    skip = 0
    total = len(businesses) if args.limit == 0 else min(args.limit, len(businesses))

    print(f"\nDownloading Street View images for {total} businesses...")
    print(f"Output: {OUTPUT_DIR}\n")

    for i, biz in enumerate(businesses[:total]):
        name = biz['name']
        lat = biz.get('lat', '')
        lon = biz.get('lon', '')
        category = biz.get('category', 'Other')

        pct = (i + 1) / total * 100
        print(f"[{i+1}/{total}] ({pct:.0f}%) {name}...", end=' ', flush=True)

        result = download_streetview(name, lat, lon, category, OUTPUT_DIR)

        if result:
            success += 1
            print("OK")
        else:
            fail += 1
            print("SKIP/FAIL")

        time.sleep(DELAY_BETWEEN_REQUESTS)

    print(f"\n{'='*50}")
    print(f"  DOWNLOAD COMPLETE")
    print(f"  Success: {success}")
    print(f"  Failed/No Image: {fail}")
    print(f"  Total: {total}")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*50}")

    logger.info(f"Complete. Success={success}, Fail={fail}, Total={total}")

    # Update database with image paths
    update_db_image_paths()


def update_db_image_paths():
    """Walk the images folder and update BUSINESSES.IMAGE_PATH for each match"""
    DB_CONN_STR = 'DRIVER={SQL Server};SERVER=localhost;DATABASE=TIGER_MARKETING;Trusted_Connection=yes;'
    conn = pyodbc.connect(DB_CONN_STR, timeout=30)
    cursor = conn.cursor()

    updated = 0
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for f in files:
            if not f.endswith('.jpg'):
                continue
            filepath = os.path.join(root, f)
            rel_path = os.path.relpath(filepath, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

            # Match by sanitized name
            biz_name = f.replace('.jpg', '').replace('_', ' ')
            cursor.execute("UPDATE BUSINESSES SET IMAGE_PATH = ?, UPDATED_DATE = GETDATE() WHERE IMAGE_PATH IS NULL AND REPLACE(REPLACE(NAME, ' ', '_'), '''', '') LIKE ?",
                           rel_path, f'%{biz_name[:20]}%')
            if cursor.rowcount > 0:
                updated += 1

    conn.commit()
    conn.close()
    logger.info(f"Updated {updated} business image paths in DB")
    print(f"Updated {updated} image paths in database")


if __name__ == '__main__':
    main()
