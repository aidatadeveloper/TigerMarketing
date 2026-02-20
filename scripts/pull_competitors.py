"""
Pull window washing and power washing competitors around Auburn, AL
Uses Google Places API (New) to search and store in TIGER_MARKETING.COMPETITORS
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
DB_CONN_STR = 'DRIVER={SQL Server};SERVER=localhost;DATABASE=TIGER_MARKETING;Trusted_Connection=yes;'
AUBURN_LAT = 32.6010
AUBURN_LON = -85.4876
SEARCH_RADIUS = 50000  # 50km (~31 miles) to cover Auburn/Opelika/surrounding areas
DELAY = 0.5

# Search terms for competitors
SEARCH_TERMS = [
    "window washing Auburn Alabama",
    "window cleaning Auburn Alabama",
    "power washing Auburn Alabama",
    "pressure washing Auburn Alabama",
    "window washing Opelika Alabama",
    "window cleaning Opelika Alabama",
    "power washing Opelika Alabama",
    "pressure washing Opelika Alabama",
    "exterior cleaning Auburn Alabama",
    "house washing Auburn Alabama",
    "commercial window cleaning Auburn AL",
    "window washing Lee County Alabama",
    "pressure washing Lee County Alabama",
    "power washing Columbus Georgia",
    "window cleaning Columbus Georgia",
]

# --- Logging ---
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'pull_competitors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def search_places(query, max_results=20):
    """Search Google Places API for businesses matching query"""
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri,places.location,places.types'
    }
    body = {
        'textQuery': query,
        'locationBias': {
            'circle': {
                'center': {'latitude': AUBURN_LAT, 'longitude': AUBURN_LON},
                'radius': float(SEARCH_RADIUS)
            }
        },
        'maxResultCount': max_results
    }

    try:
        resp = requests.post(PLACES_URL, headers=headers, json=body, timeout=15)
        if resp.status_code == 200:
            places = resp.json().get('places', [])
            logger.info(f"  '{query}' -> {len(places)} results")
            return places
        else:
            logger.warning(f"  API error for '{query}': {resp.status_code} {resp.text[:200]}")
            return []
    except Exception as e:
        logger.error(f"  Request error for '{query}': {e}")
        return []


def categorize(query):
    """Determine category from search term"""
    q = query.lower()
    if 'window' in q:
        return 'Window Washing/Cleaning'
    elif 'power' in q or 'pressure' in q:
        return 'Power/Pressure Washing'
    elif 'house wash' in q:
        return 'House Washing'
    elif 'exterior' in q:
        return 'Exterior Cleaning'
    return 'Cleaning Services'


def parse_city_state(address):
    """Extract city and state from formatted address"""
    parts = address.split(',')
    city = ''
    state = ''
    if len(parts) >= 2:
        city = parts[-3].strip() if len(parts) >= 3 else parts[-2].strip()
        state_zip = parts[-2].strip() if len(parts) >= 3 else parts[-1].strip()
        state = state_zip.split()[0] if state_zip else ''
    return city, state


def pull_competitors():
    """Pull all competitors and store in DB"""
    conn = pyodbc.connect(DB_CONN_STR, timeout=30)
    cursor = conn.cursor()

    all_places = {}  # keyed by place_id to dedupe

    for query in SEARCH_TERMS:
        logger.info(f"Searching: {query}")
        places = search_places(query)
        category = categorize(query)

        for place in places:
            pid = place.get('id', '')
            if pid in all_places:
                # Add additional search term
                all_places[pid]['search_terms'].add(query)
                continue

            name = place.get('displayName', {}).get('text', '')
            address = place.get('formattedAddress', '')
            city, state = parse_city_state(address)
            loc = place.get('location', {})

            all_places[pid] = {
                'name': name,
                'category': category,
                'address': address,
                'city': city,
                'state': state,
                'phone': place.get('nationalPhoneNumber', ''),
                'website': place.get('websiteUri', ''),
                'google_place_id': pid,
                'google_maps_url': place.get('googleMapsUri', ''),
                'rating': place.get('rating'),
                'review_count': place.get('userRatingCount'),
                'lat': loc.get('latitude'),
                'lon': loc.get('longitude'),
                'search_terms': {query},
            }

        time.sleep(DELAY)

    # Insert into DB
    inserted = 0
    for pid, biz in all_places.items():
        search_str = ' | '.join(sorted(biz['search_terms']))
        try:
            cursor.execute("""
                INSERT INTO COMPETITORS (NAME, CATEGORY, ADDRESS, CITY, STATE, PHONE, WEBSITE,
                    GOOGLE_PLACE_ID, GOOGLE_MAPS_URL, RATING, REVIEW_COUNT, LATITUDE, LONGITUDE, SEARCH_TERM)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, biz['name'], biz['category'], biz['address'], biz['city'], biz['state'],
                biz['phone'], biz['website'], biz['google_place_id'], biz['google_maps_url'],
                biz['rating'], biz['review_count'], biz['lat'], biz['lon'], search_str)
            inserted += 1
        except Exception as e:
            logger.error(f"Insert error for {biz['name']}: {e}")

    conn.commit()
    conn.close()

    # Print summary
    print(f"\n{'='*60}")
    print(f"  COMPETITOR PULL COMPLETE")
    print(f"  Total unique competitors: {len(all_places)}")
    print(f"  Inserted to DB: {inserted}")
    print(f"{'='*60}")

    # Print list
    for pid, biz in sorted(all_places.items(), key=lambda x: (x[1]['category'], x[1]['name'])):
        rating_str = f"  {biz['rating']}/5 ({biz['review_count']} reviews)" if biz['rating'] else ""
        print(f"  [{biz['category']}] {biz['name']}")
        print(f"    {biz['address']}{rating_str}")
        if biz['phone']:
            print(f"    Phone: {biz['phone']}")
        if biz['website']:
            print(f"    Web: {biz['website']}")
        print()

    logger.info(f"Done. {inserted} competitors stored in COMPETITORS table.")
    return all_places


if __name__ == '__main__':
    logger.info("Starting competitor pull for Auburn, AL area")
    pull_competitors()
