"""
Indeed Costa Rica Complete Job Scraper with Full Details
Clicks into each job to extract complete information

Installation:
pip install selenium undetected-chromedriver webdriver-manager
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
from datetime import datetime, timedelta

class IndeedFullDetailsScraper:
    def __init__(self, headless=False):
        """Initialize Selenium driver"""
        options = uc.ChromeOptions()
        
        if headless:
            options.add_argument('--headless')
        
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--lang=es-ES')
        options.add_argument('--window-size=1920,1080')
        
        print("🚀 Initializing Chrome driver...")
        self.driver = uc.Chrome(options=options)
        self.driver.set_page_load_timeout(30)
        self.wait = WebDriverWait(self.driver, 10)
        print("✅ Driver ready!\n")
    
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
        
        # Parse specific dates
        months_map = {
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12,
            'jan': 1, 'apr': 4, 'aug': 8, 'dec': 12
        }
        
        for month_name, month_num in months_map.items():
            if month_name in date_str:
                parts = re.findall(r'\d+', date_str)
                if len(parts) >= 1:
                    day = int(parts[0])
                    year = int(parts[1]) if len(parts) > 1 and len(parts[1]) == 4 else datetime.now().year
                    return f"{year}-{month_num:02d}-{day:02d}"
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def extract_salary(self, text):
        """Extract salary information"""
        if not text:
            return {'salary_type': None, 'salary': None, 'max_salary': None}
        
        text_lower = text.lower()
        salary_data = {
            'salary_type': 'monthly',
            'salary': None,
            'max_salary': None
        }
        
        if 'hora' in text_lower or 'hour' in text_lower or '/hr' in text_lower:
            salary_data['salary_type'] = 'hourly'
        elif 'año' in text_lower or 'year' in text_lower or 'anual' in text_lower or '/yr' in text_lower:
            salary_data['salary_type'] = 'yearly'
        elif 'mes' in text_lower or 'month' in text_lower or '/mo' in text_lower:
            salary_data['salary_type'] = 'monthly'
        
        numbers = re.findall(r'[\d,]+(?:\.\d{2})?', text)
        if numbers:
            cleaned = [float(n.replace(',', '')) for n in numbers]
            salary_data['salary'] = cleaned[0]
            if len(cleaned) > 1:
                salary_data['max_salary'] = cleaned[1]
        
        return salary_data
    
    def extract_experience_from_text(self, text):
        """Extract experience requirements from text"""
        if not text:
            return None, None
        
        text_lower = text.lower()
        
        # Look for experience patterns
        exp_patterns = [
            r'(\d+)\+?\s*(años?|years?)\s*(?:de\s*)?(?:experiencia|experience)',
            r'(?:experiencia|experience)\s*(?:de\s*)?(\d+)\+?\s*(años?|years?)',
            r'(\d+)\s*-\s*(\d+)\s*(años?|years?)',
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
        
        # Check for keywords
        if any(word in text_lower for word in ['senior', 'sr.', 'lead', 'principal']):
            return '5+ years', 'senior'
        elif any(word in text_lower for word in ['junior', 'jr.', 'entry level', 'entry-level', 'sin experiencia']):
            return '0-2 years', 'entry'
        elif any(word in text_lower for word in ['mid', 'intermediate', 'intermedio']):
            return '2-5 years', 'mid'
        
        return None, None
    
    def extract_qualification(self, text):
        """Extract education qualification from text"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['phd', 'doctorado', 'doctorate', 'ph.d']):
            return 'doctorate'
        elif any(word in text_lower for word in ['maestría', 'master', 'msc', 'mba', "master's", 'postgrado']):
            return 'master'
        elif any(word in text_lower for word in ['licenciatura', 'bachelor', 'grado', 'universitario', 'university degree', "bachelor's"]):
            return 'bachelor'
        elif any(word in text_lower for word in ['técnico', 'technical', 'associate', 'diploma']):
            return 'associate'
        elif any(word in text_lower for word in ['secundaria', 'high school', 'bachillerato']):
            return 'high_school'
        
        return None
    
    def extract_job_type(self, text):
        """Extract job type from text"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        if 'tiempo completo' in text_lower or 'full time' in text_lower or 'full-time' in text_lower:
            return 'full-time'
        elif 'medio tiempo' in text_lower or 'part time' in text_lower or 'part-time' in text_lower:
            return 'part-time'
        elif 'temporal' in text_lower or 'temporary' in text_lower:
            return 'temporary'
        elif 'contrato' in text_lower or 'contract' in text_lower or 'contractor' in text_lower:
            return 'contract'
        elif 'internship' in text_lower or 'pasantía' in text_lower or 'intern' in text_lower:
            return 'internship'
        elif 'freelance' in text_lower or 'por proyecto' in text_lower:
            return 'freelance'
        
        return None
    
    def click_job_and_extract_details(self, job_element, job_data):
        """Click on a job and extract full details from the detail pane"""
        try:
            # Click the job card to open details
            job_element.click()
            time.sleep(random.uniform(1.5, 3))
            
            # Wait for detail pane to load
            try:
                self.wait.until(EC.presence_of_element_located((By.ID, "jobDescriptionText")))
            except:
                pass
            
            # Extract full description
            try:
                desc_elem = self.driver.find_element(By.ID, "jobDescriptionText")
                full_description = desc_elem.text.strip()
                job_data['description'] = full_description
                
                # Extract experience and qualification from description
                exp, career_level = self.extract_experience_from_text(full_description)
                if exp:
                    job_data['experience'] = exp
                if career_level:
                    job_data['career_level'] = career_level
                
                qualification = self.extract_qualification(full_description)
                if qualification:
                    job_data['qualification'] = qualification
                
                # Extract job type if not already found
                if not job_data['type']:
                    job_type = self.extract_job_type(full_description)
                    if job_type:
                        job_data['type'] = job_type
                
            except:
                pass
            
            # Extract company details from detail pane
            try:
                company_elem = self.driver.find_element(By.CSS_SELECTOR, '[data-company-name="true"]')
                if not job_data['company']:
                    job_data['company'] = company_elem.text.strip()
            except:
                pass
            
            # Extract full location/address
            try:
                location_selectors = [
                    'div[data-testid="jobsearch-JobInfoHeader-companyLocation"]',
                    'div.jobsearch-JobInfoHeader-subtitle-container div',
                    'div.jobsearch-CompanyInfoWithoutHeaderImage'
                ]
                
                for selector in location_selectors:
                    try:
                        loc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        loc_text = loc_elem.text.strip()
                        if loc_text and not job_data['location']:
                            job_data['location'] = loc_text
                            job_data['address'] = loc_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract salary from detail view
            try:
                salary_selectors = [
                    '#salaryInfoAndJobType',
                    'div[id*="salary"]',
                    'span[class*="salary"]'
                ]
                
                for selector in salary_selectors:
                    try:
                        salary_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        salary_text = salary_elem.text.strip()
                        if salary_text and not job_data['salary']:
                            salary_info = self.extract_salary(salary_text)
                            job_data.update(salary_info)
                            break
                    except:
                        continue
            except:
                pass
            
            # Check for "Urgently Hiring"
            try:
                urgent = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Urge contratar') or contains(text(), 'Urgently hiring') or contains(text(), 'contratación urgente')]")
                if urgent:
                    job_data['urgent'] = True
                    if 'urgent' not in job_data['tag']:
                        job_data['tag'].append('urgent')
            except:
                pass
            
            # Posted date from detail view
            try:
                date_elem = self.driver.find_element(By.CSS_SELECTOR, 'span.jobsearch-JobMetadataFooter-item span')
                date_text = date_elem.text.strip()
                if date_text and not job_data['posted_date']:
                    job_data['posted_date'] = self.parse_date(date_text)
            except:
                pass
            
            # Apply button URL
            try:
                apply_button = self.driver.find_element(By.CSS_SELECTOR, '#applyButtonLinkContainer a, button#indeedApplyButton')
                apply_url = apply_button.get_attribute('href')
                if apply_url:
                    job_data['apply_url'] = apply_url
                    
                    # Determine apply type
                    if 'indeed.com' in apply_url:
                        job_data['apply_type'] = 'indeed'
                    else:
                        job_data['apply_type'] = 'external'
            except:
                pass
            
            # Company logo from detail pane
            try:
                if not job_data['featured_image']:
                    logo_elem = self.driver.find_element(By.CSS_SELECTOR, 'img[alt*="logo"], img.jobsearch-CompanyAvatar-image')
                    logo_src = logo_elem.get_attribute('src')
                    if logo_src:
                        job_data['featured_image'] = logo_src
            except:
                pass
            
        except Exception as e:
            print(f"      ⚠️  Error extracting details: {e}")
    
    def extract_job_from_card(self, card):
        """Extract basic job data from a job card"""
        job_data = {
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
            job_data['job_id'] = card.get_attribute('data-jk')
            
            # Title and URL - try multiple selectors
            title_selectors = [
                'h2.jobTitle span',
                'h2.jobTitle a',
                'a.jcs-JobTitle',
                'span[id^="jobTitle-"]'
            ]
            
            for selector in title_selectors:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['title'] = title_elem.text.strip()
                    
                    # Try to get link
                    try:
                        if title_elem.tag_name == 'a':
                            job_data['apply_url'] = title_elem.get_attribute('href')
                        else:
                            link = card.find_element(By.CSS_SELECTOR, 'h2.jobTitle a, a.jcs-JobTitle')
                            job_data['apply_url'] = link.get_attribute('href')
                    except:
                        pass
                    
                    break
                except:
                    continue
            
            # Company
            company_selectors = [
                'span[data-testid="company-name"]',
                '.companyName',
                'span.companyName'
            ]
            
            for selector in company_selectors:
                try:
                    company_elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['company'] = company_elem.text.strip()
                    break
                except:
                    continue
            
            # Rating
            try:
                rating_elem = card.find_element(By.CSS_SELECTOR, '.ratingNumber, span[class*="rating"]')
                rating_text = rating_elem.text.strip()
                job_data['company_rating'] = float(rating_text)
            except:
                pass
            
            # Location
            location_selectors = [
                'div[data-testid="text-location"]',
                '.companyLocation',
                'div.companyLocation'
            ]
            
            for selector in location_selectors:
                try:
                    location_elem = card.find_element(By.CSS_SELECTOR, selector)
                    location_text = location_elem.text.strip()
                    job_data['location'] = location_text
                    job_data['address'] = location_text
                    break
                except:
                    continue
            
            # Salary
            try:
                salary_elem = card.find_element(By.CSS_SELECTOR, '.salary-snippet-container, .salary-snippet, span.salary')
                salary_text = salary_elem.text.strip()
                salary_info = self.extract_salary(salary_text)
                job_data.update(salary_info)
            except:
                pass
            
            # Snippet description
            try:
                snippet_elem = card.find_element(By.CSS_SELECTOR, '.job-snippet, ul.job-snippet')
                snippet_text = snippet_elem.text.strip()
                job_data['description'] = snippet_text
                
                # Detect job type from snippet
                job_type = self.extract_job_type(snippet_text)
                if job_type:
                    job_data['type'] = job_type
            except:
                pass
            
            # Posted date
            try:
                date_elem = card.find_element(By.CSS_SELECTOR, '.date, span.date')
                date_text = date_elem.text.strip()
                job_data['posted_date'] = self.parse_date(date_text)
            except:
                pass
            
            # Check for tags
            card_html = card.get_attribute('innerHTML').lower()
            
            if 'patrocinado' in card_html or 'sponsored' in card_html:
                job_data['featured'] = True
                job_data['tag'].append('sponsored')
            
            if 'urge contratar' in card_html or 'urgently' in card_html or 'urgente' in card_html:
                job_data['urgent'] = True
                job_data['tag'].append('urgent')
            
            if 'nuevo' in card_html or ('hoy' in (job_data['posted_date'] or '')):
                job_data['tag'].append('new')
            
            # Logo
            try:
                logo = card.find_element(By.CSS_SELECTOR, 'img[class*="logo"], img[class*="avatar"]')
                job_data['featured_image'] = logo.get_attribute('src')
            except:
                pass
            
        except Exception as e:
            print(f"      ⚠️  Error extracting from card: {e}")
        
        return job_data
    
    def scrape_jobs(self, search_url, max_pages=5, max_jobs=None, extract_full_details=True):
        """Scrape jobs with optional full details extraction"""
        all_jobs = []
        
        print(f"🔍 Starting scrape: {search_url}\n")
        print(f"📝 Extract full details: {'YES' if extract_full_details else 'NO'}\n")
        
        for page in range(max_pages):
            # Build URL
            if page == 0:
                url = search_url
            else:
                separator = '&' if '?' in search_url else '?'
                url = f"{search_url}{separator}start={page * 10}"
            
            print(f"📄 Page {page + 1}/{max_pages}")
            
            try:
                self.driver.get(url)
                time.sleep(random.uniform(2, 4))
                
                # Scroll to load content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(1)
                
                # Find job cards
                job_cards = None
                selectors = [
                    'div.job_seen_beacon',
                    'div[data-jk]',
                    'td.resultContent',
                    'li.css-5lfssm'
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
                    self.driver.save_screenshot(f"debug_page{page+1}.png")
                    with open(f"debug_page{page+1}.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    break
                
                # Extract jobs
                for idx, card in enumerate(job_cards, 1):
                    try:
                        # Extract basic info
                        job_data = self.extract_job_from_card(card)
                        
                        if not job_data['title']:
                            continue
                        
                        company = job_data['company'] or 'Unknown'
                        print(f"  {idx:2d}. {job_data['title'][:45]:45s} @ {company[:25]}")
                        
                        # Click and extract full details
                        if extract_full_details:
                            print(f"      🔍 Extracting full details...")
                            self.click_job_and_extract_details(card, job_data)
                        
                        all_jobs.append(job_data)
                        
                        # Check max jobs limit
                        if max_jobs and len(all_jobs) >= max_jobs:
                            print(f"\n✅ Reached max jobs limit ({max_jobs})")
                            return all_jobs
                        
                        # Small delay between jobs
                        time.sleep(random.uniform(0.5, 1.5))
                        
                    except Exception as e:
                        print(f"      ❌ Error: {e}")
                        continue
                
                print()  # Blank line between pages
                
                # Delay between pages
                if page < max_pages - 1:
                    delay = random.uniform(3, 6)
                    print(f"  ⏳ Waiting {delay:.1f}s before next page...\n")
                    time.sleep(delay)
                
            except Exception as e:
                print(f"  ❌ Page error: {e}")
                break
        
        return all_jobs
    
    def close(self):
        """Close browser"""
        print("\n🔒 Closing browser...")
        self.driver.quit()
    
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
                row = job.copy()
                for key, value in row.items():
                    if isinstance(value, list):
                        row[key] = ', '.join(map(str, value))
                writer.writerow(row)
        print(f"💾 Saved {len(jobs)} jobs to {filename}")


def main():
    print("="*70)
    print("INDEED COSTA RICA - FULL DETAILS JOB SCRAPER")
    print("="*70)
    print()
    
    # Client's URL
    search_url = "https://cr.indeed.com/jobs?q=&l=costa+rica&from=searchOnHP&vjk=d182fba1685af283"
    
    scraper = None
    try:
        # Initialize (set headless=True to hide browser)
        scraper = IndeedFullDetailsScraper(headless=False)
        
        # Scrape with full details
        jobs = scraper.scrape_jobs(
            search_url, 
            max_pages=5,
            max_jobs=None,  # None = get all jobs
            extract_full_details=True  # Set True for complete data
        )
        
        # Save results
        if jobs:
            print(f"\n{'='*70}")
            print(f"✅ Successfully scraped {len(jobs)} jobs!")
            print(f"{'='*70}\n")
            
            scraper.save_to_json(jobs, 'indeed_cr_complete_jobs.json')
            scraper.save_to_csv(jobs, 'indeed_cr_complete_jobs.csv')
            
            # Print statistics
            print("\n📊 STATISTICS:")
            print("-" * 70)
            print(f"Total jobs: {len(jobs)}")
            print(f"With full description: {sum(1 for j in jobs if j['description'] and len(j['description']) > 200)}")
            print(f"With salary info: {sum(1 for j in jobs if j['salary'])}")
            print(f"Urgent hiring: {sum(1 for j in jobs if j['urgent'])}")
            print(f"Featured/Sponsored: {sum(1 for j in jobs if j['featured'])}")
            
            # Sample job
            print("\n📋 SAMPLE JOB:")
            print("-" * 70)
            sample = jobs[0]
            print(f"Title: {sample['title']}")
            print(f"Company: {sample['company']} ({sample['company_rating']}★)" if sample['company_rating'] else f"Company: {sample['company']}")
            print(f"Location: {sample['location']}")
            print(f"Type: {sample['type']}")
            print(f"Experience: {sample['experience']} ({sample['career_level']})")
            print(f"Qualification: {sample['qualification']}")
            print(f"Salary: {sample['salary']} ({sample['salary_type']})" if sample['salary'] else "Salary: Not specified")
            print(f"Posted: {sample['posted_date']}")
            print(f"Tags: {', '.join(sample['tag'])}" if sample['tag'] else "Tags: None")
            print(f"Description: {sample['description'][:200]}..." if sample['description'] else "Description: N/A")
            print(f"URL: {sample['apply_url']}")
            print("-" * 70)
        else:
            print("\n❌ No jobs scraped. Check debug files.")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
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