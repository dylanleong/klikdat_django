from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from geo.utils import GeoKlikService

class GeoKlikViewSet(viewsets.ViewSet):
    """
    API endpoints for GeoKlik encoding and searching.
    """
    
    @action(detail=False, methods=['get'])
    def encode(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        
        if not lat or not lon:
            return Response(
                {"error": "lat and lon parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return Response(
                {"error": "Invalid lat or lon values"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        result = GeoKlikService.encode(lat, lon)
        return Response(result)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q')
        
        if not query:
            return Response(
                {"error": "q (query) parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        result = GeoKlikService.search(query)
        
        if not result:
            return Response(
                {"error": "No matches found for this ID or prefix"},
                status=status.HTTP_200_OK
            )
            
        return Response(result)

    @action(detail=False, methods=['get'])
    def subregions(self, request):
        geoklik_id = request.query_params.get('id')
        if not geoklik_id:
             return Response({"error": "id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        from geo.models import GeoKlikRegion, WorldBankRegionMapping
        
        clean_id = geoklik_id.replace(" ", "").upper()
        parts = [p for p in clean_id.split('-') if p]
        
        # Only support subregions for Country level (First section)
        if len(parts) == 1:
            iso_a2 = parts[0]
            # Get all regions for this country
            regions = GeoKlikRegion.objects.filter(
                iso_a2=iso_a2, 
                epoch__name="2025.1"
            )
            
            data = []
            # Prefetch mappings to avoid N+1
            mappings = {
                m.wb_adm1_code: m.wb_region_code 
                for m in WorldBankRegionMapping.objects.filter(country_code=iso_a2)
            }
            
            for r in regions:
                 code = mappings.get(r.adm1_code, "XX")
                 data.append({
                     'id': f"{r.iso_a2}-{code}",
                     'bbox': [r.min_lat, r.min_lon, r.max_lat, r.max_lon]
                 })
            return Response(data)

        # Support subregions (Admin 2) for Region level (Second section)
        if len(parts) == 2:
            iso_a2 = parts[0]
            region_code = parts[1]
            
            mapping = WorldBankRegionMapping.objects.filter(
                country_code=iso_a2,
                wb_region_code=region_code
            ).first()
            
            if not mapping:
                return Response([])
                
            # Get all Admin 2 boundaries for this Admin 1 region
            from geo.models import WorldBankBoundary
            adm2_boundaries = WorldBankBoundary.objects.filter(
                level="Admin 2",
                adm1_code=mapping.wb_adm1_code
            )
            
            data = []
            for b in adm2_boundaries:
                if b.geometry:
                    xmin, ymin, xmax, ymax = b.geometry.extent
                    # Return generic ID since we don't have GeoKlik ID for Admin 2
                    data.append({
                        'id': f"{b.adm2_name}",
                        'bbox': [ymin, xmin, ymax, xmax]
                    })
            return Response(data)
            
        return Response([])
