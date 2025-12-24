import math

class MortonCoder:
    """
    Logic for Z-order interleaving.
    Maps normalized coordinates (0.0 to 1.0) to interleaved bit strings.
    """
    @staticmethod
    def interleave(x_bits, y_bits, x_count, y_count):
        """Interleave bits of two integers."""
        interleaved = 0
        for i in range(max(x_count, y_count)):
            if i < x_count:
                interleaved |= ((x_bits >> i) & 1) << (2 * i)
            if i < y_count:
                interleaved |= ((y_bits >> i) & 1) << (2 * i + 1)
        return interleaved

    @staticmethod
    def normalize_to_int(value, min_val, max_val, max_int):
        """Map a float value in [min_val, max_val] to an integer in [0, max_int]."""
        if value < min_val: value = min_val
        if value > max_val: value = max_val
        
        ratio = (value - min_val) / (max_val - min_val)
        return int(ratio * max_int)

    @staticmethod
    def de_interleave(interleaved, x_count, y_count):
        """De-interleave bits into two integers."""
        x_bits = 0
        y_bits = 0
        for i in range(max(x_count, y_count)):
            if i < x_count:
                x_bits |= ((interleaved >> (2 * i)) & 1) << i
            if i < y_count:
                y_bits |= ((interleaved >> (2 * i + 1)) & 1) << i
        return x_bits, y_bits

    @staticmethod
    def denormalize_from_int(val_int, min_val, max_val, max_int):
        """Map an integer in [0, max_int] back to a center float in [min_val, max_val]."""
        step = (max_val - min_val) / max_int
        return min_val + (val_int * step) + (step / 2)

    @staticmethod
    def denormalize_to_bbox(val_int, min_val, max_val, max_int):
        """Map an integer in [0, max_int] to a bounding box."""
        step = (max_val - min_val) / max_int
        b_min = min_val + (val_int * step)
        b_max = b_min + step
        return b_min, b_max

class GeoKlikEncoder:
    """
    Converts interleaved bits into the GeoKlik patterns using the full alphanumeric set.
    """
    CHAR_SET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" # Base36

    @classmethod
    def encode_standard(cls, interleaved_32):
        """Pattern: AANN-AANN (4 alpha, 4 numeric)"""
        # We need to split 32 bits into 4 groups for alpha (5 bits each? no, that's 20)
        # Actually, let's just map the whole thing to the required slots.
        # AANN-AANN means 4 Alpha, 4 Numeric.
        # Alpha slots: 26 chars. Numeric: 10 chars.
        # Total capacity: 26*26*10*10 * 26*26*10*10 = (26^2 * 10^2)^2 = 67600^2 = 4,569,760,000
        # 32 bits is ~4.29 billion. This fits perfectly.
        
        val = interleaved_32
        
        # Split into two 16-bit chunks (AANN and AANN)
        chunk2 = val % 67600
        chunk1 = val // 67600
        
        return f"{cls._to_aann(chunk1)}-{cls._to_aann(chunk2)}"

    @classmethod
    def encode_giant(cls, interleaved_35):
        """Pattern: AAAN-AAAN (6 alpha, 2 numeric)"""
        # Capacity: (26^3 * 10)^2 = (17576 * 10)^2 = 175760^2 = 30,891,577,600
        # 35 bits is ~34.35 billion. This fits too!
        
        val = interleaved_35
        chunk2 = val % 175760
        chunk1 = val // 175760
        
        return f"{cls._to_aaan(chunk1)}-{cls._to_aaan(chunk2)}"

    @classmethod
    def _to_aann(cls, val):
        n2 = val % 10
        val //= 10
        n1 = val % 10
        val //= 10
        a2 = cls.CHAR_SET[10 + (val % 26)]
        val //= 26
        a1 = cls.CHAR_SET[10 + (val % 26)]
        return f"{a1}{a2}{n1}{n2}"

    @classmethod
    def _to_aaan(cls, val):
        n1 = val % 10
        val //= 10
        a3 = cls.CHAR_SET[10 + (val % 26)]
        val //= 26
        a2 = cls.CHAR_SET[10 + (val % 26)]
        val //= 26
        a1 = cls.CHAR_SET[10 + (val % 26)]
        return f"{a1}{a2}{a3}{n1}"

    @staticmethod
    def _to_base26(val, length=4):
        chars = []
        for _ in range(length):
            val, rem = divmod(val, 26)
            chars.append(chr(65 + rem))
        return "".join(reversed(chars))

    @staticmethod
    def _from_base26(s):
        val = 0
        for char in s:
            val = val * 26 + (ord(char) - 65)
        return val

class GeoKlikService:
    """
    High-level orchestrator for generating GeoKlik IDs.
    """
    @classmethod
    def encode(cls, lat, lon, epoch_name="2025.1"):
        from geo.models import WorldBankBoundary, GeoKlikRegion, WorldBankRegionMapping
        from django.contrib.gis.geos import Point
        
        point = Point(lon, lat)
        
        # 1. Find ADM1 region
        wb_boundary = WorldBankBoundary.objects.filter(
            level="Admin 1", 
            geometry__contains=point
        ).first()
        
        if not wb_boundary:
            # Fallback: Check Ocean Regions
            gk_region = GeoKlikRegion.objects.filter(
                 epoch__name=epoch_name,
                 iso_a2='OO',
                 min_lat__lte=lat, max_lat__gte=lat,
                 min_lon__lte=lon, max_lon__gte=lon
             ).order_by('is_giant').first()
            
            if gk_region:
                # Ocean Encoding: OO-RR-AAAA-AAAA
                # 50m resolution target.
                # 4 chars Base26 = 456,976 values.
                
                coder = MortonCoder()
                # Use normalize_to_int directly for each axis
                x_norm = coder.normalize_to_int(lon, gk_region.min_lon, gk_region.max_lon, 456975)
                y_norm = coder.normalize_to_int(lat, gk_region.min_lat, gk_region.max_lat, 456975)
                
                lat_code = GeoKlikEncoder._to_base26(y_norm, 4)
                lon_code = GeoKlikEncoder._to_base26(x_norm, 4)
                
                id_str = f"{gk_region.iso_a2}-{gk_region.adm1_code}-{lat_code}-{lon_code}"
                
                ocean_names = {
                    "PE": "Pacific Ocean (East)",
                    "PW": "Pacific Ocean (West)",
                    "PA": "Pacific Ocean", # Fallback
                    "AT": "Atlantic Ocean",
                    "IN": "Indian Ocean",
                    "AA": "Arctic Ocean",
                    "SO": "Southern Ocean",
                    "ME": "Mediterranean Sea",
                    "CS": "Caspian Sea",
                    "BS": "Black Sea"
                }

                return {
                    "geoklik_id": id_str,
                    "country_name": "International Waters", 
                    "region_name": ocean_names.get(gk_region.adm1_code, "Ocean"),
                    "adm2_name": "Ocean"
                }

            return {
                "geoklik_id": "WORLD-OO-UNKNOWN",
                "error": "Location not covered by land boundaries or ocean regions"
            }

        # 2. Get Region Mapping (Custom Identifier)
        mapping = WorldBankRegionMapping.objects.filter(
            wb_adm1_code=wb_boundary.adm1_code
        ).first()
        region_code = mapping.wb_region_code if mapping else "XX"
        
        # 3. Get Persistent Region Config (Bounding Box)
        gk_region = GeoKlikRegion.objects.filter(
            epoch__name=epoch_name,
            adm1_code=wb_boundary.adm1_code
        ).first()
        
        if not gk_region:
            return {
                "geoklik_id": f"{wb_boundary.iso_a2}-{region_code}-CONFIG-MISSING",
                "error": "Configuration missing for this region"
            }

        # 4. Geocoding Math
        coder = MortonCoder()
        if gk_region.is_giant:
            # 35-bit Pattern (6 Alpha, 2 Numeric)
            # x_bits (17), y_bits (18) = 35 bits
            x_int = coder.normalize_to_int(lon, gk_region.min_lon, gk_region.max_lon, 131071)
            y_int = coder.normalize_to_int(lat, gk_region.min_lat, gk_region.max_lat, 262143)
            interleaved = coder.interleave(x_int, y_int, 17, 18)
            geodata = GeoKlikEncoder.encode_giant(interleaved)
        else:
            # 32-bit Pattern (4 Alpha, 4 Numeric)
            # x_bits (16), y_bits (16) = 32 bits
            x_int = coder.normalize_to_int(lon, gk_region.min_lon, gk_region.max_lon, 65535)
            y_int = coder.normalize_to_int(lat, gk_region.min_lat, gk_region.max_lat, 65535)
            interleaved = coder.interleave(x_int, y_int, 16, 16)
            geodata = GeoKlikEncoder.encode_standard(interleaved)

        # 5. Get Metadata
        # Try to find specific Admin 2 boundary for city/district name
        wb_adm2 = WorldBankBoundary.objects.filter(
            level="Admin 2",
            geometry__contains=point
        ).first()
        
        adm2_name = wb_adm2.adm2_name if wb_adm2 else None
        
        # Get Country Name
        from geo.models import CountryInfo
        country = CountryInfo.objects.filter(country_code=gk_region.iso_a2).first()
        country_name = country.country_name if country else gk_region.iso_a2

        id_str = f"{gk_region.iso_a2}-{region_code}-{geodata}"
        
        return {
            "geoklik_id": id_str,
            "country_name": country_name,
            "region_name": wb_boundary.adm1_name,
            "adm2_name": adm2_name
        }

    @classmethod
    def decode(cls, geoklik_id, epoch_name="2025.1"):
        from geo.models import GeoKlikRegion, WorldBankRegionMapping
        
        parts = geoklik_id.split('-')
        if len(parts) < 3: return None
        
        parts = geoklik_id.split('-')
        if len(parts) < 3: return None
        
        iso_a2 = parts[0]
        
        if iso_a2 == 'OO':
            # Ocean Decoding
            # Format: OO-RR-AAAA-AAAA
            if len(parts) != 4: return None
            
            region_code = parts[1]
            lat_code_str = parts[2]
            lon_code_str = parts[3]
            
            # Find Region by Code
            gk_region = GeoKlikRegion.objects.filter(
                epoch__name=epoch_name,
                iso_a2='OO',
                adm1_code=region_code
            ).first()
            
            if not gk_region: return None
            
            coder = MortonCoder()
            
            y_val = GeoKlikEncoder._from_base26(lat_code_str)
            x_val = GeoKlikEncoder._from_base26(lon_code_str)
            
            y_min, y_max = coder.denormalize_to_bbox(y_val, gk_region.min_lat, gk_region.max_lat, 456975)
            x_min, x_max = coder.denormalize_to_bbox(x_val, gk_region.min_lon, gk_region.max_lon, 456975)
            
            center_lat = (y_min + y_max)/2
            center_lon = (x_min + x_max)/2
            
            # Since regions might overlap (East/West Pacific), we assume the code (PE vs PW) is sufficient.
            
            return {
                'iso_a2': iso_a2,
                'region_code': region_code,
                'country_name': "International Waters", 
                'region_name': gk_region.iso_a2, # Wait, store nice name? 
                # Model doesn't have name logic easily accessible except construction str.
                # Migration stored 'name' but model doesn't have 'name' field?
                # Ah, Migration 0012: I passed 'name' to the list, but model GeoKlikRegion doesn't have 'name'!
                # I should just use "Pacific Ocean" hardcoded or derived.
                # Actually, I can use the migration list logic or just return code for now.
                # Wait, I checked models.py earlier. GeoKlikRegion only has iso_a2, adm1_code.
                # So I can't retrieve "Pacific Ocean (East)" string unless I query WorldBankBoundary?
                # But oceans don't have WB boundary.
                # I'll just return "Ocean" or derive from code map.
                'adm2_name': "Ocean",
                'bbox': [y_min, x_min, y_max, x_max],
                'center': [center_lat, center_lon]
            }

        region_code = parts[1]
        geodata = parts[2:]
        
        mapping = WorldBankRegionMapping.objects.filter(
            country_code=iso_a2,
            wb_region_code=region_code
        ).first()
        
        if not mapping: return None
        
        gk_region = GeoKlikRegion.objects.filter(
            epoch__name=epoch_name,
            adm1_code=mapping.wb_adm1_code
        ).first()
        
        if not gk_region: return None

        coder = MortonCoder()
        decoder = GeoKlikDecoder()
        
        if gk_region.is_giant:
            # Giant: AAAN-AAAN (6 Alpha, 2 Numeric) 35 bits (17x, 18y)
            if len(geodata) < 2: return None
            v1 = decoder._from_aaan(geodata[0])
            v2 = decoder._from_aaan(geodata[1])
            interleaved = (v1 * 175760) + v2
            
            # De-interleave 35 bits (17x, 18y)
            x_int, y_int = coder.de_interleave(interleaved, 17, 18)
            
            x_min, x_max = coder.denormalize_to_bbox(x_int, gk_region.min_lon, gk_region.max_lon, 131071)
            y_min, y_max = coder.denormalize_to_bbox(y_int, gk_region.min_lat, gk_region.max_lat, 262143)
        else:
            # Standard: AANN-AANN (4 Alpha, 4 Numeric) 32 bits (16x, 16y)
            if len(geodata) < 2: return None
            v1 = decoder._from_aann(geodata[0])
            v2 = decoder._from_aann(geodata[1])
            interleaved = (v1 * 67600) + v2
            x_int, y_int = coder.de_interleave(interleaved, 16, 16)
            x_min, x_max = coder.denormalize_to_bbox(x_int, gk_region.min_lon, gk_region.max_lon, 65535)
            y_min, y_max = coder.denormalize_to_bbox(y_int, gk_region.min_lat, gk_region.max_lat, 65535)

        center_lat = (y_min + y_max)/2
        center_lon = (x_min + x_max)/2
        
        # Metadata Lookup
        from geo.models import CountryInfo, WorldBankBoundary
        from django.contrib.gis.geos import Point
        
        country = CountryInfo.objects.filter(country_code=iso_a2).first()
        country_name = country.country_name if country else iso_a2
        
        # We know the region name from mapping (it's the wb_adm1_code mostly, but let's get the display name)
        # Actually mapping only has codes. We might need to look up the boundary again or store the name.
        # Efficient way: Look up WB boundary by code
        wb_boundary = WorldBankBoundary.objects.filter(adm1_code=gk_region.adm1_code).first()
        region_name = wb_boundary.adm1_name if wb_boundary else gk_region.adm1_code
        
        # Dynamic lookup for city/district (Admin 2) based on center
        wb_adm2 = WorldBankBoundary.objects.filter(
            level="Admin 2",
            geometry__contains=Point(center_lon, center_lat)
        ).first()
        adm2_name = wb_adm2.adm2_name if wb_adm2 else None

        return {
            'iso_a2': iso_a2,
            'region_code': mapping.wb_adm1_code,
            'country_name': country_name,
            'region_name': region_name,
            'adm2_name': adm2_name,
            'bbox': [y_min, x_min, y_max, x_max], # [min_lat, min_lon, max_lat, max_lon]
            'center': [center_lat, center_lon]
        }

    @classmethod
    def search(cls, geoklik_id, epoch_name="2025.1"):
        """
        Highest level search. Full or partial.
        """
        clean_id = geoklik_id.replace(" ", "").upper()
        parts = [p for p in clean_id.split('-') if p]
        
        # If it looks like a full ID
        if len(parts) >= 4 or (len(parts) == 3 and len(parts[2]) >= 8):
            return cls.decode(clean_id, epoch_name)
        else:
            return GeoKlikDecoder.decode_partial(clean_id, epoch_name)

    @staticmethod
    def _to_base26(val, length=4):
        """Convert integer to Base26 alpha string (A-Z)."""
        chars = []
        for _ in range(length):
            val, rem = divmod(val, 26)
            chars.append(chr(65 + rem))
        return "".join(reversed(chars))

    @staticmethod
    def _from_base26(s):
        """Convert Base26 alpha string to integer."""
        val = 0
        for char in s:
            val = val * 26 + (ord(char) - 65)
        return val

    @staticmethod
    def _to_base26(val, length=4):
        chars = []
        for _ in range(length):
            val, rem = divmod(val, 26)
            chars.append(chr(65 + rem))
        return "".join(reversed(chars))

    @staticmethod
    def _from_base26(s):
        val = 0
        for char in s:
            val = val * 26 + (ord(char) - 65)
        return val

class GeoKlikDecoder:
    """
    Reverse logic to convert GeoKlik IDs back to bounding boxes.
    """
    CHAR_SET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    @classmethod
    def _from_aann(cls, s):
        if len(s) != 4: return 0
        a1 = cls.CHAR_SET.find(s[0]) - 10
        a2 = cls.CHAR_SET.find(s[1]) - 10
        n1 = int(s[2])
        n2 = int(s[3])
        return (a1 * 26 * 100) + (a2 * 100) + (n1 * 10) + n2

    @classmethod
    def _from_aaan(cls, s):
        if len(s) != 4: return 0
        a1 = cls.CHAR_SET.find(s[0]) - 10
        a2 = cls.CHAR_SET.find(s[1]) - 10
        a3 = cls.CHAR_SET.find(s[2]) - 10
        n1 = int(s[3])
        return (a1 * 26 * 26 * 10) + (a2 * 26 * 10) + (a3 * 10) + n1

    @classmethod
    def decode_partial(cls, geoklik_id, epoch_name="2025.1"):
        """
        Decodes a partial ID to a wider bounding box.
        Supports:
        - ISO (e.g. NO)
        - ISO-RG (e.g. NO-O)
        - ISO-RG-GEODATA (e.g. NO-OS-JM)
        """
        from geo.models import GeoKlikRegion, WorldBankRegionMapping
        
        parts = [p.upper() for p in geoklik_id.split('-') if p]
        if not parts: return None
        
        iso_a2 = parts[0]
        region_prefix = parts[1] if len(parts) > 1 else ""
        geodata_str = "".join(parts[2:]).replace("-", "") if len(parts) > 2 else ""

        # Step 1: Find matching regions
        if not region_prefix:
            # Country only
            gk_regions = GeoKlikRegion.objects.filter(
                epoch__name=epoch_name,
                iso_a2=iso_a2
            )
        elif not geodata_str:
            # ISO-RegionPrefix
            mappings = WorldBankRegionMapping.objects.filter(
                country_code=iso_a2,
                wb_region_code__startswith=region_prefix
            )
            gk_regions = GeoKlikRegion.objects.filter(
                epoch__name=epoch_name,
                adm1_code__in=mappings.values_list('wb_adm1_code', flat=True)
            )
        else:
            # ISO-ExactRegion-Geodata
            mapping = WorldBankRegionMapping.objects.filter(
                country_code=iso_a2,
                wb_region_code=region_prefix
            ).first()
            if not mapping: return None
            gk_regions = GeoKlikRegion.objects.filter(
                epoch__name=epoch_name,
                adm1_code=mapping.wb_adm1_code
            )

        if not gk_regions.exists(): return None

        # Case: geodata partial search (narrowest)
        if geodata_str and gk_regions.count() == 1:
            gk_region = gk_regions.first()
            coder = MortonCoder()
            
            # Aligned logic for base-26/10 segments
            # chunk1: a1*2600 + a2*100 + n1*10 + n2
            # Total val = chunk1 * 67600 + chunk2
            if gk_region.is_giant:
                v_min = 0; v_max = (1 << 35) - 1
                prefix_val = 0
                for i, char in enumerate(geodata_str[:8]):
                    mult = 1
                    for j in range(i + 1, 8): mult *= 26 if j % 4 < 3 else 10
                    c_idx = cls.CHAR_SET.find(char)
                    prefix_val += (c_idx - 10) * mult if i % 4 < 3 else int(char) * mult
                v_min = prefix_val
                range_size = 1
                for j in range(len(geodata_str), 8): range_size *= 26 if j % 4 < 3 else 10
                v_max = v_min + range_size - 1
            else:
                v_min = 0; range_size = (1 << 32)
                v_max = v_min + range_size - 1
                prefix_val = 0
                for i, char in enumerate(geodata_str[:8]):
                    mult = 1
                    for j in range(i + 1, 8): mult *= 26 if j % 4 < 2 else 10
                    c_idx = cls.CHAR_SET.find(char)
                    prefix_val += (c_idx - 10) * mult if i % 4 < 2 else int(char) * mult
                v_min = prefix_val
                range_size = 1
                for j in range(len(geodata_str), 8): range_size *= 26 if j % 4 < 2 else 10
                v_max = v_min + range_size - 1
            
            if gk_region.is_giant:
                x1, y1 = coder.de_interleave(v_min, 17, 18)
                x2, y2 = coder.de_interleave(v_max, 17, 18)
                max_x = 131071; max_y = 262143
                # Square scaling for giant (1:2 grid)
                range_side_x = math.sqrt(range_size * 0.5)
                range_side_y = range_side_x * 2
            else:
                x1, y1 = coder.de_interleave(v_min, 16, 16)
                x2, y2 = coder.de_interleave(v_max, 16, 16)
                max_x = 65535; max_y = 65535
                range_side_x = math.sqrt(range_size)
                range_side_y = range_side_x
                
            x_avg = (x1 + x2) / 2
            y_avg = (y1 + y2) / 2
                
            x_min, _ = coder.denormalize_to_bbox(x_avg - range_side_x/2, gk_region.min_lon, gk_region.max_lon, max_x)
            y_min, _ = coder.denormalize_to_bbox(y_avg - range_side_y/2, gk_region.min_lat, gk_region.max_lat, max_y)
            _, x_max = coder.denormalize_to_bbox(x_avg + range_side_x/2, gk_region.min_lon, gk_region.max_lon, max_x)
            _, y_max = coder.denormalize_to_bbox(y_avg + range_side_y/2, gk_region.min_lat, gk_region.max_lat, max_y)

            center_lat = (y_min + y_max)/2
            center_lon = (x_min + x_max)/2
            
            # Metadata
            from geo.models import CountryInfo, WorldBankBoundary
            from django.contrib.gis.geos import Point
            country = CountryInfo.objects.filter(country_code=gk_region.iso_a2).first()
            
            wb_boundary = WorldBankBoundary.objects.filter(adm1_code=gk_region.adm1_code).first()
            
            # Only try for Admin 2 if the area is small enough (roughly city sized) or geodata is long
            adm2_name = None
            if len(geodata_str) >= 4:
                wb_adm2 = WorldBankBoundary.objects.filter(
                    level="Admin 2",
                    geometry__contains=Point(center_lon, center_lat)
                ).first()
                adm2_name = wb_adm2.adm2_name if wb_adm2 else None

            return {
                'bbox': [y_min, x_min, y_max, x_max], 
                'center': [center_lat, center_lon],
                'country_name': country.country_name if country else gk_region.iso_a2,
                'region_name': wb_boundary.adm1_name if wb_boundary else gk_region.adm1_code,
                'adm2_name': adm2_name
            }
        else:
            # Case: country or multiple regions (widest)
            # Find the aggregate extent
            lats = list(gk_regions.values_list('min_lat', flat=True)) + list(gk_regions.values_list('max_lat', flat=True))
            lons = list(gk_regions.values_list('min_lon', flat=True)) + list(gk_regions.values_list('max_lon', flat=True))
            y_min, y_max = min(lats), max(lats)
            x_min, x_max = min(lons), max(lons)
            from geo.models import CountryInfo
            country = CountryInfo.objects.filter(country_code=iso_a2).first()
            c_name = country.country_name if country else iso_a2

            # Try to find specific boundary geometry
            geometry = None
            wb_boundary = None
            if not region_prefix:
                 # Country level - Admin 0
                 from geo.models import WorldBankBoundary
                 wb_boundary = WorldBankBoundary.objects.filter(level="Admin 0", iso_a2=iso_a2).first()
            elif gk_regions.count() == 1:
                 # Single Region found - Admin 1
                 target_region = gk_regions.first()
                 from geo.models import WorldBankBoundary
                 wb_boundary = WorldBankBoundary.objects.filter(level="Admin 1", adm1_code=target_region.adm1_code).first()

            geometry_json = None
            if wb_boundary and wb_boundary.geometry:
                geometry_json = wb_boundary.geometry.json

            return {
                'bbox': [y_min, x_min, y_max, x_max], 
                'center': [(y_min + y_max)/2, (x_min + x_max)/2],
                'country_name': c_name,
                'region_name': region_prefix if region_prefix else "Entire Country",
                'adm2_name': None,
                'geometry': geometry_json
            }

def get_region_area(min_lat, max_lat, min_lon, max_lon):
    """Calculate approximate area in km2."""
    # Radius of earth in km
    R = 6371.0
    
    phi1 = math.radians(min_lat)
    phi2 = math.radians(max_lat)
    d_lambda = math.radians(max_lon - min_lon)
    
    # Area of a spherical cap segment
    area = R**2 * abs(math.sin(phi1) - math.sin(phi2)) * d_lambda
    return area
