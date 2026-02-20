"""
Auburn University Area Business Puller
Uses OpenStreetMap Overpass API (FREE, no API key needed)
Pulls all businesses within a configurable radius of Auburn University
"""

import requests
import csv
import json
import logging
import os
import sys
from datetime import datetime
from collections import defaultdict

# --- Config ---
AUBURN_LAT = 32.6010
AUBURN_LON = -85.4876
DEFAULT_RADIUS_METERS = 3000  # ~1.86 miles from campus center
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'auburn_businesses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Category Mapping ---
CATEGORY_MAP = {
    'restaurant': 'Restaurant',
    'fast_food': 'Fast Food',
    'cafe': 'Cafe/Coffee',
    'bar': 'Bar/Pub',
    'pub': 'Bar/Pub',
    'ice_cream': 'Ice Cream/Dessert',
    'bakery': 'Bakery',
    'food_court': 'Food Court',
    'supermarket': 'Grocery/Supermarket',
    'convenience': 'Convenience Store',
    'clothes': 'Clothing Store',
    'shoes': 'Shoe Store',
    'beauty': 'Beauty/Salon',
    'hairdresser': 'Hair Salon/Barber',
    'barber': 'Hair Salon/Barber',
    'car_repair': 'Auto Repair',
    'car_wash': 'Car Wash',
    'car': 'Car Dealership',
    'fuel': 'Gas Station',
    'bank': 'Bank',
    'atm': 'ATM',
    'pharmacy': 'Pharmacy',
    'hospital': 'Hospital/Medical',
    'clinic': 'Hospital/Medical',
    'doctors': 'Hospital/Medical',
    'dentist': 'Dentist',
    'veterinary': 'Veterinary',
    'gym': 'Gym/Fitness',
    'fitness_centre': 'Gym/Fitness',
    'hotel': 'Hotel/Lodging',
    'motel': 'Hotel/Lodging',
    'guest_house': 'Hotel/Lodging',
    'hostel': 'Hotel/Lodging',
    'laundry': 'Laundry',
    'dry_cleaning': 'Dry Cleaning',
    'mobile_phone': 'Phone/Electronics',
    'electronics': 'Phone/Electronics',
    'computer': 'Computer Store',
    'books': 'Bookstore',
    'stationery': 'Office/Stationery',
    'optician': 'Optician',
    'tattoo': 'Tattoo Parlor',
    'florist': 'Florist',
    'pet': 'Pet Store',
    'hardware': 'Hardware Store',
    'furniture': 'Furniture Store',
    'alcohol': 'Liquor Store',
    'tobacco': 'Tobacco/Vape',
    'copyshop': 'Print/Copy Shop',
    'storage_rental': 'Storage',
    'place_of_worship': 'Church/Worship',
    'school': 'School',
    'college': 'College',
    'university': 'University',
    'library': 'Library',
    'cinema': 'Movie Theater',
    'nightclub': 'Nightclub',
    'arts_centre': 'Arts Center',
    'museum': 'Museum',
    'parking': 'Parking',
    'bicycle_rental': 'Bike Rental',
}


def classify_business(tags):
    """Determine category from OSM tags"""
    for key in ['amenity', 'shop', 'tourism', 'leisure', 'office']:
        val = tags.get(key, '')
        if val in CATEGORY_MAP:
            return CATEGORY_MAP[val]
        if val:
            return val.replace('_', ' ').title()

    if tags.get('building') == 'commercial':
        return 'Commercial'
    if tags.get('building') == 'retail':
        return 'Retail'
    if tags.get('office'):
        return f"Office ({tags['office'].replace('_', ' ').title()})"

    return 'Other'


def build_query(lat, lon, radius):
    """Build Overpass QL query for businesses around a point"""
    return f"""
[out:json][timeout:60];
(
  node["name"]["amenity"](around:{radius},{lat},{lon});
  way["name"]["amenity"](around:{radius},{lat},{lon});
  node["name"]["shop"](around:{radius},{lat},{lon});
  way["name"]["shop"](around:{radius},{lat},{lon});
  node["name"]["tourism"](around:{radius},{lat},{lon});
  way["name"]["tourism"](around:{radius},{lat},{lon});
  node["name"]["leisure"](around:{radius},{lat},{lon});
  way["name"]["leisure"](around:{radius},{lat},{lon});
  node["name"]["office"](around:{radius},{lat},{lon});
  way["name"]["office"](around:{radius},{lat},{lon});
);
out center;
"""


def pull_businesses(lat=AUBURN_LAT, lon=AUBURN_LON, radius=DEFAULT_RADIUS_METERS):
    """Pull all businesses from OpenStreetMap around given coordinates"""
    query = build_query(lat, lon, radius)
    logger.info(f"Querying Overpass API: {radius}m radius around ({lat}, {lon})")

    try:
        resp = requests.post(OVERPASS_URL, data={'data': query}, timeout=90)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error(f"Overpass API error: {e}")
        return []

    elements = data.get('elements', [])
    logger.info(f"Raw results: {len(elements)} elements")

    businesses = []
    seen_names = set()

    for el in elements:
        tags = el.get('tags', {})
        name = tags.get('name', '').strip()
        if not name:
            continue

        # De-duplicate by name + type
        biz_lat = el.get('lat') or el.get('center', {}).get('lat', '')
        biz_lon = el.get('lon') or el.get('center', {}).get('lon', '')
        category = classify_business(tags)

        dedup_key = f"{name.lower()}|{category.lower()}"
        if dedup_key in seen_names:
            continue
        seen_names.add(dedup_key)

        biz = {
            'name': name,
            'category': category,
            'address': tags.get('addr:street', ''),
            'house_number': tags.get('addr:housenumber', ''),
            'city': tags.get('addr:city', 'Auburn'),
            'state': tags.get('addr:state', 'AL'),
            'zip': tags.get('addr:postcode', ''),
            'phone': tags.get('phone', tags.get('contact:phone', '')),
            'website': tags.get('website', tags.get('contact:website', '')),
            'cuisine': tags.get('cuisine', ''),
            'hours': tags.get('opening_hours', ''),
            'lat': biz_lat,
            'lon': biz_lon,
        }

        # Build full address
        if biz['house_number'] and biz['address']:
            biz['full_address'] = f"{biz['house_number']} {biz['address']}"
        elif biz['address']:
            biz['full_address'] = biz['address']
        else:
            biz['full_address'] = ''

        businesses.append(biz)

    # Sort by category then name
    businesses.sort(key=lambda x: (x['category'], x['name']))
    logger.info(f"Unique businesses found: {len(businesses)}")
    return businesses


def save_csv(businesses, filename=None):
    """Save businesses to CSV"""
    if not filename:
        out_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(out_dir, f'auburn_businesses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

    fields = ['name', 'category', 'full_address', 'city', 'state', 'zip',
              'phone', 'website', 'cuisine', 'hours', 'lat', 'lon']

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(businesses)

    logger.info(f"CSV saved: {filename}")
    return filename


def save_json(businesses, filename=None):
    """Save businesses to JSON"""
    if not filename:
        out_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(out_dir, f'auburn_businesses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(businesses, f, indent=2, ensure_ascii=False)

    logger.info(f"JSON saved: {filename}")
    return filename


def print_summary(businesses):
    """Print category summary"""
    cats = defaultdict(int)
    for b in businesses:
        cats[b['category']] += 1

    print(f"\n{'='*60}")
    print(f"  AUBURN UNIVERSITY AREA BUSINESSES")
    print(f"  Total: {len(businesses)} unique businesses")
    print(f"{'='*60}")

    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat:<30} {count:>4}")

    print(f"{'='*60}\n")

    # Print top 20 sample
    print("SAMPLE (first 20):")
    print(f"{'Name':<35} {'Category':<20} {'Address':<30}")
    print("-" * 85)
    for b in businesses[:20]:
        print(f"{b['name'][:34]:<35} {b['category'][:19]:<20} {b['full_address'][:29]:<30}")

    if len(businesses) > 20:
        print(f"  ... and {len(businesses) - 20} more (see CSV/JSON)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Pull businesses around Auburn University')
    parser.add_argument('--radius', type=int, default=DEFAULT_RADIUS_METERS,
                        help=f'Search radius in meters (default: {DEFAULT_RADIUS_METERS})')
    parser.add_argument('--csv', action='store_true', default=True, help='Save CSV (default: yes)')
    parser.add_argument('--json', action='store_true', help='Also save JSON')
    parser.add_argument('--email', action='store_true', help='Email results to boss')
    parser.add_argument('--no-csv', action='store_true', help='Skip CSV output')
    args = parser.parse_args()

    logger.info(f"Starting Auburn business pull - radius: {args.radius}m")

    businesses = pull_businesses(radius=args.radius)

    if not businesses:
        logger.warning("No businesses found!")
        print("No businesses found. Try increasing --radius")
        return

    print_summary(businesses)

    csv_file = None
    json_file = None

    if args.csv and not args.no_csv:
        csv_file = save_csv(businesses)

    if args.json:
        json_file = save_json(businesses)

    if args.email:
        email_results(businesses, csv_file)

    return businesses


def email_results(businesses, csv_file=None):
    """Email business list to boss"""
    cats = defaultdict(list)
    for b in businesses:
        cats[b['category']].append(b)

    body_lines = [
        f"Auburn University Area Businesses",
        f"Total: {len(businesses)} unique businesses found",
        f"Radius: {DEFAULT_RADIUS_METERS}m from campus center",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}",
        "",
        "=" * 50,
    ]

    for cat in sorted(cats.keys()):
        biz_list = cats[cat]
        body_lines.append(f"\n--- {cat} ({len(biz_list)}) ---")
        for b in sorted(biz_list, key=lambda x: x['name']):
            line = f"  {b['name']}"
            if b['full_address']:
                line += f" | {b['full_address']}"
            if b['phone']:
                line += f" | {b['phone']}"
            if b['cuisine']:
                line += f" | Cuisine: {b['cuisine']}"
            body_lines.append(line)

    body = "\n".join(body_lines)

    # Use gmail_send.py
    gmail_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gmail', 'gmail_send.py')
    import subprocess
    cmd = [
        sys.executable, gmail_script,
        '--to', 'jckpc@yahoo.com',
        '--subject', f'Auburn University Area Businesses ({len(businesses)} found)',
        '--body', body
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        logger.info("Email sent successfully")
    else:
        logger.error(f"Email failed: {result.stderr}")


if __name__ == '__main__':
    main()
