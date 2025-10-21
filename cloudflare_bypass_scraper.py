"""
Indeed Scraper with Multiple Cloudflare Bypass Methods

Solutions:
1. Use cloudscraper (bypasses Cloudflare automatically)
2. Use Playwright (better than Selenium for stealth)
3. Manual cookie extraction

Install:
pip install cloudscraper playwright beautifulsoup4
python -m playwright install chromium
"""

import json
import csv
import time
import random
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ============================================================================
# METHOD 1: CloudScraper (Easiest - bypasses Cloudflare automatically)
# ============================================================================

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except:
    CLOUDSCRAPER_AVAILABLE = False
    print("⚠️  cloudscraper not installed. Install with: pip install cloudscraper")


class IndeedCloudScraperMethod:
    """Uses cloudscraper to bypass Cloudflare"""
    
    def __init__(self):
        if not CLOUDSCRAPER_AVAILABLE:
            raise ImportError("cloudscraper is required")
        
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
    
    def scrape_jobs(self, url, max_pages=5):
        """Scrape jobs using cloudscraper"""
        all_jobs = []
        
        print(f"🔍 Using CloudScraper method...")
        print(f"📍 URL: {url}\n")
        
        for page in range(max_pages):
            page_url = url if page == 0 else f"{url}&start={page * 10}"
            
            print(f"📄 Page {page + 1}/{max_pages}")
            
            try:
                # CloudScraper automatically bypasses Cloudflare
                response = self.scraper.get(page_url, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Check if we got through Cloudflare
                    if 'cloudflare' in response.text.lower() and 'verification' in response.text.lower():
                        print("  ❌ Cloudflare still blocking")
                        break
                    
                    # Extract jobs
                    jobs = self.extract_jobs_from_html(soup)
                    
                    if jobs:
                        print(f"  ✅ Found {len(jobs)} jobs")
                        all_jobs.extend(jobs)
                    else:
                        print("  ⚠️  No jobs found")
                        break
                else:
                    print(f"  ❌ Status: {response.status_code}")
                    break
                
                # Delay
                if page < max_pages - 1:
                    time.sleep(random.uniform(3, 6))
            
            except Exception as e:
                print(f"  ❌ Error: {e}")
                break
        
        return all_jobs
    
    def extract_jobs_from_html(self, soup):
        """Extract jobs from HTML"""
        jobs = []
        
        # Find job cards
        job_cards = (
            soup.find_all('div', class_='job_seen_beacon') or
            soup.find_all('div', attrs={'data-jk': True}) or
            soup.find_all('td', class_='resultContent')
        )
        
        for card in job_cards:
            job_data = self.extract_job_data(card)
            if job_data['title']:
                jobs.append(job_data)
        
        return jobs
    
    def extract_job_data(self, card):
        """Extract data from job card"""
        job = {
            'title': None, 'company': None, 'location': None,
            'salary': None, 'description': None, 'posted_date': None,
            'apply_url': None, 'job_id': None, 'source': 'indeed_cr'
        }
        
        # Job ID
        job['job_id'] = card.get('data-jk')
        
        # Title
        title_elem = card.find('h2', class_='jobTitle') or card.find('a', class_='jcs-JobTitle')
        if title_elem:
            job['title'] = title_elem.get_text(strip=True)
            link = title_elem.find('a') if title_elem.name != 'a' else title_elem
            if link and link.get('href'):
                job['apply_url'] = f"https://cr.indeed.com{link['href']}"
        
        # Company
        company_elem = card.find('span', {'data-testid': 'company-name'})
        if company_elem:
            job['company'] = company_elem.get_text(strip=True)
        
        # Location
        location_elem = card.find('div', {'data-testid': 'text-location'})
        if location_elem:
            job['location'] = location_elem.get_text(strip=True)
        
        # Salary
        salary_elem = card.find('div', class_='salary-snippet')
        if salary_elem:
            job['salary'] = salary_elem.get_text(strip=True)
        
        # Description
        desc_elem = card.find('div', class_='job-snippet')
        if desc_elem:
            job['description'] = desc_elem.get_text(strip=True)
        
        # Date
        date_elem = card.find('span', class_='date')
        if date_elem:
            job['posted_date'] = date_elem.get_text(strip=True)
        
        return job


# ============================================================================
# METHOD 2: Playwright (Most Reliable - Better than Selenium)
# ============================================================================

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  playwright not installed. Install with: pip install playwright")


class IndeedPlaywrightMethod:
    """Uses Playwright to bypass Cloudflare"""
    
    def scrape_jobs(self, url, max_pages=5, headless=False):
        """Scrape using Playwright"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("playwright is required")
        
        all_jobs = []
        
        print(f"🔍 Using Playwright method...")
        print(f"📍 URL: {url}\n")
        
        with sync_playwright() as p:
            # Launch browser with stealth settings
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            
            # Create context with realistic settings
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='es-CR',
                timezone_id='America/Costa_Rica'
            )
            
            # Remove automation indicators
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['es-CR', 'es', 'en']});
            """)
            
            page = context.new_page()
            
            for page_num in range(max_pages):
                page_url = url if page_num == 0 else f"{url}&start={page_num * 10}"
                
                print(f"📄 Page {page_num + 1}/{max_pages}")
                
                try:
                    # Navigate with human-like behavior
                    page.goto(page_url, wait_until='domcontentloaded', timeout=60000)
                    
                    # Wait for Cloudflare to load
                    time.sleep(random.uniform(5, 8))
                    
                    # Check if Cloudflare challenge is present
                    content = page.content()
                    if 'cloudflare' in content.lower() and 'verification' in content.lower():
                        print("  ⏳ Waiting for Cloudflare challenge...")
                        
                        # Wait up to 30 seconds for Cloudflare to complete
                        for i in range(30):
                            time.sleep(1)
                            content = page.content()
                            if 'cloudflare' not in content.lower() or 'verification' not in content.lower():
                                print("  ✅ Cloudflare passed!")
                                break
                        else:
                            print("  ❌ Cloudflare challenge not completed")
                            page.screenshot(path=f'cloudflare_challenge_{page_num + 1}.png')
                            continue
                    
                    # Scroll to load content
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
                    time.sleep(2)
                    
                    # Extract jobs
                    soup = BeautifulSoup(page.content(), 'html.parser')
                    jobs = self.extract_jobs_from_html(soup)
                    
                    if jobs:
                        print(f"  ✅ Found {len(jobs)} jobs")
                        all_jobs.extend(jobs)
                    else:
                        print("  ⚠️  No jobs found")
                        page.screenshot(path=f'no_jobs_page_{page_num + 1}.png')
                        break
                    
                    # Delay
                    if page_num < max_pages - 1:
                        time.sleep(random.uniform(4, 7))
                
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    break
            
            browser.close()
        
        return all_jobs
    
    def extract_jobs_from_html(self, soup):
        """Extract jobs from HTML"""
        jobs = []
        
        job_cards = (
            soup.find_all('div', class_='job_seen_beacon') or
            soup.find_all('div', attrs={'data-jk': True}) or
            soup.find_all('td', class_='resultContent')
        )
        
        for card in job_cards:
            job = {
                'title': None, 'company': None, 'location': None,
                'salary': None, 'description': None, 'apply_url': None,
                'job_id': card.get('data-jk'), 'source': 'indeed_cr'
            }
            
            # Extract fields
            title_elem = card.find('h2', class_='jobTitle')
            if title_elem:
                job['title'] = title_elem.get_text(strip=True)
            
            company_elem = card.find('span', {'data-testid': 'company-name'})
            if company_elem:
                job['company'] = company_elem.get_text(strip=True)
            
            location_elem = card.find('div', {'data-testid': 'text-location'})
            if location_elem:
                job['location'] = location_elem.get_text(strip=True)
            
            if job['title']:
                jobs.append(job)
        
        return jobs


# ============================================================================
# Utility Functions
# ============================================================================

def save_to_json(jobs, filename='indeed_jobs.json'):
    """Save jobs to JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved to {filename}")


def save_to_csv(jobs, filename='indeed_jobs.csv'):
    """Save jobs to CSV"""
    if not jobs:
        return
    
    keys = jobs[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(jobs)
    print(f"💾 Saved to {filename}")


# ============================================================================
# Main Function
# ============================================================================

def main():
    print("="*70)
    print("INDEED COSTA RICA - CLOUDFLARE BYPASS SCRAPER")
    print("="*70)
    print()
    
    url = "https://cr.indeed.com/jobs?q=&l=costa+rica&from=searchOnHP"
    
    # Try Method 1: CloudScraper (Fastest)
    if CLOUDSCRAPER_AVAILABLE:
        print("🔧 Method 1: CloudScraper (Automatic Bypass)")
        print("-"*70)
        try:
            scraper = IndeedCloudScraperMethod()
            jobs = scraper.scrape_jobs(url, max_pages=3)
            
            if jobs:
                print(f"\n✅ Success! Scraped {len(jobs)} jobs with CloudScraper\n")
                save_to_json(jobs, 'indeed_jobs_cloudscraper.json')
                save_to_csv(jobs, 'indeed_jobs_cloudscraper.csv')
                return
            else:
                print("\n⚠️  CloudScraper didn't find jobs. Trying Playwright...\n")
        except Exception as e:
            print(f"\n❌ CloudScraper failed: {e}\n")
    
    # Try Method 2: Playwright (Most Reliable)
    if PLAYWRIGHT_AVAILABLE:
        print("🔧 Method 2: Playwright (Stealth Browser)")
        print("-"*70)
        try:
            scraper = IndeedPlaywrightMethod()
            jobs = scraper.scrape_jobs(url, max_pages=3, headless=False)
            
            if jobs:
                print(f"\n✅ Success! Scraped {len(jobs)} jobs with Playwright\n")
                save_to_json(jobs, 'indeed_jobs_playwright.json')
                save_to_csv(jobs, 'indeed_jobs_playwright.csv')
                return
            else:
                print("\n⚠️  Playwright didn't find jobs\n")
        except Exception as e:
            print(f"\n❌ Playwright failed: {e}\n")
    
    # If all methods fail
    print("❌ All methods failed. Solutions:")
    print("   1. Install cloudscraper: pip install cloudscraper")
    print("   2. Install playwright: pip install playwright")
    print("   3. Run: python -m playwright install chromium")
    print("   4. Use a VPN to Costa Rica")
    print("   5. Use residential proxies")
    print("   6. Try Indeed API/RSS feeds instead")


if __name__ == "__main__":
    main()