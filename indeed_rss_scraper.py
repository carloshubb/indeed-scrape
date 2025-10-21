"""
FINAL WORKING SOLUTION
═══════════════════════════════════════════════════════════════
Opens browser, YOU solve CAPTCHA manually, then scrapes automatically
This is the most reliable method for Indeed Costa Rica
═══════════════════════════════════════════════════════════════

Install:
pip install selenium webdriver-manager beautifulsoup4
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import csv
import time
import re

class IndeedManualCAPTCHAScraper:
    def __init__(self):
        """Initialize Chrome with normal settings"""
        options = Options()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        print("🚀 Starting Chrome browser...")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        # Remove automation flags
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            '''
        })
        
        print("✅ Browser ready!\n")
    
    def scrape_with_manual_captcha(self, url, max_pages=5):
        """
        Opens browser, waits for you to solve CAPTCHA, then scrapes
        """
        all_jobs = []
        
        print("="*70)
        print("MANUAL CAPTCHA SOLVER")
        print("="*70)
        print(f"📍 URL: {url}\n")
        
        # Load first page
        print("🌐 Loading Indeed...")
        self.driver.get(url)
        
        # Check for Cloudflare
        time.sleep(3)
        page_source = self.driver.page_source.lower()
        
        if 'cloudflare' in page_source and 'verification' in page_source:
            print("\n" + "="*70)
            print("⚠️  CLOUDFLARE CAPTCHA DETECTED")
            print("="*70)
            print("👉 PLEASE SOLVE THE CAPTCHA IN THE BROWSER WINDOW")
            print("👉 I'll wait for you...")
            print("👉 Once you see job listings, I'll start scraping")
            print("="*70)
            
            # Wait for user to solve CAPTCHA (check every 3 seconds)
            captcha_solved = False
            wait_time = 0
            max_wait = 120  # 2 minutes max
            
            while not captcha_solved and wait_time < max_wait:
                time.sleep(3)
                wait_time += 3
                
                page_source = self.driver.page_source.lower()
                
                # Check if CAPTCHA is gone
                if 'cloudflare' not in page_source or 'verification' not in page_source:
                    # Check if we see job listings
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    job_cards = soup.find_all('div', class_='job_seen_beacon') or soup.find_all('div', attrs={'data-jk': True})
                    
                    if job_cards:
                        print("\n✅ CAPTCHA SOLVED! Found job listings!")
                        captcha_solved = True
                    else:
                        print(f"⏳ Waiting... ({wait_time}s)")
                else:
                    print(f"⏳ Waiting for CAPTCHA... ({wait_time}s)")
            
            if not captcha_solved:
                print("\n❌ Timeout waiting for CAPTCHA. Please try again.")
                return []
        else:
            print("✅ No CAPTCHA detected!\n")
        
        # Now scrape pages
        for page_num in range(max_pages):
            if page_num > 0:
                page_url = f"{url}&start={page_num * 10}"
                print(f"\n📄 Loading page {page_num + 1}...")
                self.driver.get(page_url)
                time.sleep(3)
            else:
                print(f"\n📄 Page {page_num + 1}/{max_pages}")
            
            # Extract jobs from current page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            jobs = self.extract_jobs(soup)
            
            if jobs:
                print(f"✅ Found {len(jobs)} jobs on this page")
                
                for idx, job in enumerate(jobs, 1):
                    print(f"  {idx:2d}. {job['title'][:55]:55s} @ {(job['company'] or 'Unknown')[:20]}")
                    all_jobs.append(job)
            else:
                print("⚠️  No jobs found on this page")
                break
            
            # Delay between pages
            if page_num < max_pages - 1:
                time.sleep(2)
        
        return all_jobs
    
    def extract_jobs(self, soup):
        """Extract jobs from page HTML"""
        jobs = []
        
        # Find job cards - try multiple selectors
        job_cards = (
            soup.find_all('div', class_='job_seen_beacon') or
            soup.find_all('div', attrs={'data-jk': True}) or
            soup.find_all('td', class_='resultContent')
        )
        
        for card in job_cards:
            job = self.extract_job_data(card)
            if job['title']:
                jobs.append(job)
        
        return jobs
    
    def extract_job_data(self, card):
        """Extract data from a job card"""
        job = {
            'featured_image': None,
            'title': None,
            'featured': False,
            'filled': False,
            'urgent': False,
            'description': None,
            'category': None,
            'type': None,
            'tag': [],
            'expiry_date': None,
            'gender': None,
            'apply_type': 'external',
            'apply_url': None,
            'apply_email': None,
            'salary_type': None,
            'salary': None,
            'max_salary': None,
            'experience': None,
            'career_level': None,
            'qualification': None,
            'video_url': None,
            'photos': [],
            'application_deadline_date': None,
            'address': None,
            'location': None,
            'map_location': None,
            'company': None,
            'company_rating': None,
            'posted_date': None,
            'job_id': None,
            'source': 'indeed_cr'
        }
        
        try:
            # Job ID
            job['job_id'] = card.get('data-jk')
            
            # Title and URL
            title_elem = card.find('h2', class_='jobTitle') or card.find('a', class_='jcs-JobTitle')
            if title_elem:
                # Extract text
                title_span = title_elem.find('span') or title_elem.find('a') or title_elem
                job['title'] = title_span.get_text(strip=True)
                
                # Extract URL
                link = title_elem.find('a')
                if link and link.get('href'):
                    href = link['href']
                    job['apply_url'] = f"https://cr.indeed.com{href}" if not href.startswith('http') else href
            
            # Company
            company_elem = card.find('span', {'data-testid': 'company-name'}) or card.find('span', class_='companyName')
            if company_elem:
                job['company'] = company_elem.get_text(strip=True)
            
            # Company Rating
            rating_elem = card.find('span', class_='ratingNumber')
            if rating_elem:
                try:
                    job['company_rating'] = float(rating_elem.get_text(strip=True))
                except:
                    pass
            
            # Location
            location_elem = card.find('div', {'data-testid': 'text-location'}) or card.find('div', class_='companyLocation')
            if location_elem:
                location = location_elem.get_text(strip=True)
                job['location'] = location
                job['address'] = location
            
            # Salary
            salary_elem = card.find('div', class_='salary-snippet') or card.find('span', class_='salary')
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)
                job['salary'] = salary_text
                
                # Detect salary type
                if 'hora' in salary_text.lower() or 'hour' in salary_text.lower():
                    job['salary_type'] = 'hourly'
                elif 'año' in salary_text.lower() or 'year' in salary_text.lower():
                    job['salary_type'] = 'yearly'
                else:
                    job['salary_type'] = 'monthly'
            
            # Description
            desc_elem = card.find('div', class_='job-snippet') or card.find('ul', class_='job-snippet')
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True)
                job['description'] = desc_text
                
                # Detect job type
                desc_lower = desc_text.lower()
                if 'tiempo completo' in desc_lower or 'full time' in desc_lower:
                    job['type'] = 'full-time'
                elif 'medio tiempo' in desc_lower or 'part time' in desc_lower:
                    job['type'] = 'part-time'
                elif 'contrato' in desc_lower or 'contract' in desc_lower:
                    job['type'] = 'contract'
            
            # Posted date
            date_elem = card.find('span', class_='date')
            if date_elem:
                job['posted_date'] = date_elem.get_text(strip=True)
            
            # Tags
            card_html = str(card).lower()
            if 'patrocinado' in card_html or 'sponsored' in card_html:
                job['featured'] = True
                job['tag'].append('sponsored')
            
            if 'urgently' in card_html or 'urge contratar' in card_html:
                job['urgent'] = True
                job['tag'].append('urgent')
            
            # Company logo
            logo_elem = card.find('img', class_=re.compile(r'logo|avatar'))
            if logo_elem and logo_elem.get('src'):
                job['featured_image'] = logo_elem['src']
        
        except Exception as e:
            print(f"    ⚠️  Error extracting job: {e}")
        
        return job
    
    def close(self):
        """Close browser"""
        print("\n🔒 Closing browser...")
        try:
            self.driver.quit()
        except:
            pass
    
    def save_to_json(self, jobs, filename='indeed_jobs.json'):
        """Save to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved {len(jobs)} jobs to {filename}")
    
    def save_to_csv(self, jobs, filename='indeed_jobs.csv'):
        """Save to CSV"""
        if not jobs:
            print("⚠️  No jobs to save")
            return
        
        keys = jobs[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for job in jobs:
                row = {k: ', '.join(map(str, v)) if isinstance(v, list) else v 
                       for k, v in job.items()}
                writer.writerow(row)
        print(f"💾 Saved {len(jobs)} jobs to {filename}")


def main():
    print("\n" + "="*70)
    print("INDEED COSTA RICA SCRAPER - MANUAL CAPTCHA SOLVER")
    print("="*70)
    print("\n📌 HOW IT WORKS:")
    print("   1. Browser opens automatically")
    print("   2. If CAPTCHA appears, YOU solve it manually")
    print("   3. Script waits for you to finish")
    print("   4. Then automatically scrapes all pages")
    print("="*70 + "\n")
    
    input("Press ENTER to start...")
    
    scraper = None
    try:
        # Initialize scraper
        scraper = IndeedManualCAPTCHAScraper()
        
        # Target URL
        url = "https://cr.indeed.com/jobs?q=&l=costa+rica&from=searchOnHP"
        
        # Scrape jobs (YOU solve CAPTCHA when prompted)
        jobs = scraper.scrape_with_manual_captcha(url, max_pages=5)
        
        if jobs:
            print("\n" + "="*70)
            print(f"✅ SUCCESS! Scraped {len(jobs)} jobs")
            print("="*70 + "\n")
            
            # Save results
            scraper.save_to_json(jobs, 'indeed_cr_jobs.json')
            scraper.save_to_csv(jobs, 'indeed_cr_jobs.csv')
            
            # Show statistics
            print("\n📊 STATISTICS:")
            print("-"*70)
            print(f"Total jobs: {len(jobs)}")
            print(f"With company: {sum(1 for j in jobs if j['company'])}")
            print(f"With location: {sum(1 for j in jobs if j['location'])}")
            print(f"With salary: {sum(1 for j in jobs if j['salary'])}")
            print(f"Featured: {sum(1 for j in jobs if j['featured'])}")
            print(f"Urgent: {sum(1 for j in jobs if j['urgent'])}")
            
            # Sample job
            print("\n📋 SAMPLE JOB:")
            print("-"*70)
            sample = jobs[0]
            print(f"Title: {sample['title']}")
            print(f"Company: {sample['company']}")
            print(f"Location: {sample['location']}")
            print(f"Salary: {sample['salary']}")
            print(f"Type: {sample['type']}")
            print(f"Posted: {sample['posted_date']}")
            print(f"URL: {sample['apply_url']}")
            print("-"*70)
        else:
            print("\n❌ No jobs scraped")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper:
            scraper.close()
        print("\n✅ Done!\n")


if __name__ == "__main__":
    main()