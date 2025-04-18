import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ..location_tracker import LocationTracker
from .base_scraper import RestaurantScraper

class BKScraper(RestaurantScraper):
    @property
    def restaurant_name(self) -> str:
        return "bk"

    def get_locations_from_coordinates(self, lat, lon):
        try:
            
            time.sleep(0.5)
            url = f"https://use1-prod-bk-gateway.rbictg.com/graphql"
            
            # URL-encoded variables section with dynamic lat/lon
            variables = {
                "input": {
                    "pagination": {"first": 100},
                    "radiusStrictMode": True,
                    "coordinates": {
                        "searchRadius": 10000,
                        "userLat": lat,
                        "userLng": lon
                    }
                }
            }
            
            # Construct the full URL with encoded parameters
            encoded_variables = requests.utils.quote(json.dumps(variables))
            extensions = requests.utils.quote('{"persistedQuery":{"version":1,"sha256Hash":"823984086ffe25adca8294186fc551ab2aa4830da4e851f91298d423adab5b20"}}')
            
            new_url = f"{url}?operationName=GetNearbyRestaurants&variables={encoded_variables}&extensions={extensions}"
            
            response = requests.get(new_url)
            data = response.json()
            
            locations = []
            for restaurant in data.get('data', {}).get('restaurantsV2', {}).get('nearby', {}).get('nodes', []):
                address = restaurant.get('physicalAddress', {})
                if address and address.get('stateProvinceShort', '') == 'FL':  # Only add Florida locations
                    locations.append({
                        'street': address.get('address1', ''),
                        'city': address.get('city', ''),
                        'state': address.get('stateProvinceShort', ''),
                        'postal_code': address.get('postalCode', '').split('-')[0]  # Remove ZIP+4 suffix
                    })
            
            print(f"Processed {lat},{lon} - Found {len(locations)} locations")
            return locations
        except Exception as e:
            print(f"Error processing {lat},{lon}: {str(e)}")
            return []

    def scrape(self):
        start_time = time.time()
        all_locations = []
        
        # Read coordinates from gazetteer file
        coordinates = []
        with open('src/reference_data/2024_Gaz_zcta_national.txt', 'r') as f:
            # Skip header line
            next(f)
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 7:
                    zip_code = parts[0]
                    # Only process Florida ZIP codes (32xxx, 33xxx, 34xxx)
                    if zip_code.startswith(('32', '33', '34')):
                        lat = float(parts[5])
                        lon = float(parts[6])
                        coordinates.append((lat, lon))
        
        print(f"Processing {len(coordinates)} Florida coordinates...")
        
        # Reduce max_workers to 10 for rate limiting
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Process coordinates in smaller batches
            batch_size = 10
            for i in range(0, len(coordinates), batch_size):
                batch = coordinates[i:i + batch_size]
                future_to_coords = {
                    executor.submit(self.get_locations_from_coordinates, lat, lon): (lat, lon)
                    for lat, lon in batch
                }
                
                for future in as_completed(future_to_coords):
                    locations = future.result()
                    all_locations.extend(locations)

            time.sleep(1)
                
        
        # Remove duplicates based on all fields
        unique_locations = []
        seen = set()
        for loc in all_locations:
            location_tuple = tuple(loc.items())
            if location_tuple not in seen:
                seen.add(location_tuple)
                unique_locations.append(loc)
        
        print(f"\nScraping completed in {time.time() - start_time:.2f} seconds")
        print(f"Total {self.restaurant_name} locations found: {len(unique_locations)}")
        
        return unique_locations

if __name__ == "__main__":
    scraper = BKScraper()
    locations = scraper.scrape()
    
    # Save results to JSON file
    with open('bk_locations.json', 'w') as f:
        json.dump(locations, f, indent=2)
    
    # Initialize tracker
    tracker = LocationTracker()
    
    # Compare with historical data
    changes = tracker.compare_locations("bk", locations)
    
    # Output changes if any locations were removed
    if changes.removed_locations:
        print(f"\nRemoved Burger King locations as of {changes.date}:")
        for location in changes.removed_locations:
            print(f"- {location['street']}, {location['city']}, {location['state']} {location['postal_code']}")
    else:
        print("\nNo Burger King locations were removed")
    
    # Update historical data
    tracker.update_historical_data("bk", locations)
