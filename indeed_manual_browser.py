"""
PRACTICAL SOLUTION: Manual Cookie Extraction Method

Since Indeed blocks automation, this is the most reliable approach:
1. You manually open Indeed and pass Cloudflare
2. Extract cookies from your browser
3. Use those cookies in the scraper

This bypasses all protection because we're using YOUR legitimate session
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
from datetime import datetime, timedelta
import time

class IndeedManualCookieScraper:
    """
    Uses cookies from your browser session to bypass Cloudflare
    """
    
    def __init__(self, cookies_dict=None):
        """
        Initialize with cookies from your browser
        
        Args:
            cookies_dict: Dictionary of cookies from your browser
        """
        self.session = requests.Session()
        
        # Set realistic headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-419,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'DNT': '1',
        })
        
        # Add cookies if provided
        if cookies_dict:
            for name, value in cookies_dict.items():
                self.session.cookies.set(name, value)
    
    def scrape_jobs(self, url, max_pages=5):
        """Scrape jobs using session with cookies"""
        all_jobs = []
        
        print(f"🔍 Starting scrape with manual cookies")
        print(f"📍 URL: {url}\n")
        
        for page in range(max_pages):
            page_url = url if page == 0 else f"{url}&start={page * 10}"
            
            print(f"📄 Page {page + 1}/{max_pages}")
            
            try:
                response = self.session.get(page_url, timeout=30)
                
                # Check if we're blocked
                if response.status_code == 403:
                    print("  ❌ 403 Forbidden - Cookies may be expired")
                    print("  → Extract new cookies from your browser")
                    break
                
                if 'cloudflare' in response.text.lower() and 'verification' in response.text.lower():
                    print("  ❌ Cloudflare challenge detected")
                    print("  → Extract new cookies after passing CAPTCHA")
                    break
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract jobs
                jobs = self.extract_jobs(soup)
                
                if jobs:
                    print(f"  ✅ Found {len(jobs)} jobs")
                    all_jobs.extend(jobs)
                else:
                    print("  ⚠️  No jobs found")
                    # Save for debugging
                    with open(f'debug_no_jobs_page{page+1}.html', 'w', encoding='utf-8') as f:
                        f.write(soup.prettify())
                    break
                
                # Delay between pages
                if page < max_pages - 1:
                    time.sleep(3)
            
            except Exception as e:
                print(f"  ❌ Error: {e}")
                break
        
        return all_jobs
    
    def extract_jobs(self, soup):
        """Extract jobs from HTML"""
        jobs = []
        
        # Find job cards - try multiple selectors
        job_cards = (
            soup.find_all('div', class_='job_seen_beacon') or
            soup.find_all('div', attrs={'data-jk': True}) or
            soup.find_all('td', class_='resultContent') or
            soup.find_all('div', class_=re.compile(r'jobsearch.*Card'))
        )
        
        for card in job_cards:
            job = self.extract_job_data(card)
            if job['title']:
                jobs.append(job)
        
        return jobs
    
    def extract_job_data(self, card):
        """Extract data from job card"""
        job = {
            'title': None, 'company': None, 'location': None,
            'salary': None, 'salary_type': None, 'description': None,
            'posted_date': None, 'apply_url': None, 'job_id': None,
            'type': None, 'featured': False, 'urgent': False,
            'company_rating': None, 'source': 'indeed_cr'
        }
        
        # Job ID
        job['job_id'] = card.get('data-jk')
        
        # Title
        title_elem = card.find('h2', class_='jobTitle') or card.find('a', class_='jcs-JobTitle')
        if title_elem:
            job['title'] = title_elem.get_text(strip=True)
            link = title_elem.find('a') if title_elem.name != 'a' else title_elem
            if link and link.get('href'):
                job['apply_url'] = f"https://cr.indeed.com{link['href']}" if not link['href'].startswith('http') else link['href']
        
        # Company
        company_elem = card.find('span', {'data-testid': 'company-name'}) or card.find('span', class_='companyName')
        if company_elem:
            job['company'] = company_elem.get_text(strip=True)
        
        # Company rating
        rating_elem = card.find('span', class_='ratingNumber')
        if rating_elem:
            try:
                job['company_rating'] = float(rating_elem.get_text(strip=True))
            except:
                pass
        
        # Location
        location_elem = card.find('div', {'data-testid': 'text-location'}) or card.find('div', class_='companyLocation')
        if location_elem:
            job['location'] = location_elem.get_text(strip=True)
        
        # Salary
        salary_elem = card.find('div', class_='salary-snippet') or card.find('span', class_='salary')
        if salary_elem:
            job['salary'] = salary_elem.get_text(strip=True)
        
        # Description snippet
        desc_elem = card.find('div', class_='job-snippet') or card.find('ul', class_='job-snippet')
        if desc_elem:
            job['description'] = desc_elem.get_text(strip=True)
        
        # Posted date
        date_elem = card.find('span', class_='date')
        if date_elem:
            job['posted_date'] = date_elem.get_text(strip=True)
        
        # Check for tags
        html_text = str(card).lower()
        if 'patrocinado' in html_text or 'sponsored' in html_text:
            job['featured'] = True
        if 'urgently' in html_text or 'urge contratar' in html_text:
            job['urgent'] = True
        
        return job
    
    def save_to_json(self, jobs, filename='indeed_jobs.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved to {filename}")
    
    def save_to_csv(self, jobs, filename='indeed_jobs.csv'):
        if not jobs:
            return
        keys = jobs[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(jobs)
        print(f"💾 Saved to {filename}")


# =================================================================
# STEP-BY-STEP INSTRUCTIONS TO EXTRACT COOKIES
# =================================================================

def print_instructions():
    """Print detailed instructions for extracting cookies"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                  HOW TO EXTRACT COOKIES FROM BROWSER                 ║
╚══════════════════════════════════════════════════════════════════════╝

OPTION 1: Using Chrome DevTools (EASIEST)
──────────────────────────────────────────────────────────────────────
1. Open Google Chrome
2. Go to: https://cr.indeed.com/jobs?q=&l=costa+rica&from=searchOnHP
3. Complete the Cloudflare CAPTCHA if prompted
4. Once you see job listings, press F12 (Opens DevTools)
5. Click the "Application" tab (or "Storage" in Firefox)
6. In left sidebar: Expand "Cookies" → Click "https://cr.indeed.com"
7. You'll see a list of cookies. Look for these important ones:
   - cf_clearance (Cloudflare bypass cookie)
   - INDEED_CSRF_TOKEN
   - CTK
   - Any cookie with "indeed" in the name

8. Copy the cookie values into the script below


OPTION 2: Using Browser Extension (AUTOMATIC)
──────────────────────────────────────────────────────────────────────
1. Install "EditThisCookie" or "Cookie-Editor" extension
2. Visit Indeed and pass Cloudflare
3. Click the extension icon
4. Click "Export" → Copy all cookies
5. Paste into script


OPTION 3: Just Use Your Browser Manually
──────────────────────────────────────────────────────────────────────
If scraping is too difficult, simply:
1. Open Indeed in your browser
2. Search for jobs manually
3. Copy job URLs and details into Excel
4. Or use the browser's "Copy as Markdown" extension

═══════════════════════════════════════════════════════════════════════

""")


def example_with_cookies():
    """Example of how to use the scraper with cookies"""
    
    print_instructions()
    
    print("="*70)
    print("EXAMPLE: Using Manual Cookies")
    print("="*70)
    print()
    
    # Example cookies (YOU NEED TO REPLACE THESE WITH YOUR OWN)
    cookies = {
        # REPLACE THESE WITH YOUR ACTUAL COOKIES
        'cf_clearance': 'YOUR_CF_CLEARANCE_COOKIE_HERE',
        'INDEED_CSRF_TOKEN': 'YOUR_CSRF_TOKEN_HERE',
        'CTK': 'YOUR_CTK_COOKIE_HERE',
        # Add more cookies as needed
    }
    
    # Check if user has set cookies
    if 'YOUR_CF_CLEARANCE_COOKIE_HERE' in cookies.get('cf_clearance', ''):
        print("⚠️  WARNING: You haven't set your cookies yet!")
        print("   Follow the instructions above to extract cookies from your browser")
        print("   Then replace the cookie values in this script\n")
        return
    
    # Create scraper with cookies
    scraper = IndeedManualCookieScraper(cookies)
    
    # Scrape jobs
    url = "https://cr.indeed.com/jobs?q=&l=costa+rica&from=searchOnHP"
    jobs = scraper.scrape_jobs(url, max_pages=5)
    
    if jobs:
        print(f"\n✅ SUCCESS! Scraped {len(jobs)} jobs")
        scraper.save_to_json(jobs, 'indeed_jobs_manual.json')
        scraper.save_to_csv(jobs, 'indeed_jobs_manual.csv')
        
        # Show sample
        print("\n📋 Sample job:")
        print(f"Title: {jobs[0]['title']}")
        print(f"Company: {jobs[0]['company']}")
        print(f"Location: {jobs[0]['location']}")
    else:
        print("\n❌ No jobs scraped")


# =================================================================
# ALTERNATIVE: SIMPLE BROWSER AUTOMATION
# =================================================================

def simple_browser_solution():
    """Simplest solution - just open browser and wait for user"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                    SIMPLEST SOLUTION (NO CODING)                     ║
╚══════════════════════════════════════════════════════════════════════╝

Since Indeed's protection is very strong, here's the EASIEST approach:

1. BROWSER EXTENSION METHOD:
   ────────────────────────────────────────────────────────────────
   • Install "Web Scraper" extension (Chrome/Firefox)
   • It runs IN your browser (no blocking)
   • Define what data to scrape visually
   • Export to CSV
   • Link: https://webscraper.io/

2. EXCEL/SHEETS METHOD:
   ────────────────────────────────────────────────────────────────
   • Open Indeed, complete CAPTCHA
   • Copy job listings
   • Use "Power Query" (Excel) or "ImportHTML" (Sheets)
   • Refresh data without re-scraping

3. HIRING A SERVICE:
   ────────────────────────────────────────────────────────────────
   • ScraperAPI.com - Handles all blocking ($49/month)
   • Bright Data - Residential proxies
   • Apify - Pre-built Indeed scraper

4. CONTACT YOUR CLIENT:
   ────────────────────────────────────────────────────────────────
   • Explain Indeed blocks automation
   • Suggest using Indeed's Job API (official)
   • Or scrape less frequently with manual intervention

══════════════════════════════════════════════════════════════════════
""")


if __name__ == "__main__":
    # Show all options
    example_with_cookies()
    print("\n")
    simple_browser_solution()