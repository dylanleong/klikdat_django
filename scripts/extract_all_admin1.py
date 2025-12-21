import json
import csv
import os

def extract_all_properties(geojson_path, output_csv):
    """Extracts all properties from a GeoJSON file and saves to CSV."""
    if not os.path.exists(geojson_path):
        print(f"Error: {geojson_path} does not exist.")
        return

    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    if not features:
        print("No features found.")
        return

    # Extract all properties from every feature
    results = []
    all_keys = set()
    
    for feature in features:
        props = feature.get('properties', {})
        if not props:
            continue
            
        # Skip metadata features (like CRS definitions)
        if props.get('name') and ('CRS' in props.get('name') or 'crs' in props.get('name')):
            continue
            
        results.append(props)
        all_keys.update(props.keys())

    if not results:
        print("No valid properties found.")
        return

    fieldnames = sorted(list(all_keys))

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in results:
            writer.writerow(record)

    print(f"Extracted {len(results)} records to {output_csv}")

src_path = '/home/dylanleong/dev/klikdat_django/data/geo/wb_admin1.geojson'
dest_path = '/home/dylanleong/.gemini/antigravity/brain/f5cdd91c-dc94-4a28-8bc0-25bdc9b2047f/wb_admin1_full_metadata.csv'

extract_all_properties(src_path, dest_path)
