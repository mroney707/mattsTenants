import json
from datetime import datetime
import os
from typing import List, Dict, Set
from dataclasses import dataclass

@dataclass
class LocationChange:
    tenant: str
    removed_locations: List[Dict]
    date: str

class LocationTracker:
    def __init__(self, data_dir: str = "historical_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def _get_historical_file(self, tenant: str) -> str:
        return os.path.join(self.data_dir, f"{tenant}_locations.json")
    
    def _get_location_key(self, location: Dict) -> str:
        """Create unique key for location based on address components"""
        return f"{location['street']}|{location['city']}|{location['state']}|{location['postal_code']}"
    
    def compare_locations(self, tenant: str, current_locations: List[Dict]) -> LocationChange:
        """Compare current locations with historical data and return changes"""
        historical_file = self._get_historical_file(tenant)
        
        # Get historical locations
        if os.path.exists(historical_file):
            with open(historical_file, 'r') as f:
                historical_locations = json.load(f)
        else:
            historical_locations = []
        
        # Convert locations to sets for comparison
        historical_keys = {self._get_location_key(loc) for loc in historical_locations}
        current_keys = {self._get_location_key(loc) for loc in current_locations}
        
        # Find removed locations
        removed_keys = historical_keys - current_keys
        removed_locations = [
            loc for loc in historical_locations 
            if self._get_location_key(loc) in removed_keys
        ]
        
        return LocationChange(
            tenant=tenant,
            removed_locations=removed_locations,
            date=datetime.now().strftime("%Y-%m-%d")
        )
    
    def update_historical_data(self, tenant: str, current_locations: List[Dict]):
        """Update historical data with current locations"""
        historical_file = self._get_historical_file(tenant)
        with open(historical_file, 'w') as f:
            json.dump(current_locations, f, indent=2) 