import requests
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys
import os
from ..location_tracker import LocationTracker
from .base_scraper import RestaurantScraper

class WendysScraper(RestaurantScraper):
    @property
    def restaurant_name(self) -> str:
        return "wendys"

    def get_location_details(self, url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            locations = []
            
            # First check for multiple locations
            location_list = soup.find('ul', class_='Directory-listTeasers')
            if location_list:
                for address in location_list.find_all('address', class_='c-address'):
                    street = address.find('span', class_='c-address-street-1').text.strip()
                    city = address.find('span', class_='c-address-city').text.strip()
                    state = address.find('abbr', class_='c-address-state').text.strip()
                    postal_code = address.find('span', class_='c-address-postal-code').text.strip()
                    locations.append({
                        'street': street,
                        'city': city,
                        'state': state,
                        'postal_code': postal_code
                    })
            else:
                # If no directory list found, check for single location
                single_location = soup.find('address', class_='c-address')
                if single_location:
                    street = single_location.find('span', class_='c-address-street-1').text.strip()
                    city = single_location.find('span', class_='c-address-city').text.strip()
                    state = single_location.find('abbr', class_='c-address-state').text.strip()
                    postal_code = single_location.find('span', class_='c-address-postal-code').text.strip()
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
        base_url = 'https://locations.wendys.com/united-states/fl'
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        all_locations = []
        city_links = soup.find('ul', class_='Directory-listLinks')
        
        urls_to_process = [
            f'https://locations.wendys.com{city.find("a")["href"].replace("..", "")}'
            for city in city_links.find_all('li')
        ]
        
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
    scraper = WendysScraper()
    locations = scraper.scrape()
    
    # Save results to JSON file
    with open('wendys_locations.json', 'w') as f:
        json.dump(locations, f, indent=2)
    
    # Initialize tracker
    tracker = LocationTracker()
    
    # Compare with historical data
    changes = tracker.compare_locations("wendys", locations)
    
    # Output changes if any locations were removed
    if changes.removed_locations:
        print(f"\nRemoved Wendy's locations as of {changes.date}:")
        for location in changes.removed_locations:
            print(f"- {location['street']}, {location['city']}, {location['state']} {location['postal_code']}")
    else:
        print("\nNo Wendy's locations were removed")
    
    # Update historical data
    tracker.update_historical_data("wendys", locations)
