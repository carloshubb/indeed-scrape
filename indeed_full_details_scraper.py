"""
Indeed Costa Rica Complete Job Scraper - FIXED VERSION
With improved error handling for GitHub Actions
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import json
import csv
import time
import random
import re
import warnings
import sys
import os
from datetime import datetime, timedelta



default_deadline = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
warnings.filterwarnings("ignore", category=DeprecationWarning)

class IndeedFullDetailsScraper:
    def __init__(self, headless=False):
        """Initialize Selenium driver"""
        options = uc.ChromeOptions()
        
        if headless:
            options.add_argument('--headless=new')
        
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--lang=es-ES')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional options for stability
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')
        options.add_argument('--silent')
        
        print("🚀 Initializing Chrome driver...")
        try:
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.set_page_load_timeout(30)
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
                'account manager', 'vendedor', 'mercadeo', 'publicidad'
            ],
            'Finance/Accounting': [
                'accountant', 'finance', 'accounting', 'contador', 'contabilidad', 'finanzas',
                'auditor', 'financial', 'cpa', 'bookkeeper'
            ],
            'Human Resources': [
                'human resources', 'hr', 'recruiter', 'recursos humanos', 'reclutamiento',
                'recruitment', 'talent', 'talento'
            ],
            'Administrative': [
                'administrative', 'assistant', 'secretary', 'office', 'receptionist',
                'administrativo', 'asistente', 'secretaria'
            ],
            'Management': [
                'manager', 'director', 'supervisor', 'lead', 'gerente', 'jefe'
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
    
    def extract_experience_from_text(self, text):
        """Extract experience requirements"""
        if not text:
            return None, None
        
        text_lower = text.lower()
        
        exp_patterns = [
            r'(\d+)\+?\s*(años?|years?)\s*(?:de\s*)?(?:experiencia|experience)',
            r'(?:experiencia|experience)\s*(?:de\s*)?(\d+)\+?\s*(años?|years?)'
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text_lower)
            if match:
                years = int(match.group(1))
                if years >= 7:
                    return f"{years}+ years", 'senior'
                elif years >= 3:
                    return f"{years}+ years", 'mid'
                elif years >= 1:
                    return f"{years}+ years", 'junior'
                else:
                    return f"{years} years", 'entry'
        
        if any(word in text_lower for word in ['senior', 'sr.', 'lead']):
            return '5+ years', 'senior'
        elif any(word in text_lower for word in ['junior', 'jr.', 'entry']):
            return '0-2 years', 'entry'
        
        return None, None
    
    def extract_qualification(self, text):
        """Extract education qualification"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['phd', 'doctorado']):
            return 'doctorate'
        elif any(word in text_lower for word in ['maestría', 'master', 'mba']):
            return 'master'
        elif any(word in text_lower for word in ['licenciatura', 'bachelor']):
            return 'bachelor'
        elif any(word in text_lower for word in ['técnico', 'technical']):
            return 'associate'
        
        return None
    
    def extract_job_type(self, text):
        """Extract job type"""
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
        """Click job and extract full details"""
        try:
            job_element.click()
            time.sleep(random.uniform(2, 3))
            
            # Wait for details to load
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#jobDescriptionText, .jobsearch-JobComponent-description")))
            except:
                pass
            
            # Extract full description - UPDATED SELECTORS
            desc_selectors = [
                "#jobDescriptionText",
                ".jobsearch-JobComponent-description",
                "div[id*='jobDescriptionText']",
                "div.jobsearch-jobDescriptionText",
                "div[class*='jobDescription']"
            ]
            
            for selector in desc_selectors:
                try:
                    desc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    full_description = desc_elem.text.strip()
                    if full_description:
                        job_data['_job_description'] = full_description
                        
                        category = self.extract_category(job_data['_job_title'], full_description)
                        if category:
                            job_data['_job_category'] = category
                        
                        exp, career_level = self.extract_experience_from_text(full_description)
                        if exp:
                            job_data['_job_experience'] = exp
                        if career_level:
                            job_data['_job_career_level'] = career_level
                        
                        qualification = self.extract_qualification(full_description)
                        if qualification:
                            job_data['_job_qualification'] = qualification
                        
                        if not job_data['_job_type']:
                            job_type = self.extract_job_type(full_description)
                            if job_type:
                                job_data['_job_type'] = job_type
                        break
                except:
                    continue
            
            # Extract location
            location_selectors = [
                'div[data-testid="jobsearch-JobInfoHeader-companyLocation"]',
                'div[data-testid="inlineHeader-companyLocation"]',
                'div.jobsearch-JobInfoHeader-subtitle',
                'div[class*="companyLocation"]'
            ]
            
            for selector in location_selectors:
                try:
                    loc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    loc_text = loc_elem.text.strip()
                    if loc_text:
                        job_data['_job_location'] = loc_text
                        job_data['_job_address'] = loc_text
                        job_data['_job_map_location'] = loc_text
                        break
                except:
                    continue
            
            # Extract salary
            salary_selectors = [
                "#salaryInfoAndJobType",
                'div[id*="salary"]',
                'div.css-kyg8or',
                'div[class*="salary"]'
            ]
            
            for selector in salary_selectors:
                try:
                    salary_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    salary_text = salary_elem.text.strip()
                    if salary_text and not job_data['_job_salary']:
                        salary_info = self.extract_salary(salary_text)
                        job_data.update(salary_info)
                        break
                except:
                    continue
            
        except Exception as e:
            # Don't print errors for individual job detail extraction
            pass
    
    def extract_job_from_card(self, card):
        """Extract job data from card"""
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
            '_job_gender': None,
            '_job_apply_type': 'external',
            '_job_apply_url': None,
            '_job_apply_email': None,
            '_job_salary_type': None,
            '_job_salary': None,
            '_job_max_salary': None,
            '_job_experience': None,
            '_job_career_level': None,
            '_job_qualification': None,
            '_job_video_url': None,
            '_job_photos': [],
            '_job_application_deadline_date': default_deadline,
            '_job_address': None,
            '_job_location': None,
            '_job_map_location': None
        }
        
        try:
            # Title - UPDATED SELECTORS
            title_selectors = [
                'h2.jobTitle a span',
                'h2.jobTitle span',
                'a.jcs-JobTitle span',
                'span[id*="jobTitle"]',
                'h2 span[title]'
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['_job_title'] = title_elem.text.strip()
                    if job_data['_job_title']:
                        break
                except:
                    continue
            
            # URL
            try:
                link = card.find_element(By.CSS_SELECTOR, 'h2.jobTitle a, a.jcs-JobTitle')
                job_data['_job_apply_url'] = link.get_attribute('href')
            except:
                pass
            
            # Location
            location_selectors = [
                'div[data-testid="text-location"]',
                'div.companyLocation',
                'span.companyLocation'
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = card.find_element(By.CSS_SELECTOR, selector)
                    location_text = location_elem.text.strip()
                    if location_text:
                        job_data['_job_location'] = location_text
                        job_data['_job_address'] = location_text
                        job_data['_job_map_location'] = location_text
                        break
                except:
                    continue
            
            # Salary
            try:
                salary_elem = card.find_element(By.CSS_SELECTOR, 'div.salary-snippet-container, div.attribute_snippet')
                salary_text = salary_elem.text.strip()
                if salary_text:
                    salary_info = self.extract_salary(salary_text)
                    job_data.update(salary_info)
            except:
                pass
            
            # Snippet
            try:
                snippet_elem = card.find_element(By.CSS_SELECTOR, 'div.job-snippet, ul.job-snippet, div[class*="snippet"]')
                snippet_text = snippet_elem.text.strip()
                if snippet_text:
                    job_data['_job_description'] = snippet_text
                    job_type = self.extract_job_type(snippet_text)
                    if job_type:
                        job_data['_job_type'] = job_type
            except:
                pass
            
            # Check tags
            card_html = card.get_attribute('innerHTML').lower()
            
            if 'patrocinado' in card_html or 'sponsored' in card_html:
                job_data['_job_featured'] = 1
                job_data['_job_tag'].append('sponsored')
            
            if 'urge' in card_html or 'urgently' in card_html:
                job_data['_job_urgent'] = 1
                job_data['_job_tag'].append('urgent')
            
        except Exception as e:
            # Don't print errors for individual cards
            pass
        
        return job_data
    
    def scrape_jobs(self, search_url, max_pages=5, max_jobs=None, extract_full_details=True):
        """Main scraping function"""
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
                
                # Scroll to load
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(2)
                
                # UPDATED JOB CARD SELECTORS
                job_cards = None
                selectors = [
                    'div.job_seen_beacon',
                    'div.cardOutline',
                    'li.css-5lfssm',
                    'div[data-jk]',
                    'td.resultContent',
                    'div.slider_container div.slider_item',
                    'ul.jobsearch-ResultsList li',
                    'div[class*="job_seen"]',
                    'div[class*="result"]'
                ]
                
                for selector in selectors:
                    try:
                        cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if cards and len(cards) > 0:
                            job_cards = cards
                            print(f"  ✅ Found {len(cards)} jobs\n")
                            break
                    except:
                        continue
                
                if not job_cards:
                    print("  ⚠️ No job cards found")
                    break
                
                # Process jobs
                for idx, card in enumerate(job_cards, 1):
                    try:
                        job_data = self.extract_job_from_card(card)
                        
                        if not job_data['_job_title']:
                            continue
                        
                        title_display = job_data['_job_title'][:50]
                        print(f"  {idx:2d}. {title_display:50s}")
                        
                        if extract_full_details:
                            self.click_job_and_extract_details(card, job_data)
                        
                        if not job_data['_job_category']:
                            category = self.extract_category(job_data['_job_title'], job_data['_job_description'])
                            job_data['_job_category'] = category
                        
                        all_jobs.append(job_data)
                        
                        if max_jobs and len(all_jobs) >= max_jobs:
                            print(f"\n✅ Reached max jobs limit ({max_jobs})")
                            return all_jobs
                        
                        time.sleep(random.uniform(0.5, 1.5))
                        
                    except Exception as e:
                        continue
                
                print()
                
                if page < max_pages - 1:
                    delay = random.uniform(4, 7)
                    print(f"  ⏳ Waiting {delay:.1f}s before next page...\n")
                    time.sleep(delay)
                
            except Exception as e:
                print(f"  ⚠️ Page error: {e}")
                break
        
        return all_jobs
    
    def close(self):
        """Close browser safely"""
        print("\n🔒 Closing browser...")
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except Exception as e:
            # Silently ignore cleanup errors
            pass
    
    def save_to_json(self, jobs, filename='indeed_jobs.json'):
        """Save to JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, ensure_ascii=False, indent=2)
            print(f"💾 Saved {len(jobs)} jobs to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")
            return False
    
    def save_to_csv(self, jobs, filename='indeed_jobs.csv'):
        """Save to CSV"""
        if not jobs:
            print("⚠️ No jobs to save")
            return False
        
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
            return True
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")
            return False


def main():
    print("="*70)
    print("INDEED COSTA RICA - JOB SCRAPER")
    print("="*70)
    print()
    
    # Get environment variables or use defaults
    max_pages = int(os.getenv('MAX_PAGES', '5'))
    max_jobs = os.getenv('MAX_JOBS', '')
    max_jobs = int(max_jobs) if max_jobs and max_jobs.isdigit() else None
    
    search_url = "https://cr.indeed.com/jobs?q=&l=costa+rica&from=searchOnHP&vjk=8223ee513792bd50"
    
    scraper = None
    success = False
    
    try:
        # Check if running in GitHub Actions
        is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        
        scraper = IndeedFullDetailsScraper(headless=is_github_actions)
        
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
            
            json_saved = scraper.save_to_json(jobs, json_filename)
            csv_saved = scraper.save_to_csv(jobs, csv_filename)
            
            if json_saved and csv_saved:
                success = True
            
            # Statistics
            print("\n📊 STATISTICS:")
            print("-" * 70)
            print(f"Total jobs: {len(jobs)}")
            print(f"With full description: {sum(1 for j in jobs if j['_job_description'] and len(j['_job_description']) > 200)}")
            print(f"With salary info: {sum(1 for j in jobs if j['_job_salary'])}")
            
            categories = {}
            for job in jobs:
                cat = job['_job_category'] or 'Unknown'
                categories[cat] = categories.get(cat, 0) + 1
            
            print("\n📂 TOP CATEGORIES:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {cat}: {count}")
            
            print("-" * 70)
            
        else:
            print("\n⚠️ No jobs scraped")
            success = False
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        success = False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        success = False
    finally:
        if scraper:
            try:
                scraper.close()
            except:
                pass
        print("\n✅ Done!")
    
    # Exit with proper code for GitHub Actions
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()