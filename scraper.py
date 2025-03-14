from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import logging
import csv
import os
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Login credentials and offset choose here
username = ""
password = ""
offset = 500
num_results = 500


class PennAlumScraper:
    def __init__(self, offset, num_results):
        self.driver = webdriver.Chrome()
        self.base_url = "https://mypenn.upenn.edu/s/login"
        self.offset = offset
        self.num_results = num_results
        self.directory_part_two = "&sort=%40sflastname%20ascending&numberOfResults=100&f:@sfprimary_industry__c=[Management%20Consulting]"
        # Create output directory if it doesn't exist
        self.output_dir = "output"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
    def login(self, username, password):
        try:
            self.driver.get(self.base_url)

            # Wait for and find login button - using multiple attributes to be more specific
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[value="0LE6g000000k9mGGAQ"][aria-label="PennKey Login"]'))
            )
            login_button.click()
            
            # Wait for the login form to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "loginform"))
            )
            
            # Wait for and find username field
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.send_keys(username)
            
            # Find password field and submit button
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_field.send_keys(password)
            
            # Find and click submit button
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="_eventId_proceed"]'))
            )
            submit_button.click()
            
            # Wait for user to approve on duomobile
            time.sleep(15)
            
            return True
            
        except TimeoutException as e:
            logger.error(f"Timeout during login: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    def get_directory_url(self, current_offset):
        directory_part_one = f"https://mypenn.upenn.edu/s/directory#first={current_offset}"
        return directory_part_one + self.directory_part_two

    def scrape_all_profiles(self):
        all_profiles = []
        num_batches = (self.num_results + 99) // 100  # Round up to nearest 100
        current_offset = self.offset

        with tqdm(total=self.num_results, desc="Total Progress") as pbar:
            for batch in range(num_batches):
                # Update directory URL for current batch
                self.directory_url = self.get_directory_url(current_offset)
                
                # Scrape current batch
                batch_profiles = self.scrape_profiles()
                all_profiles.extend(batch_profiles)
                
                # Update progress bar
                pbar.update(len(batch_profiles))
                
                # Save batch to CSV
                self.save_to_csv(batch_profiles, current_offset)
                
                # Increment offset for next batch
                current_offset += 100
                
                # Break if we've reached desired number of results
                if len(all_profiles) >= self.num_results:
                    break

        return all_profiles

    def scrape_profiles(self):
        try:
            profiles = []
            
            print("Performing warm-up navigation...")
            self.driver.get(self.directory_url)
            
            # Do a dummy profile click to warm up the navigation
            try:
                # Wait for any profile card and click it
                first_card = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".CoveoSalesforceResultLink"))
                )
                first_card.click()
                print("Clicked warm-up profile")
                
                # Wait for the page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-item-id="06cbc91a-b7eb-45c4-b2e7-41cde0bfd89a"]'))
                )
                print("Warm-up profile page loaded")
                
                # Navigate back to directory
                print("Navigating back to directory for actual scraping...")
                self.driver.get(self.directory_url)
                
                # Now wait for the container to be ready
                print("Waiting for directory to fully reload...")
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".coveo-result-list-container"))
                )
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".CoveoResult"))
                )
                # Wait for any animations or dynamic loading to complete
                WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".CoveoSalesforceResultLink"))
                )
                print("Directory page ready for scraping")
                
            except Exception as e:
                print(f"Warm-up navigation failed: {str(e)}")
                # Continue anyway as the main scraping might still work
            
            # Now proceed with the actual scraping
            # Find all profile cards
            profile_cards = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".CoveoResult"))
            )
            logger.info(f"Found {len(profile_cards)} profile cards")
            
            # Instead of storing cards, we'll process them by index
            for i in range(min(100, len(profile_cards))):
                try:
                    print(f"\nProcessing profile {i + 1}/{min(100, len(profile_cards))}")
                    
                    # Find the current card fresh each time
                    print(f"Finding card {i + 1}...")
                    current_card = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, f".CoveoResult:nth-child({i + 1})"))
                    )
                    
                    # Find and get the name link within the current card
                    print("Finding name link...")
                    name_link = WebDriverWait(current_card, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".CoveoSalesforceResultLink"))
                    )
                    name = name_link.text
                    print(f"Found profile: {name}")
                    
                    # Click using JavaScript to avoid stale element issues
                    print("Clicking on profile link...")
                    self.driver.execute_script("arguments[0].click();", name_link)
                    
                    # Wait for profile page to load
                    print("Waiting for profile page to load...")
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-item-id="06cbc91a-b7eb-45c4-b2e7-41cde0bfd89a"]'))
                    )
                    
                    # Extract email
                    print("Extracting email...")
                    email = self.extract_email_from_profile(self.driver)
                    print(f"Extracted email: {email}")
                    
                    profiles.append({
                        'name': name,
                        'email': email
                    })
                    
                    # Navigate back
                    print("Navigating back to directory...")
                    self.driver.get(self.directory_url)
                    
                    # Wait for both the container AND the first result to be fully loaded
                    print("Waiting for directory to fully reload...")
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".coveo-result-list-container"))
                    )
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".CoveoResult"))
                    )
                    # Wait for any animations or dynamic loading to complete
                    WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".CoveoSalesforceResultLink"))
                    )
                    print("Successfully processed profile")
                    
                except Exception as e:
                    print(f"ERROR processing profile {i}: {str(e)}")
                    print(f"Error type: {type(e).__name__}")
                    continue
            
            print(f"\nSuccessfully scraped {len(profiles)} profiles")
            return profiles
            
        except Exception as e:
            print(f"FATAL ERROR scraping profiles: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            return []
    
    def extract_email_from_profile(self, profile_page):
        try:
            print("Looking for outer div...")
            # First find the outer div with the specific data-item ID
            outer_div = WebDriverWait(profile_page, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-item-id="06cbc91a-b7eb-45c4-b2e7-41cde0bfd89a"]'))
            )
            
            print("Looking for inner div...")
            # Find the inner div with the specific data-item ID (Email Addresses section)
            inner_div = WebDriverWait(outer_div, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-item-id="3353720f-5938-46b2-a62d-d377b3a97f6c"]'))
            )
            
            # Check for "No email addresses provided" using the specific span with lwc attribute
            try:
                no_email_element = WebDriverWait(inner_div, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                    'span[lwc-4nfn2rc40ch][part="formatted-rich-text"]'))
                )
                print(no_email_element)
                if no_email_element.text.strip() == "No email addresses provided.":
                    print("No email addresses provided message found")
                    return None
            except Exception as e:
                print(f"Error checking for no email message: {str(e)}")
            
            print("Looking for email links...")
            # Wait for and find all email links
            WebDriverWait(inner_div, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="mailto:"]'))
            )
            email_links = inner_div.find_elements(By.CSS_SELECTOR, 'a[href^="mailto:"]')
            
            # Extract emails from the links
            emails = []
            for link in email_links:
                email = link.get_attribute('href').replace('mailto:', '')
                if email not in emails:  # Avoid duplicates
                    emails.append(email)
            
            print(f"Found {len(emails)} unique email links")
            
            # Return the first email found
            return emails[0] if emails else None
            
        except Exception as e:
            print(f"ERROR extracting email: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            return None
    
    def close(self):
        self.driver.quit()

    def save_to_csv(self, profiles, current_offset):
        filename = os.path.join(self.output_dir, f"penn_alumni_{current_offset+1}-{current_offset+100}.csv")
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'email']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(profiles)
                
            logger.info(f"Successfully saved {len(profiles)} profiles to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
            return None

def main():    
    scraper = PennAlumScraper(offset, num_results)
    
    if scraper.login(username, password):
        scraper.scrape_all_profiles()
    
    scraper.close()

if __name__ == "__main__":
    main()
