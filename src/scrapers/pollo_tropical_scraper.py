import requests
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys
import os
from ..location_tracker import LocationTracker
from .base_scraper import RestaurantScraper

class PolloTropicalScraper(RestaurantScraper):
    @property
    def restaurant_name(self) -> str:
        return "pollo_tropical"

    def get_location_details(self, url, city, state):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            locations = []
            
            container = soup.find('div', class_='container my-8')
            if container:
                location_list = container.find('ul')
                if location_list:
                    for location in location_list.find_all('li'):
                        address_div = location.find('div', class_='Core-nearbyLocAddress')
                        if address_div:
                            street = address_div.text.strip()
                            locations.append({
                                'street': street,
                                'city': city,
                                'state': state,
                                'postal_code': ''  # Website doesn't provide postal code
                            })
            
            print(f"Processed {url} - Found {len(locations)} locations")
            return locations
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            return []

    def scrape(self):
        start_time = time.time()
        base_url = 'https://locations.pollotropical.com/fl'
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        all_locations = []
        container = soup.find('div', class_='container my-8')
        city_links = container.find('ul')
        
        urls_to_process = []
        for city in city_links.find_all('li'):
            city_link = city.find('a')
            if city_link:
                city_name = city_link.text.strip()
                city_url = f"https://locations.pollotropical.com/{city_link['href']}"
                urls_to_process.append((city_url, city_name, 'FL'))
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {
                executor.submit(self.get_location_details, url, city, state): url 
                for url, city, state in urls_to_process
            }
            
            for future in as_completed(future_to_url):
                locations = future.result()
                all_locations.extend(locations)
        
        print(f"\nScraping completed in {time.time() - start_time:.2f} seconds")
        print(f"Total {self.restaurant_name} locations found: {len(all_locations)}")
        
        return all_locations

if __name__ == "__main__":
    scraper = PolloTropicalScraper()
    locations = scraper.scrape()
    
    # Save results to JSON file
    with open('pollo_tropical_locations.json', 'w') as f:
        json.dump(locations, f, indent=2)
    
    # Initialize tracker
    tracker = LocationTracker()
    
    # Compare with historical data
    changes = tracker.compare_locations("pollo_tropical", locations)
    
    # Output changes if any locations were removed
    if changes.removed_locations:
        print(f"\nRemoved Pollo Tropical locations as of {changes.date}:")
        for location in changes.removed_locations:
            print(f"- {location['street']}, {location['city']}, {location['state']} {location['postal_code']}")
    else:
        print("\nNo Pollo Tropical locations were removed")
    
    # Update historical data
    tracker.update_historical_data("pollo_tropical", locations) 