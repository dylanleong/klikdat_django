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
