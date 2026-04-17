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


class PopeyesScraper(RestaurantScraper):
    def __init__(self):
        super().__init__()
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=chrome_options)

    @property
    def restaurant_name(self) -> str:
        return "popeyes"

    def scrape(self):
        # start_time = time.time()
        base_url = 'https://www.popeyes.com/restaurants'
        self.driver.get(base_url)
        time.sleep(10)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'css-146c3p1'))
        )

        address_a_tags = self.driver.find_elements(By.CLASS_NAME, 'css-146c3p1')

        all_locations = []

        for a_tag in address_a_tags:
            text = a_tag.text.strip()

            # Remove non-ASCII characters
            cleaned = text.encode("ascii", errors="ignore").decode("ascii")

            # Split into lines
            lines = [line.strip() for line in cleaned.split("\n") if line.strip()]

            if len(lines) != 2:
                continue  # skip malformed addresses

            street = lines[0]

            # Split "City, State Postal"
            city_part, state_zip_part = lines[1].split(",", 1)
            city = city_part.strip()

            state_parts = state_zip_part.strip().split()
            state = state_parts[0]
            postal_code = " ".join(state_parts[1:])

            address_dict = {
                "street": street,
                "city": city,
                "state": state,
                "postal_code": postal_code
            }

            if address_dict['state'] == 'Florida':
                all_locations.append(address_dict)


        # base_url = 'https://locations.wendys.com/united-states/fl'
        # response = requests.get(base_url)
        # soup = BeautifulSoup(response.text, 'html.parser')
        #
        # city_unordered_list_element = soup.find('ul', class_='Directory-listLinks')
        # city_link_element_list = city_unordered_list_element.find_all('li')
        # city_link_list = []

        # for city_link_item in city_link_element_list:
        #   city_link_a = city_link_item.find('a')
        #   city_link_href = city_link_a['href']
        #   city_link_list.append(city_link_href)
        #
        # urls_to_process = [
        #     f'https://locations.wendys.com{city.find("a")["href"].replace("..", "")}'
        #     for city in city_links.find_all('li')
        # ]
        #
        # with ThreadPoolExecutor(max_workers=10) as executor:
        #     future_to_url = {
        #         executor.submit(self.get_location_details, url): url
        #         for url in urls_to_process
        #     }
        #
        #     for future in as_completed(future_to_url):
        #         locations = future.result()
        #         all_locations.extend(locations)
        #
        # print(f"\nScraping completed in {time.time() - start_time:.2f} seconds")
        # print(f"Total {self.restaurant_name} locations found: {len(all_locations)}")

        return all_locations


if __name__ == "__main__":
    scraper = PopeyesScraper()
    scraper.scrape()

