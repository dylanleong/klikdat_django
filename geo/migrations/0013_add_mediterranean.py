from django.db import migrations

def add_mediterranean(apps, schema_editor):
    GeoKlikRegion = apps.get_model('geo', 'GeoKlikRegion')
    GeoKlikEpoch = apps.get_model('geo', 'GeoKlikEpoch')
    
    epoch, _ = GeoKlikEpoch.objects.get_or_create(name="2025.1")
    
    # Mediterranean Sea
    # Approx: 30N to 47N, 6W to 37E
    
    med = {
        "iso_a2": "OO",
        "adm1_code": "ME", 
        "name": "Mediterranean Sea",
        "min_lat": 30, "max_lat": 47, 
        "min_lon": -6, "max_lon": 37,
        "is_giant": False # Small enough for standard resolution? 
        # Area is ~2.5M km2. 
        # Standard 32-bit region (16x16) covers 65536 * 50m = 3276 km side.
        # Med width ~3800km. Might exceed standard 32-bit grid if mapped linearly to one region?
        # 37 - (-6) = 43 degrees longitude. At 35 deg lat, 1 deg ~= 91km. 43 * 91 = 3913 km.
        # Max standard grid: 65535 * 0.00045 degrees (50m) ~= 29 degrees?
        # 360 deg / 65536 ~= 0.005 deg per unit? No.
        # Utils uses normalize_to_int.
        # If is_giant=False, we have 65535 steps. 
        # Range is 43 degrees lon.
        # 43 degrees / 65535 = 0.00065 deg/step.
        # 0.00065 deg * 111km/deg ~= 72 meters.
        # So resolution would be ~72m, not 50m.
        # If we want 50m, we need more bits or splitting.
        # Giant region (35 bits) gives 131071 x (17 bits) -> double precision.
        # Wait, Giant is 6 chars + 2 nums.
        # Let's align with user request. "ocean identifier... 50m x 50m... 3rd and 4th section AAAA-AAAA".
        # AAAA-AAAA is 8 chars.
        # My Giant implementation was AAAN-AAAN (6 alpha 2 num).
        # Standard was AANN-AANN (4 alpha 2 num).
        # User requested explicitly "3rd and 4th section should be AAAA-AAAA". (8 Alpha).
        # 8 Alpha Base26 = 26^8 ~= 208 billion.
        # 4 chars Base26 = 26^4 = 456,976.
        # My implementation in utils.py used `_to_base26(val, length=4)` for both Lat and Lon codes.
        # So `lat_code` (4 chars) + `lon_code` (4 chars) = `AAAA-AAAA`.
        # Max val 456976.
        # Length 43 degrees.
        # 43 degrees / 456976 = 0.000094 degrees.
        # 0.000094 * 111km ~= 10 meters!
        # So 4 chars Base26 is PLENTY for 50m resolution over 43 degrees.
        # We don't need "Giant" logic (interleaving bits) for this specific format.
        # The Ocean implementation I wrote uses `_to_base26` separately for lat/lon (grid style), 
        # NOT Morton/Interleave.
        # So `is_giant` flag is effectively ignored by the `if gk_region.iso_a2 == 'OO'` block in utils.py 
        # (which uses the direct Base26 conversion).
        # So is_giant=True/False doesn't matter for logic, but let's set False.
    }
    
    if not GeoKlikRegion.objects.filter(epoch=epoch, iso_a2='OO', adm1_code='ME').exists():
         GeoKlikRegion.objects.create(
            epoch=epoch,
            iso_a2=med['iso_a2'],
            adm1_code=med['adm1_code'],
            min_lat=med['min_lat'],
            max_lat=med['max_lat'],
            min_lon=med['min_lon'],
            max_lon=med['max_lon'],
            is_giant=False
        )

def remove_mediterranean(apps, schema_editor):
    GeoKlikRegion = apps.get_model('geo', 'GeoKlikRegion')
    GeoKlikRegion.objects.filter(iso_a2='OO', adm1_code='ME').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0012_add_ocean_regions'), 
    ]

    operations = [
        migrations.RunPython(add_mediterranean, remove_mediterranean),
    ]
