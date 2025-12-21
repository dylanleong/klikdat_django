import json
import csv
import os

def extract_samples(geojson_path, output_csv, limit=10):
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])[:limit]
    if not features:
        return

    # Extract all property keys found in these 10 features
    fieldnames = set()
    for feature in features:
        fieldnames.update(feature.get('properties', {}).keys())
    
    fieldnames = sorted(list(fieldnames))

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for feature in features:
            writer.writerow(feature.get('properties', {}))

base_path = '/home/dylanleong/dev/klikdat_django/data/geo'
output_dir = '/home/dylanleong/.gemini/antigravity/brain/f5cdd91c-dc94-4a28-8bc0-25bdc9b2047f'

files = {
    'wb_admin0.geojson': 'wb_admin0_samples.csv',
    'wb_admin1.geojson': 'wb_admin1_samples.csv',
    'wb_admin2.geojson': 'wb_admin2_samples.csv'
}

for src, dest in files.items():
    extract_samples(os.path.join(base_path, src), os.path.join(output_dir, dest))
    print(f"Extracted samples from {src} to {dest}")
