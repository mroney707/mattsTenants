import requests
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from ..location_tracker import LocationTracker
from .base_scraper import RestaurantScraper

class DennysScraper(RestaurantScraper):
    @property
    def restaurant_name(self) -> str:
        return "dennys"

    def get_location_details(self, url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            locations = []
            
            # Check for multiple locations
            stores_container = soup.find('div', class_='stores-container')
            if stores_container:
                for store in stores_container.find_all('div', class_='gtm-store shadow'):
                    address_span = store.find('span', class_='address')
                    if address_span:
                        address_parts = address_span.text.strip().split(',')
                        if len(address_parts) >= 4:  # Changed from 3 to 4 since state and zip are separate
                            street = address_parts[0].strip()
                            city = address_parts[1].strip()
                            state = address_parts[2].strip()  # State is now its own part
                            postal_code = address_parts[3].strip()  # Zip code is now its own part
                            locations.append({
                                'street': street,
                                'city': city,
                                'state': state,
                                'postal_code': postal_code
                            })
            
            print(f"Processed {url} - Found {len(locations)} locations")
            return locations
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            return []

    def scrape(self):
        start_time = time.time()
        base_url = 'https://locations.dennys.com/FL'
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        all_locations = []
        city_blocks = soup.find_all('div', class_='cities-block')
        
        urls_to_process = []
        for block in city_blocks:
            for city_link in block.find_all('a'):
                if city_link.get('href'):
                    urls_to_process.append(city_link['href'])  # Use href directly since it's already a full URL
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {
                executor.submit(self.get_location_details, url): url 
                for url in urls_to_process
            }
            
            for future in as_completed(future_to_url):
                locations = future.result()
                all_locations.extend(locations)
        
        print(f"\nScraping completed in {time.time() - start_time:.2f} seconds")
        print(f"Total {self.restaurant_name} locations found: {len(all_locations)}")
        
        return all_locations

if __name__ == "__main__":
    scraper = DennysScraper()
    locations = scraper.scrape()
    
    # Save results to JSON file
    with open('dennys_locations.json', 'w') as f:
        json.dump(locations, f, indent=2)
    
    # Initialize tracker
    tracker = LocationTracker()
    
    # Compare with historical data
    changes = tracker.compare_locations("dennys", locations)
    
    # Output changes if any locations were removed
    if changes.removed_locations:
        print(f"\nRemoved Denny's locations as of {changes.date}:")
        for location in changes.removed_locations:
            print(f"- {location['street']}, {location['city']}, {location['state']} {location['postal_code']}")
    else:
        print("\nNo Denny's locations were removed")
    
    # Update historical data
    tracker.update_historical_data("dennys", locations)
