from abc import ABC, abstractmethod
from typing import List, Dict

class RestaurantScraper(ABC):
    @abstractmethod
    def scrape(self) -> List[Dict[str, str]]:
        """
        Scrape restaurant locations and return a list of location dictionaries.
        Each location should have 'street', 'city', 'state', and 'postal_code'.
        """
        pass

    @property
    @abstractmethod
    def restaurant_name(self) -> str:
        """Return the name of the restaurant chain"""
        pass 