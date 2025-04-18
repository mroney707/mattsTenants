import requests
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys
import os
from ..location_tracker import LocationTracker
from .base_scraper import RestaurantScraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class ArbysScraper(RestaurantScraper):
    def __init__(self):
        super().__init__()
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=chrome_options)

    @property
    def restaurant_name(self) -> str:
        return "arbys"

    def get_location_details(self, url):
        try:
            self.driver.get(url)
            time.sleep(2)
            # Wait for location tiles to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'cityLocationTile_leftColumn__MNTz5'))
            )
            
            locations = []
            location_tiles = self.driver.find_elements(By.CLASS_NAME, 'cityLocationTile_leftColumn__MNTz5')
            
            for tile in location_tiles:
                address_link = tile.find_element(By.CLASS_NAME, 'cityLocationTile_addressLink__2OikU')
                address_text = address_link.text.strip()
                address_lines = address_text.split('\n')
                
                # Find the line that starts with a number (street address)
                street = None
                for line in address_lines:
                    if line and line[0].isdigit():
                        street = line
                        break
                
                # Get the last line which should contain city, state, zip
                location_line = address_lines[-1]
                location_parts = location_line.split(', ')
                
                if street and len(location_parts) == 2:
                    city = location_parts[0].strip()
                    state_zip = location_parts[1].split(' ')
                    if len(state_zip) == 2:
                        state = state_zip[0].strip()
                        postal_code = state_zip[1].strip()
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
        base_url = 'https://www.arbys.com/locations/us/fl/'
        
        try:
            self.driver.get(base_url)
            # Wait for cities container to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'stateLocationsTile_citesContainer__aZiEj'))
            )
            
            city_links = self.driver.find_elements(
                By.CSS_SELECTOR, 
                '.cityLocationsContainer_link__vqyGx'
            )
            
            urls_to_process = [
                link.get_attribute('href')
                for link in city_links
            ]
            
            all_locations = []
            with ThreadPoolExecutor(max_workers=1) as executor:
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
        except Exception as e:
            print(f"Error scraping: {str(e)}")
            return []

    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

if __name__ == "__main__":
    scraper = ArbysScraper()
    locations = scraper.scrape()
    
    # Save results to JSON file
    with open('arbys_locations.json', 'w') as f:
        json.dump(locations, f, indent=2)
    
    # Initialize tracker
    tracker = LocationTracker()
    
    # Compare with historical data
    changes = tracker.compare_locations("arbys", locations)
    
    # Output changes if any locations were removed
    if changes.removed_locations:
        print(f"\nRemoved Arby's locations as of {changes.date}:")
        for location in changes.removed_locations:
            print(f"- {location['street']}, {location['city']}, {location['state']} {location['postal_code']}")
    else:
        print("\nNo Arby's locations were removed")
    
    # Update historical data
    tracker.update_historical_data("arbys", locations) 