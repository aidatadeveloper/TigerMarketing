"""
Enrich Auburn businesses with Google Places data (ratings, reviews, photos, place_id)
Requires Google Places API (New) to be enabled in Google Cloud Console.

Enable at: https://console.developers.google.com/apis/api/places.googleapis.com/overview?project=201143722121
Also enable: https://console.developers.google.com/apis/api/streetview.googleapis.com/overview?project=201143722121
"""
import os
import sys
import time
import json
import logging
import requests
import pyodbc
from datetime import datetime

# --- Config ---
API_KEY = "AIzaSyBtUAnT5vQLaH1TLA7POPD0toSV_FJriJo"
PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
PHOTO_URL = "https://places.googleapis.com/v1/{name}/media"
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images', 'google_places')
DB_CONN_STR = 'DRIVER={SQL Server};SERVER=localhost;DATABASE=TIGER_MARKETING;Trusted_Connection=yes;'
DELAY = 0.3  # seconds between requests

# --- Logging ---
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'enrich_businesses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def search_place(name, lat, lon):
    """Search for a business on Google Places API (New)"""
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.rating,places.userRatingCount,places.photos,places.googleMapsUri,places.formattedAddress'
    }
    body = {
        'textQuery': f'{name} Auburn AL',
        'locationBias': {
            'circle': {
                'center': {'latitude': float(lat), 'longitude': float(lon)},
                'radius': 500.0
            }
        },
        'maxResultCount': 1
    }
    try:
        resp = requests.post(PLACES_URL, headers=headers, json=body, timeout=10)
        if resp.status_code == 200:
            places = resp.json().get('places', [])
            return places[0] if places else None
        else:
            logger.warning(f"Places search failed for {name}: {resp.status_code} {resp.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"Places search error for {name}: {e}")
        return None


def download_photo(photo_name, output_path):
    """Download a place photo"""
    url = f"https://places.googleapis.com/v1/{photo_name}/media"
    params = {
        'maxHeightPx': 600,
        'maxWidthPx': 800,
        'key': API_KEY
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 5000:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(resp.content)
            return True
    except Exception as e:
        logger.error(f"Photo download error: {e}")
    return False


def enrich_all(limit=0):
    """Enrich all businesses in DB with Google Places data"""
    conn = pyodbc.connect(DB_CONN_STR, timeout=30)
    cursor = conn.cursor()

    # Get businesses without Google Place ID
    cursor.execute("""
        SELECT ID, NAME, LATITUDE, LONGITUDE, CATEGORY
        FROM BUSINESSES
        WHERE GOOGLE_PLACE_ID IS NULL AND LATITUDE IS NOT NULL
        ORDER BY NAME
    """)
    businesses = cursor.fetchall()

    if limit > 0:
        businesses = businesses[:limit]

    total = len(businesses)
    logger.info(f"Enriching {total} businesses")
    enriched = 0
    photos_downloaded = 0

    os.makedirs(IMAGE_DIR, exist_ok=True)

    for i, (biz_id, name, lat, lon, category) in enumerate(businesses):
        pct = (i + 1) / total * 100
        print(f"[{i+1}/{total}] ({pct:.0f}%) {name}...", end=' ', flush=True)

        place = search_place(name, lat, lon)
        if not place:
            print("NOT FOUND")
            time.sleep(DELAY)
            continue

        # Update DB
        place_id = place.get('id', '')
        rating = place.get('rating')
        review_count = place.get('userRatingCount')

        cursor.execute("""
            UPDATE BUSINESSES
            SET GOOGLE_PLACE_ID = ?, RATING = ?, REVIEW_COUNT = ?, UPDATED_DATE = GETDATE()
            WHERE ID = ?
        """, place_id, rating, review_count, biz_id)
        enriched += 1

        # Download first photo if available
        photos = place.get('photos', [])
        if photos:
            import re
            safe_name = re.sub(r'[<>:"/\\|?*]', '', name)
            safe_name = re.sub(r'\s+', '_', safe_name.strip())[:80]
            safe_cat = re.sub(r'[<>:"/\\|?*]', '', category or 'Other')
            safe_cat = re.sub(r'\s+', '_', safe_cat.strip())

            photo_path = os.path.join(IMAGE_DIR, safe_cat, f'{safe_name}.jpg')
            photo_name = photos[0].get('name', '')

            if photo_name and download_photo(photo_name, photo_path):
                rel_path = os.path.relpath(photo_path, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
                cursor.execute("UPDATE BUSINESSES SET IMAGE_PATH = ? WHERE ID = ?", rel_path, biz_id)
                photos_downloaded += 1
                print(f"OK (rating={rating}, photos={len(photos)})")
            else:
                print(f"OK (rating={rating}, no photo)")
        else:
            print(f"OK (rating={rating})")

        conn.commit()
        time.sleep(DELAY)

    conn.close()
    print(f"\n{'='*50}")
    print(f"  ENRICHMENT COMPLETE")
    print(f"  Enriched: {enriched}/{total}")
    print(f"  Photos: {photos_downloaded}")
    print(f"{'='*50}")
    logger.info(f"Done. Enriched={enriched}, Photos={photos_downloaded}")


def test_api():
    """Test if Places API is enabled"""
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.displayName'
    }
    body = {
        'textQuery': 'Toomer Corner Auburn AL',
        'maxResultCount': 1
    }
    resp = requests.post(PLACES_URL, headers=headers, json=body, timeout=10)
    if resp.status_code == 200:
        places = resp.json().get('places', [])
        if places:
            print(f"API WORKING! Found: {places[0].get('displayName', {}).get('text', 'Unknown')}")
            return True
    print(f"API NOT READY: {resp.status_code} - {resp.text[:300]}")
    return False


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Enrich businesses with Google Places data')
    parser.add_argument('--limit', type=int, default=0, help='Limit enrichment count (0=all)')
    parser.add_argument('--test', action='store_true', help='Test API connectivity')
    args = parser.parse_args()

    if args.test:
        test_api()
    else:
        enrich_all(limit=args.limit)
