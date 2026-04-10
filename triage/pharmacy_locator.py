import requests
import json
from django.conf import settings
from django.core.cache import cache

class PharmacyLocator:
    """Find nearby pharmacies using Google Places API"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api/place"
    
    def find_nearby_pharmacies(self, lat, lng, radius=5000, keyword=None):
        """
        Find pharmacies near a location
        
        Args:
            lat: Latitude
            lng: Longitude
            radius: Search radius in meters (max 50000)
            keyword: Optional search keyword
        
        Returns:
            list: Pharmacies with details
        """
        cache_key = f"pharmacies_{lat}_{lng}_{radius}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        url = f"{self.base_url}/nearbysearch/json"
        params = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'type': 'pharmacy',
            'key': self.api_key
        }
        
        if keyword:
            params['keyword'] = keyword
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK':
                pharmacies = []
                for place in data['results']:
                    pharmacies.append({
                        'id': place['place_id'],
                        'name': place['name'],
                        'address': place.get('vicinity', ''),
                        'location': place['geometry']['location'],
                        'rating': place.get('rating', 0),
                        'user_ratings_total': place.get('user_ratings_total', 0),
                        'open_now': place.get('opening_hours', {}).get('open_now', False),
                        'photo_reference': place.get('photos', [{}])[0].get('photo_reference', '')
                    })
                
                # Cache for 1 hour
                cache.set(cache_key, pharmacies, 3600)
                return pharmacies
            
            return []
        except Exception as e:
            print(f"Error finding pharmacies: {e}")
            return []
    
    def get_place_details(self, place_id):
        """Get detailed information about a specific pharmacy"""
        cache_key = f"place_details_{place_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        url = f"{self.base_url}/details/json"
        params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,formatted_phone_number,website,opening_hours,rating,reviews,geometry',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK':
                result = data['result']
                details = {
                    'name': result.get('name'),
                    'address': result.get('formatted_address'),
                    'phone': result.get('formatted_phone_number'),
                    'website': result.get('website'),
                    'rating': result.get('rating'),
                    'hours': result.get('opening_hours', {}).get('weekday_text', []),
                    'location': result.get('geometry', {}).get('location')
                }
                cache.set(cache_key, details, 86400)  # Cache for 24 hours
                return details
            
            return None
        except Exception as e:
            print(f"Error getting place details: {e}")
            return None

pharmacy_locator = PharmacyLocator()