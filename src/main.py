import json
from typing import Dict, List
from src.scrapers.base_scraper import RestaurantScraper
from src.location_tracker import LocationTracker
from src.scrapers.popeyes_scraper import PopeyesScraper
from src.scrapers.wendys_scraper import WendysScraper
from src.scrapers.dennys_scraper import DennysScraper
from src.scrapers.arbys_scraper import ArbysScraper
from src.scrapers.pollo_tropical_scraper import PolloTropicalScraper
from src.scrapers.bk_scraper import BKScraper
# Import other scrapers as you create them

class RestaurantScraperManager:
    def __init__(self):
        self.scrapers = [
            PopeyesScraper(),
            WendysScraper(),
            DennysScraper(),
            ArbysScraper(),
            PolloTropicalScraper(),
            BKScraper()
        ]
        self.tracker = LocationTracker()

    def generate_dashboard(self):
        dashboard_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Restaurant Closures Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                .restaurant-section { margin-bottom: 30px; }
                .location-card { 
                    background-color: #fff;
                    border: 1px solid #ddd;
                    padding: 15px;
                    margin-bottom: 10px;
                    border-radius: 5px;
                }
                .no-locations { color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Restaurant Closures Dashboard</h1>
        """

        try:
            with open('removed_locations.json', 'r') as f:
                data = json.load(f)
                
            dashboard_html += f"<p>Last Updated: {data['date']}</p></div>"
            
            for restaurant, locations in data['locations'].items():
                dashboard_html += f"""
                    <div class="restaurant-section">
                        <h2>{restaurant.title()}</h2>
                """
                
                if locations:
                    for location in locations:
                        dashboard_html += f"""
                            <div class="location-card">
                                <p>{location['street']}<br>
                                {location['city']}, {location['state']} {location['postal_code']}</p>
                            </div>
                        """
                else:
                    dashboard_html += '<p class="no-locations">No removed locations</p>'
                
                dashboard_html += "</div>"
            
        except FileNotFoundError:
            dashboard_html += """
                    <p>No removal data available yet.</p>
                </div>
            """

        dashboard_html += """
            </div>
        </body>
        </html>
        """

        with open('dashboard.html', 'w') as f:
            f.write(dashboard_html)

    def send_email_report(self, removed_locations_data: Dict):
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from datetime import datetime

        # Email configuration
        sender_email = "mhausman97@gmail.com"  # Replace with your Gmail
        receiver_email = "mhausman97@gmail.com"  # Replace with recipient's email
        password = "ncyj qgrp cksz dlza"  # Replace with Gmail App Password

        # Create message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = f"Restaurant Closures Report - {datetime.now().strftime('%Y-%m-%d')}"

        # Create email body
        email_body = "<h2>Restaurant Closures Report</h2>"
        
        if removed_locations_data["date"]:
            email_body += f"<p>Last Updated: {removed_locations_data['date']}</p>"
            
            for restaurant, locations in removed_locations_data["locations"].items():
                email_body += f"<h3>{restaurant.title()}</h3>"
                
                if locations:
                    for location in locations:
                        email_body += f"""
                            <div style='margin-bottom: 10px; padding: 10px; border: 1px solid #ddd;'>
                                <p>{location['street']}<br>
                                {location['city']}, {location['state']} {location['postal_code']}</p>
                            </div>
                        """
                else:
                    email_body += '<p>No removed locations</p>'
        else:
            email_body += "<p>No locations were removed.</p>"

        message.attach(MIMEText(email_body, "html"))

        # Send email
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.send_message(message)
            print("Email report sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {str(e)}")

    def run_all_scrapers(self) -> Dict[str, List[Dict[str, str]]]:
        all_results = {}
        removed_locations_data = {
            "date": None,
            "locations": {}
        }
        
        for scraper in self.scrapers:
            print(f"\nScraping {scraper.restaurant_name.title()} locations...")
            locations = scraper.scrape()
            
            # Compare with historical data
            changes = self.tracker.compare_locations(scraper.restaurant_name, locations)
            
            # Output changes and store removed locations
            if changes.removed_locations:
                print(f"\nRemoved {scraper.restaurant_name.title()} locations as of {changes.date}:")
                removed_locations_data["date"] = changes.date
                removed_locations_data["locations"][scraper.restaurant_name] = changes.removed_locations
                for location in changes.removed_locations:
                    print(f"- {location['street']}, {location['city']}, {location['state']} {location['postal_code']}")
            else:
                print(f"\nNo {scraper.restaurant_name.title()} locations were removed")
            
            # Update historical data
            self.tracker.update_historical_data(scraper.restaurant_name, locations)
            
            # Add to results
            all_results[scraper.restaurant_name] = locations
        
        # Replace dashboard generation with email sending
        if any(removed_locations_data["locations"]):
            with open('removed_locations.json', 'w') as f:
                json.dump(removed_locations_data, f, indent=2)
            self.send_email_report(removed_locations_data)
        
        return all_results

    def save_results(self, results: Dict[str, List[Dict[str, str]]], filename: str = "all_locations.json"):
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

if __name__ == "__main__":
    manager = RestaurantScraperManager()
    results = manager.run_all_scrapers()
    manager.save_results(results)
