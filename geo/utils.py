import math

class CoordinateTransformer:
    """
    Utilities for mapping geographic coordinates to normalized integer spaces.
    """

    @staticmethod
    def normalize_to_int(value, min_val, max_val, max_int):
        """Map a float value into [0, max_int] bins."""
        num_bins = max_int + 1
        if value <= min_val: return 0
        if value >= max_val: return max_int
        
        step = (max_val - min_val) / num_bins
        return int((value - min_val) / step)

    @staticmethod
    def denormalize_from_int(val_int, min_val, max_val, max_int):
        """Map an integer to the center float of the corresponding bin."""
        num_bins = max_int + 1
        step = (max_val - min_val) / num_bins
        return min_val + (val_int + 0.5) * step

    @staticmethod
    def denormalize_to_bbox(val_int, min_val, max_val, max_int):
        """Map an integer bin index to its bounding box edges."""
        num_bins = max_int + 1
        step = (max_val - min_val) / num_bins
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
        """
        Pattern: AANN-AANN (4 alpha, 4 numeric)
        Method: Bitwise Split Quadtree
        Total Bits: 32 (16X, 16Y)
        Split: High 16 bits, Low 16 bits.
        """
        val = interleaved_32
        
        # Split at bit 16
        chunk1 = val >> 16
        chunk2 = val & 0xFFFF
        
        return f"{cls._to_aann(chunk1)}-{cls._to_aann(chunk2)}"

    @classmethod
    def encode_giant(cls, interleaved_34):
        """
        Pattern: AAAN-AAAN (6 alpha, 2 numeric)
        Method: Bitwise Split Quadtree
        Total Bits: 34 (17X, 17Y)
        Split: High 17 bits, Low 17 bits.
        """
        val = interleaved_34
        
        # Split at bit 17
        chunk1 = val >> 17
        chunk2 = val & 0x1FFFF
        
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

class HilbertCoder:
    @staticmethod
    def rot(n, x, y, rx, ry):
        if ry == 0:
            if rx == 1:
                x = n - 1 - x
                y = n - 1 - y
            return y, x
        return x, y

    @classmethod
    def xy2d(cls, n, x, y):
        d = 0
        s = n // 2
        while s > 0:
            rx = 1 if (x & s) > 0 else 0
            ry = 1 if (y & s) > 0 else 0
            d += s * s * ((3 * rx) ^ ry)
            x, y = cls.rot(s, x, y, rx, ry)
            s //= 2
        return d

    @classmethod
    def d2xy(cls, n, d):
        x = y = 0
        s = 1
        t = d
        while s < n:
            rx = 1 & (t // 2)
            ry = 1 & (t ^ rx)
            x, y = cls.rot(s, x, y, rx, ry)
            x += s * rx
            y += s * ry
            t //= 4
            s *= 2
        return x, y


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
                
                # Ocean Encoding: OO-RR-AAAN-AAAN (Hilbert 34-bit)
                # Unifying Ocean with standard Hilbert curve logic.
                n_val = 1 << 17
                x_int = CoordinateTransformer.normalize_to_int(lon, gk_region.min_lon, gk_region.max_lon, 131071)
                y_int = CoordinateTransformer.normalize_to_int(lat, gk_region.min_lat, gk_region.max_lat, 131071)
                d_val = HilbertCoder.xy2d(n_val, x_int, y_int)
                geodata = GeoKlikEncoder.encode_giant(d_val)
                
                id_str = f"{gk_region.iso_a2}-{gk_region.adm1_code}-{geodata}"
                
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
            # 34-bit Hilbert (17 bits per dimension)
            n_val = 1 << 17
            x_int = CoordinateTransformer.normalize_to_int(lon, gk_region.min_lon, gk_region.max_lon, 131071)
            y_int = CoordinateTransformer.normalize_to_int(lat, gk_region.min_lat, gk_region.max_lat, 131071)
            d_val = HilbertCoder.xy2d(n_val, x_int, y_int)
            geodata = GeoKlikEncoder.encode_giant(d_val)
        else:
            # 32-bit Hilbert (16 bits per dimension)
            n_val = 1 << 16
            x_int = CoordinateTransformer.normalize_to_int(lon, gk_region.min_lon, gk_region.max_lon, 65535)
            y_int = CoordinateTransformer.normalize_to_int(lat, gk_region.min_lat, gk_region.max_lat, 65535)
            d_val = HilbertCoder.xy2d(n_val, x_int, y_int)
            geodata = GeoKlikEncoder.encode_standard(d_val)

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
        
        iso_a2 = parts[0].upper()
        if iso_a2 == 'OO':
            # Unified Ocean Decoding (Hilbert 34-bit)
            # Format: OO-RR-AAAN-AAAN
            if len(parts) < 4: return None
            region_code = parts[1]
            
            # Find Region by Code
            gk_region = GeoKlikRegion.objects.filter(
                epoch__name=epoch_name,
                iso_a2='OO',
                adm1_code=region_code
            ).first()
            if not gk_region: return None

            geodata = geoklik_id.split('-', 2)[2] # Get everything after OO-RR
            parts_geo = geodata.split('-')
            
            decoder = GeoKlikDecoder()
            v1 = decoder._from_aaan(parts_geo[0])
            v2 = decoder._from_aaan(parts_geo[1])
            d_val = (v1 << 17) | v2
            
            n_val = 1 << 17
            x_int, y_int = HilbertCoder.d2xy(n_val, d_val)
            
            x_min, x_max = CoordinateTransformer.denormalize_to_bbox(x_int, gk_region.min_lon, gk_region.max_lon, 131071)
            y_min, y_max = CoordinateTransformer.denormalize_to_bbox(y_int, gk_region.min_lat, gk_region.max_lat, 131071)
            
            center_lat = (y_min + y_max)/2
            center_lon = (x_min + x_max)/2
            
            # Since regions might overlap (East/West Pacific), we assume the code (PE vs PW) is sufficient.
            
            return {
                'iso_a2': iso_a2,
                'region_code': region_code,
                'country_name': "International Waters", 
                'region_name': gk_region.iso_a2,
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

        decoder = GeoKlikDecoder()
        
        if gk_region.is_giant:
            # Giant: AAAN-AAAN (6 Alpha, 2 Numeric) 34 bits (17x, 17y)
            geodata_str = "".join(geodata).replace("-", "")
            if len(geodata_str) < 8: return None
            
            v1 = decoder._from_aaan(geodata_str[:4])
            v2 = decoder._from_aaan(geodata_str[4:8])
            d_val = (v1 << 17) | v2
            
            n_val = 1 << 17
            x_int, y_int = HilbertCoder.d2xy(n_val, d_val)
            
            x_min, x_max = CoordinateTransformer.denormalize_to_bbox(x_int, gk_region.min_lon, gk_region.max_lon, 131071)
            y_min, y_max = CoordinateTransformer.denormalize_to_bbox(y_int, gk_region.min_lat, gk_region.max_lat, 131071)
        else:
            # Standard: AANN-AANN (4 Alpha, 4 Numeric) 32 bits (16x, 16y)
            geodata_str = "".join(geodata).replace("-", "")
            if len(geodata_str) < 8: return None
            
            v1 = decoder._from_aann(geodata_str[:4])
            v2 = decoder._from_aann(geodata_str[4:8])
            d_val = (v1 << 16) | v2
            
            n_val = 1 << 16
            x_int, y_int = HilbertCoder.d2xy(n_val, d_val)
            x_min, x_max = CoordinateTransformer.denormalize_to_bbox(x_int, gk_region.min_lon, gk_region.max_lon, 65535)
            y_min, y_max = CoordinateTransformer.denormalize_to_bbox(y_int, gk_region.min_lat, gk_region.max_lat, 65535)

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
        
        # Route based on geodata length
        geodata_str = "".join(parts[2:]).replace("-", "") if len(parts) > 2 else ""
        
        if len(geodata_str) >= 8:
            # Full ID (at least 8 chars of geodata)
            return cls.decode(clean_id, epoch_name)
        else:
            # Partial ID
            return GeoKlikDecoder.decode_partial(clean_id, epoch_name)

    @staticmethod
    def _to_base26(val, length=4):
        """Convert integer to Base26 alpha string (A-Z)."""
        chars = []
        for _ in range(length):
            val, rem = divmod(val, 26)
            chars.append(chr(65 + rem))
        return "".join(reversed(chars))

    @classmethod
    def get_subgrid(cls, geoklik_id, epoch_name="2025.1"):
        """
        Returns the next level of hierarchical sub-regions for a given prefix.
        """
        from geo.models import GeoKlikRegion, WorldBankRegionMapping
        clean_id = geoklik_id.replace(" ", "").upper()
        parts = [p for p in clean_id.split('-') if p]
        
        if len(parts) == 0: return []
        
        iso_a2 = parts[0]
        
        # Level 1: ISO -> ADM1 Regions (ISO-RG)
        if len(parts) == 1:
            regions = GeoKlikRegion.objects.filter(
                iso_a2=iso_a2, 
                epoch__name=epoch_name
            )
            mappings = {
                m.wb_adm1_code: m.wb_region_code 
                for m in WorldBankRegionMapping.objects.filter(country_code=iso_a2)
            }
            data = []
            for r in regions:
                 code = mappings.get(r.adm1_code, "XX")
                 data.append({
                     'id': f"{r.iso_a2}-{code}",
                     'label': code,
                     'bbox': [r.min_lat, r.min_lon, r.max_lat, r.max_lon]
                 })
            return data

        # Level 2+: Drill down into Hilbert grid
        region_code = parts[1]
        geodata_prefix = "".join(parts[2:]).replace("-", "")
        
        mapping = WorldBankRegionMapping.objects.filter(
            country_code=iso_a2,
            wb_region_code=region_code
        ).first()
        if not mapping: return []
        
        gk_region = GeoKlikRegion.objects.filter(
            epoch__name=epoch_name,
            adm1_code=mapping.wb_adm1_code
        ).first()
        if not gk_region: return []

        shift = 17 if gk_region.is_giant else 16
        n_full = 1 << shift
        pattern = 'giant' if gk_region.is_giant else 'standard'
        
        # Determine current depth and next chars
        depth = len(geodata_prefix)
        if depth >= 8: return [] # Already at full resolution
        
        # Segment 3 hierarchy: chars 0-3
        # Segment 4 hierarchy: chars 4-7
        current_segment = geodata_prefix[:4] if depth < 4 else geodata_prefix[4:]
        segment_depth = len(current_segment)
        
        # Giant (AAAN): 26, 26, 26, 10
        # Standard (AANN): 26, 26, 10, 10
        if pattern == 'giant':
            is_alpha = [True, True, True, False]
            bases = [26, 26, 26, 10]
        else:
            is_alpha = [True, True, False, False]
            bases = [26, 26, 10, 10]

        char_set = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        next_chars = []
        if is_alpha[segment_depth]:
            next_chars = [char_set[10 + i] for i in range(26)]
        else:
            next_chars = [str(i) for i in range(10)]


        data = []
        decoder = GeoKlikDecoder()
        
        # If we are drilling into the first segment (chars 0-3)
        if depth < 4:
            for char in next_chars:
                test_prefix = geodata_prefix + char
                h_min, h_max = decoder._decode_mixed_range(test_prefix, pattern)
                
                x1, x2, y1, y2 = GeoKlikDecoder._scan_curve_range_bbox(
                    h_min << shift, (h_max << shift) + ((1 << shift) - 1), n_full
                )
                
                max_code = 131071 if gk_region.is_giant else 65535
                ln_min, _ = CoordinateTransformer.denormalize_to_bbox(x1, gk_region.min_lon, gk_region.max_lon, max_code)
                _, ln_max = CoordinateTransformer.denormalize_to_bbox(x2, gk_region.min_lon, gk_region.max_lon, max_code)
                lt_min, _ = CoordinateTransformer.denormalize_to_bbox(y1, gk_region.min_lat, gk_region.max_lat, max_code)
                _, lt_max = CoordinateTransformer.denormalize_to_bbox(y2, gk_region.min_lat, gk_region.max_lat, max_code)

                data.append({
                    'id': f"{iso_a2}-{region_code}-{test_prefix}",
                    'label': test_prefix,
                    'bbox': [lt_min, ln_min, lt_max, ln_max]
                })
        else:
            # Drilling into second segment (Low Chunks)
            h_val = decoder._from_aaan(geodata_prefix[:4]) if pattern == 'giant' else decoder._from_aann(geodata_prefix[:4])
            offset = h_val << shift
            
            for char in next_chars:
                test_suffix = current_segment + char
                l_min, l_max = decoder._decode_mixed_range(test_suffix, pattern)
                
                x1, x2, y1, y2 = GeoKlikDecoder._scan_curve_range_bbox(
                    offset + l_min, offset + l_max, n_full
                )
                
                max_code = 131071 if gk_region.is_giant else 65535
                ln_min, _ = CoordinateTransformer.denormalize_to_bbox(x1, gk_region.min_lon, gk_region.max_lon, max_code)
                _, ln_max = CoordinateTransformer.denormalize_to_bbox(x2, gk_region.min_lon, gk_region.max_lon, max_code)
                lt_min, _ = CoordinateTransformer.denormalize_to_bbox(y1, gk_region.min_lat, gk_region.max_lat, max_code)
                _, lt_max = CoordinateTransformer.denormalize_to_bbox(y2, gk_region.min_lat, gk_region.max_lat, max_code)

                full_id = f"{iso_a2}-{region_code}-{geodata_prefix[:4]}-{test_suffix}"
                data.append({
                    'id': full_id,
                    'label': test_suffix,
                    'bbox': [lt_min, ln_min, lt_max, ln_max]
                })
        
        return data



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
    def _decode_mixed_range(cls, partial_s, pattern_type):
        """
        Given a partial string (e.g. "G", "GW", "GW9"), returns the (min, max) integer
        range that this prefix covers in the full chunk space.
        pattern_type: 'standard' (AANN) or 'giant' (AAAN)
        """
        if pattern_type == 'giant':
            # AAAN: 26, 26, 26, 10
            bases = [26, 26, 26, 10]
            mults = [6760, 260, 10, 1]
            is_alpha = [True, True, True, False]
        else:
            # AANN: 26, 26, 10, 10
            bases = [26, 26, 10, 10]
            mults = [2600, 100, 10, 1]
            is_alpha = [True, True, False, False]
            
        val_min = 0; val_max = 0
        common_val = 0
        
        # 1. Base value from provided chars
        for i, char in enumerate(partial_s):
            if i >= 4: break
            c_idx = cls.CHAR_SET.find(char)
            digit_val = (c_idx - 10) if is_alpha[i] else int(char)
            common_val += digit_val * mults[i]
            
        val_min = common_val
        val_max = common_val
        
        # 2. Add range for missing suffixes
        for i in range(len(partial_s), 4):
            val_max += (bases[i] - 1) * mults[i]
            
        return val_min, val_max

    @classmethod
    def _get_aligned_hilbert_mbr(cls, d_val, b_shift, n_full):
        """
        Returns the MBR of an aligned Hilbert block of size 2^b_shift.
        For aligned Hilbert indices, this corresponds to a square (even shift)
        or a rectangle (odd shift).
        """
        # We find a point in the block
        x, y = HilbertCoder.d2xy(n_full, d_val << b_shift)
        
        # For a block of size 2^b, the coordinates are aligned to power-of-2 bounds.
        # Standard split: bits_total=32, b=16. x_bits=8, y_bits=8.
        # Giant split: bits_total=34, b=17. x_bits=9, y_bits=8 (or vice versa).
        
        # Rule: X gets more bits if b is odd in this implementation.
        # b=1 maps to rx=bit 1, ry=bit 0... so bits 0,1 are quadrant 1.
        # Bits 0..b-1 are consumed.
        x_bits = (b_shift + 1) // 2
        y_bits = b_shift // 2
        
        x_min = (x >> x_bits) << x_bits
        y_min = (y >> y_bits) << y_bits
        return x_min, x_min + (1 << x_bits) - 1, y_min, y_min + (1 << y_bits) - 1

    @classmethod
    def _scan_curve_range_bbox(cls, v_min, v_max, n):
        """
        Iteratively scans the Hilbert Curve range [v_min, v_max] to find the
        True Minimum Bounding Rectangle (MBR).
        """
        v_limit = n * n - 1
        v_min = min(v_min, v_limit)
        v_max = min(v_max, v_limit)
        
        if v_min > v_max:
             return 0, 0, 0, 0
             
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')
        
        count = v_max - v_min + 1
        
        if count > 10000:
             step = count // 100
             for val in range(v_min, v_max + 1, step):
                 x, y = HilbertCoder.d2xy(n, val)
                 if x < min_x: min_x = x
                 if x > max_x: max_x = x
                 if y < min_y: min_y = y
                 if y > max_y: max_y = y
             for val in [v_min, v_max]:
                 x, y = HilbertCoder.d2xy(n, val)
                 if x < min_x: min_x = x
                 if x > max_x: max_x = x
                 if y < min_y: min_y = y
                 if y > max_y: max_y = y
             return min_x, max_x, min_y, max_y

        for val in range(v_min, v_max + 1):
            x, y = HilbertCoder.d2xy(n, val)
            if x < min_x: min_x = x
            if x > max_x: max_x = x
            if y < min_y: min_y = y
            if y > max_y: max_y = y
            
        if min_x == float('inf'):
             return 0, 0, 0, 0

        return min_x, max_x, min_y, max_y

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
            
            # Aligned logic for base-26/10 segments
            # chunk1: a1*2600 + a2*100 + n1*10 + n2
            # Total val = chunk1 * 67600 + chunk2
            # Use helper to decode partial/full ranges for chunks
            high_str = geodata_str[:4]
            low_str = geodata_str[4:] if len(geodata_str) > 4 else ""
            
            pattern = 'giant' if gk_region.is_giant else 'standard'
            shift = 17 if gk_region.is_giant else 16
            
            decoder = GeoKlikDecoder()
            h_min, h_max = decoder._decode_mixed_range(high_str, pattern)
            
            x_min_int, x_max_int = 0, 0
            n_full = 1 << shift
            if len(high_str) < 4:
                # We are scanning ranges of High Chunks.
                # Each High Chunk is an aligned Hilbert block of size 2^shift.
                vals_h = range(h_min, h_max + 1)
                x_mins, y_mins, x_maxs, y_maxs = [], [], [], []
                
                # Safety cap for tile iteration
                display_vals = vals_h
                max_iter = 500
                if len(vals_h) > max_iter:
                    step = len(vals_h) // max_iter
                    display_vals = list(vals_h[::step]) + [vals_h[-1]]

                for h in display_vals:
                    x1, x2, y1, y2 = cls._get_aligned_hilbert_mbr(h, shift, n_full)
                    x_mins.append(x1); x_maxs.append(x2)
                    y_mins.append(y1); y_maxs.append(y2)
                
                x_min_int, x_max_int = min(x_mins), max(x_maxs)
                y_min_int, y_max_int = min(y_mins), max(y_maxs)
                
            else:
                # h_min is single value.
                if low_str:
                    l_min, l_max = decoder._decode_mixed_range(low_str, pattern)
                    offset = (h_min << shift)
                    x_min_int, x_max_int, y_min_int, y_max_int = cls._scan_curve_range_bbox(
                        offset + l_min, offset + l_max, n_full
                    )
                else:
                    # Full Tile for single h_min
                    x_min_int, x_max_int, y_min_int, y_max_int = cls._get_aligned_hilbert_mbr(h_min, shift, n_full)

            max_code = 131071 if gk_region.is_giant else 65535
            
            x_min, _ = CoordinateTransformer.denormalize_to_bbox(x_min_int, gk_region.min_lon, gk_region.max_lon, max_code)
            _, x_max = CoordinateTransformer.denormalize_to_bbox(x_max_int, gk_region.min_lon, gk_region.max_lon, max_code)
            y_min, _ = CoordinateTransformer.denormalize_to_bbox(y_min_int, gk_region.min_lat, gk_region.max_lat, max_code)
            _, y_max = CoordinateTransformer.denormalize_to_bbox(y_max_int, gk_region.min_lat, gk_region.max_lat, max_code)

            center_lat = (y_min+y_max)/2
            center_lon = (x_min+x_max)/2
            
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
