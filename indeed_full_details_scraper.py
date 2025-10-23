"""
Indeed Costa Rica Complete Job Scraper - GitHub Actions Compatible
Updated version with CI/CD environment support
"""

import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import json
import csv
import time
import random
import re
import warnings
from datetime import datetime, timedelta

default_deadline = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
warnings.filterwarnings("ignore", category=DeprecationWarning)

class IndeedFullDetailsScraper:
    def __init__(self, headless=True):
        """Initialize Selenium driver with CI-friendly options"""
        options = Options()
        
        # Essential for GitHub Actions
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=es-ES')
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional stability options
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        print("🚀 Initializing Chrome driver...")
        print(f"   Environment: {'CI/CD' if os.getenv('CI') else 'Local'}")
        print(f"   Headless: {headless}")
        
        try:
            # Use system Chrome in CI environment
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(60)
            self.wait = WebDriverWait(self.driver, 15)
            print("✅ Driver ready!\n")
        except Exception as e:
            print(f"❌ Failed to initialize driver: {e}")
            raise
    
    def extract_category(self, title, description):
        """Extract job category from title and description keywords"""
        if not title and not description:
            return None
        
        text = f"{title or ''} {description or ''}".lower()
        
        categories = {
            'IT/Software Development': [
                'software', 'developer', 'programming', 'engineer', 'web', 'mobile',
                'frontend', 'backend', 'fullstack', 'devops', 'cloud', 'java', 'python',
                'javascript', 'react', 'angular', 'node', 'php', 'dotnet', '.net',
                'desarrollo', 'programador', 'desarrollador', 'sistemas', 'typescript'
            ],
            'Customer Service': [
                'customer service', 'call center', 'support', 'help desk', 'servicio al cliente',
                'atención al cliente', 'soporte', 'representante', 'agent', 'cliente'
            ],
            'Sales/Marketing': [
                'sales', 'marketing', 'ventas', 'comercial', 'business development',
                'account manager', 'vendedor', 'mercadeo'
            ],
            'Finance/Accounting': [
                'accountant', 'finance', 'accounting', 'contador', 'contabilidad', 'finanzas',
                'auditor', 'financial', 'cpa', 'bookkeeper'
            ],
            'Human Resources': [
                'human resources', 'hr', 'recruiter', 'recursos humanos', 'reclutamiento',
                'recruitment', 'talent'
            ],
            'Administrative': [
                'administrative', 'assistant', 'secretary', 'office', 'receptionist',
                'administrativo', 'asistente'
            ]
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return 'General/Other'
    
    def parse_date(self, date_str):
        """Parse Indeed date formats"""
        if not date_str:
            return None
        
        date_str = date_str.lower().strip()
        
        if 'hoy' in date_str or 'today' in date_str or 'just posted' in date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        if 'hace' in date_str or 'ago' in date_str:
            numbers = re.findall(r'\d+', date_str)
            if numbers:
                num = int(numbers[0])
                if 'hora' in date_str or 'hour' in date_str:
                    date = datetime.now()
                else:
                    date = datetime.now() - timedelta(days=num)
                return date.strftime('%Y-%m-%d')
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def extract_salary(self, text):
        """Extract salary information"""
        if not text:
            return {'_job_salary_type': None, '_job_salary': None, '_job_max_salary': None}
        
        text_lower = text.lower()
        salary_data = {
            '_job_salary_type': 'monthly',
            '_job_salary': None,
            '_job_max_salary': None
        }
        
        if 'hora' in text_lower or 'hour' in text_lower or '/hr' in text_lower:
            salary_data['_job_salary_type'] = 'hourly'
        elif 'año' in text_lower or 'year' in text_lower or 'anual' in text_lower:
            salary_data['_job_salary_type'] = 'yearly'
        
        numbers = re.findall(r'[\d,]+(?:\.\d{2})?', text)
        if numbers:
            cleaned = [float(n.replace(',', '')) for n in numbers]
            salary_data['_job_salary'] = cleaned[0]
            if len(cleaned) > 1:
                salary_data['_job_max_salary'] = cleaned[1]
        
        return salary_data
    
    def extract_job_type(self, text):
        """Extract job type from text"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        if 'tiempo completo' in text_lower or 'full time' in text_lower:
            return 'full-time'
        elif 'medio tiempo' in text_lower or 'part time' in text_lower:
            return 'part-time'
        elif 'temporal' in text_lower or 'temporary' in text_lower:
            return 'temporary'
        elif 'contrato' in text_lower or 'contract' in text_lower:
            return 'contract'
        
        return None
    
    def click_job_and_extract_details(self, job_element, job_data):
        """Click on a job and extract full details"""
        try:
            job_element.click()
            time.sleep(random.uniform(2, 3))
            
            try:
                self.wait.until(EC.presence_of_element_located((By.ID, "jobDescriptionText")))
            except:
                pass
            
            # Extract full description
            try:
                desc_elem = self.driver.find_element(By.ID, "jobDescriptionText")
                full_description = desc_elem.text.strip()
                job_data['_job_description'] = full_description
                
                category = self.extract_category(job_data['_job_title'], full_description)
                if category:
                    job_data['_job_category'] = category
                
                job_type = self.extract_job_type(full_description)
                if job_type and not job_data['_job_type']:
                    job_data['_job_type'] = job_type
            except:
                pass
            
            # Extract location
            try:
                location_selectors = [
                    'div[data-testid="jobsearch-JobInfoHeader-companyLocation"]',
                    'div.jobsearch-JobInfoHeader-subtitle-container div'
                ]
                
                for selector in location_selectors:
                    try:
                        loc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        loc_text = loc_elem.text.strip()
                        if loc_text and not job_data['_job_location']:
                            job_data['_job_location'] = loc_text
                            job_data['_job_address'] = loc_text
                            break
                    except:
                        continue
            except:
                pass
            
        except Exception as e:
            print(f"      ⚠️  Error extracting details: {e}")
    
    def extract_job_from_card(self, card):
        """Extract basic job data from a job card"""
        job_data = {
            '_job_featured_image': None,
            '_job_title': None,
            '_job_featured': 0,
            '_job_filled': 0,
            '_job_urgent': 0,
            '_job_description': None,
            '_job_category': None,
            '_job_type': None,
            '_job_tag': ['Costa Rica'],
            '_job_expiry_date': default_deadline,
            '_job_apply_type': 'external',
            '_job_apply_url': None,
            '_job_salary_type': None,
            '_job_salary': None,
            '_job_max_salary': None,
            '_job_application_deadline_date': default_deadline,
            '_job_address': None,
            '_job_location': None
        }
        
        try:
            # Title
            title_selectors = [
                'h2.jobTitle span',
                'h2.jobTitle a',
                'a.jcs-JobTitle'
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['_job_title'] = title_elem.text.strip()
                    
                    try:
                        if title_elem.tag_name == 'a':
                            job_data['_job_apply_url'] = title_elem.get_attribute('href')
                        else:
                            link = card.find_element(By.CSS_SELECTOR, 'h2.jobTitle a')
                            job_data['_job_apply_url'] = link.get_attribute('href')
                    except:
                        pass
                    break
                except:
                    continue
            
            # Location
            try:
                location_elem = card.find_element(By.CSS_SELECTOR, 'div[data-testid="text-location"], .companyLocation')
                location_text = location_elem.text.strip()
                job_data['_job_location'] = location_text
                job_data['_job_address'] = location_text
            except:
                pass
            
            # Salary
            try:
                salary_elem = card.find_element(By.CSS_SELECTOR, '.salary-snippet-container, .salary-snippet')
                salary_text = salary_elem.text.strip()
                salary_info = self.extract_salary(salary_text)
                job_data.update(salary_info)
            except:
                pass
            
            # Snippet
            try:
                snippet_elem = card.find_element(By.CSS_SELECTOR, '.job-snippet, ul.job-snippet')
                snippet_text = snippet_elem.text.strip()
                job_data['_job_description'] = snippet_text
                
                job_type = self.extract_job_type(snippet_text)
                if job_type:
                    job_data['_job_type'] = job_type
            except:
                pass
            
        except Exception as e:
            print(f"      ⚠️  Error extracting from card: {e}")
        
        return job_data
    
    def scrape_jobs(self, search_url, max_pages=5, max_jobs=None, extract_full_details=True):
        """Scrape jobs with optional full details extraction"""
        all_jobs = []
        
        print(f"🔍 Starting scrape: {search_url}\n")
        print(f"📋 Extract full details: {'YES' if extract_full_details else 'NO'}\n")
        
        for page in range(max_pages):
            if page == 0:
                url = search_url
            else:
                separator = '&' if '?' in search_url else '?'
                url = f"{search_url}{separator}start={page * 10}"
            
            print(f"📄 Page {page + 1}/{max_pages}")
            
            try:
                self.driver.get(url)
                time.sleep(random.uniform(3, 5))
                
                # Scroll
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(2)
                
                # Find job cards
                job_cards = None
                selectors = [
                    'div.job_seen_beacon',
                    'div[data-jk]',
                    'td.resultContent'
                ]
                
                for selector in selectors:
                    try:
                        cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if cards:
                            job_cards = cards
                            print(f"  ✅ Found {len(cards)} jobs\n")
                            break
                    except:
                        continue
                
                if not job_cards:
                    print("  ⚠️  No job cards found")
                    # Save debug info
                    try:
                        self.driver.save_screenshot(f"debug_page{page+1}.png")
                        with open(f"debug_page{page+1}.html", "w", encoding="utf-8") as f:
                            f.write(self.driver.page_source)
                    except:
                        pass
                    break
                
                # Extract jobs
                for idx, card in enumerate(job_cards, 1):
                    try:
                        job_data = self.extract_job_from_card(card)
                        
                        if not job_data['_job_title']:
                            continue
                        
                        print(f"  {idx:2d}. {job_data['_job_title'][:50]}")
                        
                        if extract_full_details:
                            self.click_job_and_extract_details(card, job_data)
                        
                        if not job_data['_job_category']:
                            category = self.extract_category(job_data['_job_title'], job_data['_job_description'])
                            job_data['_job_category'] = category
                        
                        all_jobs.append(job_data)
                        
                        if max_jobs and len(all_jobs) >= max_jobs:
                            print(f"\n✅ Reached max jobs limit ({max_jobs})")
                            return all_jobs
                        
                        time.sleep(random.uniform(0.5, 1))
                        
                    except Exception as e:
                        print(f"      ❌ Error: {e}")
                        continue
                
                print()
                
                if page < max_pages - 1:
                    delay = random.uniform(3, 5)
                    print(f"  ⏳ Waiting {delay:.1f}s before next page...\n")
                    time.sleep(delay)
                
            except Exception as e:
                print(f"  ❌ Page error: {e}")
                import traceback
                traceback.print_exc()
                break
        
        return all_jobs
    
    def close(self):
        """Close browser"""
        print("\n🔒 Closing browser...")
        try:
            self.driver.quit()
        except:
            pass
    
    def save_to_json(self, jobs, filename='indeed_jobs.json'):
        """Save to JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, ensure_ascii=False, indent=2)
            print(f"💾 Saved {len(jobs)} jobs to {filename}")
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")
    
    def save_to_csv(self, jobs, filename='indeed_jobs.csv'):
        """Save to CSV"""
        if not jobs:
            print("⚠️  No jobs to save")
            return
        
        try:
            keys = jobs[0].keys()
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for job in jobs:
                    row = job.copy()
                    for key, value in row.items():
                        if isinstance(value, list):
                            row[key] = ', '.join(map(str, value))
                    writer.writerow(row)
            print(f"💾 Saved {len(jobs)} jobs to {filename}")
        except Exception as e:
            print(f"❌ Failed to save CSV: {e}")


def main():
    print("="*70)
    print("INDEED COSTA RICA - FULL DETAILS JOB SCRAPER")
    print("="*70)
    print()
    
    # Get parameters from environment or use defaults
    max_pages = int(os.getenv('MAX_PAGES', '5'))
    max_jobs_env = os.getenv('MAX_JOBS', '')
    max_jobs = int(max_jobs_env) if max_jobs_env else None
    headless = os.getenv('HEADLESS', 'true').lower() == 'true'
    
    print(f"⚙️  Configuration:")
    print(f"   Max Pages: {max_pages}")
    print(f"   Max Jobs: {max_jobs or 'unlimited'}")
    print(f"   Headless: {headless}")
    print()
    
    search_url = "https://cr.indeed.com/jobs?q=&l=costa+rica&from=searchOnHP"
    
    scraper = None
    try:
        scraper = IndeedFullDetailsScraper(headless=headless)
        
        jobs = scraper.scrape_jobs(
            search_url, 
            max_pages=max_pages,
            max_jobs=max_jobs,
            extract_full_details=True
        )
        
        if jobs:
            print(f"\n{'='*70}")
            print(f"✅ Successfully scraped {len(jobs)} jobs!")
            print(f"{'='*70}\n")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_filename = f'indeed_cr_jobs_{timestamp}.json'
            csv_filename = f'indeed_cr_jobs_{timestamp}.csv'
            
            scraper.save_to_json(jobs, json_filename)
            scraper.save_to_csv(jobs, csv_filename)
            
            # Print statistics
            print("\n📊 STATISTICS:")
            print("-" * 70)
            print(f"Total jobs: {len(jobs)}")
            print(f"With descriptions: {sum(1 for j in jobs if j['_job_description'])}")
            print(f"With salary: {sum(1 for j in jobs if j['_job_salary'])}")
            
            categories = {}
            for job in jobs:
                cat = job['_job_category'] or 'Unknown'
                categories[cat] = categories.get(cat, 0) + 1
            
            print("\n📂 CATEGORIES:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"  {cat}: {count}")
            
            print("\n📦 EXPORTED FILES:")
            print(f"  ✅ {json_filename}")
            print(f"  ✅ {csv_filename}")
            
            sys.exit(0)
        else:
            print("\n❌ No jobs scraped")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if scraper:
            scraper.close()
        print("\n✅ Done!")


if __name__ == "__main__":
    main()