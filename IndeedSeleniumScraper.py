"""
Improved Indeed Scraper - Handles dynamic page structure
Analyzes debug HTML to find correct selectors
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
import json
import csv
import time
import random
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

class ImprovedIndeedScraper:
    def __init__(self, headless=False):
        """Initialize with better options"""
        options = uc.ChromeOptions()
        
        if headless:
            options.add_argument('--headless=new')
        
        # Better stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--lang=es-419,es')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-notifications')
        
        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        print("🚀 Initializing Chrome driver...")
        try:
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.set_page_load_timeout(30)
            self.wait = WebDriverWait(self.driver, 15)
            print("✅ Driver ready!\n")
        except Exception as e:
            print(f"❌ Error initializing driver: {e}")
            raise
    
    def parse_date(self, date_str):
        """Parse date strings"""
        if not date_str:
            return None
        
        date_str = date_str.lower().strip()
        
        # Today
        if any(word in date_str for word in ['hoy', 'today', 'just posted']):
            return datetime.now().strftime('%Y-%m-%d')
        
        # X days/hours ago
        if 'hace' in date_str or 'ago' in date_str:
            numbers = re.findall(r'\d+', date_str)
            if numbers:
                num = int(numbers[0])
                if 'hora' in date_str or 'hour' in date_str:
                    return datetime.now().strftime('%Y-%m-%d')
                else:
                    return (datetime.now() - timedelta(days=num)).strftime('%Y-%m-%d')
        
        # Specific dates
        months = {
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12,
            'jan': 1, 'apr': 4, 'aug': 8, 'dec': 12
        }
        
        for m, num in months.items():
            if m in date_str:
                parts = re.findall(r'\d+', date_str)
                if parts:
                    day = int(parts[0])
                    year = int(parts[1]) if len(parts) > 1 else datetime.now().year
                    return f"{year}-{num:02d}-{day:02d}"
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def extract_salary(self, text):
        """Extract salary"""
        if not text:
            return {'salary_type': None, 'salary': None, 'max_salary': None}
        
        text_lower = text.lower()
        result = {'salary_type': 'monthly', 'salary': None, 'max_salary': None}
        
        if any(w in text_lower for w in ['hora', 'hour', '/hr']):
            result['salary_type'] = 'hourly'
        elif any(w in text_lower for w in ['año', 'year', 'anual', '/yr']):
            result['salary_type'] = 'yearly'
        
        numbers = re.findall(r'[\d,]+(?:\.\d{2})?', text)
        if numbers:
            nums = [float(n.replace(',', '')) for n in numbers]
            result['salary'] = nums[0]
            if len(nums) > 1:
                result['max_salary'] = nums[1]
        
        return result
    
    def wait_and_find_jobs(self):
        """Wait for page to load and find job elements using multiple strategies"""
        print("  🔍 Analyzing page structure...")
        
        # Wait for page to fully load
        time.sleep(3)
        
        # Try to scroll first
        try:
            self.driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(1)
        except:
            pass
        
        # Get page source for analysis
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # Try multiple selectors
        job_selectors = [
            ('CSS', 'div.job_seen_beacon'),
            ('CSS', 'div[data-jk]'),
            ('CSS', 'td.resultContent'),
            ('CSS', 'div.jobsearch-SerpJobCard'),
            ('CSS', 'li[data-jk]'),
            ('CSS', 'div.slider_container div.slider_item'),
            ('CSS', 'table.jobCard_mainContent'),
            ('CSS', 'div[class*="job"]'),
            ('XPATH', '//div[contains(@class, "job")]'),
            ('XPATH', '//td[contains(@class, "resultContent")]'),
        ]
        
        jobs_found = []
        
        for selector_type, selector in job_selectors:
            try:
                if selector_type == 'CSS':
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                else:
                    elements = self.driver.find_elements(By.XPATH, selector)
                
                if elements and len(elements) > 3:  # Found valid job list
                    print(f"  ✅ Found {len(elements)} jobs using: {selector}")
                    jobs_found = elements
                    break
            except:
                continue
        
        # If no jobs found with selenium, try parsing HTML directly
        if not jobs_found:
            print("  🔧 Trying HTML parsing fallback...")
            
            # Look for job cards in HTML
            job_cards = (
                soup.find_all('div', class_='job_seen_beacon') or
                soup.find_all('div', attrs={'data-jk': True}) or
                soup.find_all('td', class_='resultContent') or
                soup.find_all('div', class_=re.compile(r'jobsearch.*Card')) or
                soup.find_all('li', attrs={'data-jk': True})
            )
            
            if job_cards:
                print(f"  ✅ Found {len(job_cards)} jobs in HTML")
                return job_cards, 'html'
        
        if jobs_found:
            return jobs_found, 'selenium'
        
        # Last resort - save debug info
        print("  ❌ Could not find jobs. Analyzing page...")
        
        # Check if we hit a redirect or blocking
        current_url = self.driver.current_url
        if 'google.com/sorry' in current_url or 'captcha' in current_url.lower():
            print("  ⚠️  CAPTCHA detected!")
            return None, None
        
        # Look for any links that might be jobs
        all_links = soup.find_all('a', href=True)
        job_links = [a for a in all_links if '/viewjob' in a.get('href', '') or 'jk=' in a.get('href', '')]
        
        if job_links:
            print(f"  📎 Found {len(job_links)} job links in page")
            return job_links, 'links'
        
        return None, None
    
    def extract_from_html(self, soup_element):
        """Extract job data from BeautifulSoup element"""
        job_data = self.get_empty_job_dict()
        
        try:
            # Job ID
            job_data['job_id'] = soup_element.get('data-jk') or soup_element.get('id')
            
            # Title
            title_elem = (
                soup_element.find('h2', class_='jobTitle') or
                soup_element.find('a', class_=re.compile(r'jcs.*JobTitle')) or
                soup_element.find('span', id=re.compile(r'jobTitle'))
            )
            if title_elem:
                job_data['title'] = title_elem.get_text(strip=True)
                
                # URL
                link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if link and link.get('href'):
                    href = link['href']
                    if href.startswith('http'):
                        job_data['apply_url'] = href
                    else:
                        job_data['apply_url'] = f"https://cr.indeed.com{href}"
            
            # Company
            company_elem = (
                soup_element.find('span', attrs={'data-testid': 'company-name'}) or
                soup_element.find('span', class_='companyName')
            )
            if company_elem:
                job_data['company'] = company_elem.get_text(strip=True)
            
            # Rating
            rating_elem = soup_element.find('span', class_='ratingNumber')
            if rating_elem:
                try:
                    job_data['company_rating'] = float(rating_elem.get_text(strip=True))
                except:
                    pass
            
            # Location
            location_elem = (
                soup_element.find('div', attrs={'data-testid': 'text-location'}) or
                soup_element.find('div', class_='companyLocation')
            )
            if location_elem:
                loc_text = location_elem.get_text(strip=True)
                job_data['location'] = loc_text
                job_data['address'] = loc_text
            
            # Salary
            salary_elem = soup_element.find('div', class_=re.compile(r'salary'))
            if salary_elem:
                salary_info = self.extract_salary(salary_elem.get_text())
                job_data.update(salary_info)
            
            # Description snippet
            snippet_elem = soup_element.find('div', class_='job-snippet')
            if snippet_elem:
                job_data['description'] = snippet_elem.get_text(strip=True)
            
            # Date
            date_elem = soup_element.find('span', class_='date')
            if date_elem:
                job_data['posted_date'] = self.parse_date(date_elem.get_text())
            
            # Tags
            html_text = str(soup_element).lower()
            if 'patrocinado' in html_text or 'sponsored' in html_text:
                job_data['featured'] = True
                job_data['tag'].append('sponsored')
            
            if 'urge contratar' in html_text or 'urgently' in html_text:
                job_data['urgent'] = True
                job_data['tag'].append('urgent')
            
        except Exception as e:
            print(f"    ⚠️  Extraction error: {e}")
        
        return job_data
    
    def extract_from_selenium(self, element):
        """Extract from Selenium element"""
        job_data = self.get_empty_job_dict()
        
        try:
            # Get the HTML and parse it
            html = element.get_attribute('outerHTML')
            soup = BeautifulSoup(html, 'html.parser')
            return self.extract_from_html(soup)
        except StaleElementReferenceException:
            print("    ⚠️  Stale element")
            return job_data
        except Exception as e:
            print(f"    ⚠️  Error: {e}")
            return job_data
    
    def get_empty_job_dict(self):
        """Return empty job data structure"""
        return {
            'featured_image': None, 'title': None, 'featured': False,
            'filled': False, 'urgent': False, 'description': None,
            'category': None, 'type': None, 'tag': [],
            'expiry_date': None, 'gender': None, 'apply_type': 'external',
            'apply_url': None, 'apply_email': None, 'salary_type': None,
            'salary': None, 'max_salary': None, 'experience': None,
            'career_level': None, 'qualification': None, 'video_url': None,
            'photos': [], 'application_deadline_date': None, 'address': None,
            'location': None, 'map_location': None, 'company': None,
            'company_rating': None, 'posted_date': None, 'job_id': None,
            'source': 'indeed_cr'
        }
    
    def scrape_jobs(self, search_url, max_pages=5, max_jobs=None):
        """Main scraping function"""
        all_jobs = []
        
        print(f"🔍 Target: {search_url}\n")
        
        for page in range(max_pages):
            if page == 0:
                url = search_url
            else:
                separator = '&' if '?' in search_url else '?'
                url = f"{search_url}{separator}start={page * 10}"
            
            print(f"📄 Page {page + 1}/{max_pages}")
            
            try:
                # Load page
                self.driver.get(url)
                time.sleep(random.uniform(3, 5))
                
                # Find jobs
                job_elements, element_type = self.wait_and_find_jobs()
                
                if not job_elements:
                    print("  ⚠️  No jobs found. Saving debug files...")
                    self.driver.save_screenshot(f'debug_page{page+1}.png')
                    with open(f'debug_page{page+1}.html', 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    print(f"  💾 Check debug_page{page+1}.png and debug_page{page+1}.html")
                    break
                
                # Extract jobs based on element type
                print(f"  📊 Extracting from {len(job_elements)} elements...\n")
                
                for idx, element in enumerate(job_elements, 1):
                    try:
                        if element_type == 'html':
                            job_data = self.extract_from_html(element)
                        elif element_type == 'selenium':
                            job_data = self.extract_from_selenium(element)
                        elif element_type == 'links':
                            # Extract from link element
                            job_data = self.get_empty_job_dict()
                            job_data['title'] = element.get_text(strip=True)
                            href = element.get('href', '')
                            if href.startswith('http'):
                                job_data['apply_url'] = href
                            else:
                                job_data['apply_url'] = f"https://cr.indeed.com{href}"
                        else:
                            continue
                        
                        if job_data['title']:
                            company = job_data['company'] or 'Unknown'
                            print(f"  {idx:2d}. {job_data['title'][:50]:50s} @ {company[:20]}")
                            all_jobs.append(job_data)
                            
                            if max_jobs and len(all_jobs) >= max_jobs:
                                print(f"\n✅ Reached {max_jobs} jobs")
                                return all_jobs
                    
                    except Exception as e:
                        print(f"  ❌ Job {idx} error: {e}")
                        continue
                
                print()
                
                # Check if there's a next page
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, 'a[data-testid="pagination-page-next"]')
                    if not next_button.is_enabled():
                        print("  ℹ️  No more pages")
                        break
                except:
                    pass
                
                # Delay
                if page < max_pages - 1:
                    delay = random.uniform(4, 7)
                    print(f"  ⏳ Waiting {delay:.1f}s...\n")
                    time.sleep(delay)
            
            except Exception as e:
                print(f"  ❌ Page error: {e}")
                break
        
        return all_jobs
    
    def close(self):
        """Close browser safely"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
    
    def save_json(self, jobs, filename='indeed_jobs.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print(f"💾 {filename}")
    
    def save_csv(self, jobs, filename='indeed_jobs.csv'):
        if not jobs:
            return
        keys = jobs[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for job in jobs:
                row = {k: ', '.join(map(str, v)) if isinstance(v, list) else v for k, v in job.items()}
                writer.writerow(row)
        print(f"💾 {filename}")


def main():
    print("="*70)
    print("INDEED COSTA RICA - IMPROVED SCRAPER")
    print("="*70)
    print()
    
    url = "https://cr.indeed.com/jobs?q=&l=costa+rica&from=searchOnHP"
    
    scraper = None
    try:
        scraper = ImprovedIndeedScraper(headless=False)
        jobs = scraper.scrape_jobs(url, max_pages=5, max_jobs=None)
        
        if jobs:
            print(f"\n{'='*70}")
            print(f"✅ Scraped {len(jobs)} jobs!")
            print(f"{'='*70}\n")
            
            scraper.save_json(jobs, 'indeed_cr_jobs.json')
            scraper.save_csv(jobs, 'indeed_cr_jobs.csv')
            
            # Sample
            sample = jobs[0]
            print("📋 SAMPLE:")
            print(f"  Title: {sample['title']}")
            print(f"  Company: {sample['company']}")
            print(f"  Location: {sample['location']}")
            print(f"  URL: {sample['apply_url']}")
        else:
            print("\n❌ No jobs found. Check debug files.")
    
    except KeyboardInterrupt:
        print("\n⚠️  Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper:
            scraper.close()
        print("\n✅ Done!")


if __name__ == "__main__":
    main()