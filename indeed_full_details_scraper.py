"""
Indeed Costa Rica Complete Job Scraper with Full Details
Updated version with _job_ prefix and category extraction

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
import warnings
from datetime import datetime, timedelta


default_deadline = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
# print(default_deadline)
# Suppress warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

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
    
    def extract_category(self, title, description):
        """Extract job category from title and description keywords"""
        if not title and not description:
            return None
        
        text = f"{title or ''} {description or ''}".lower()
        
        # Define category keywords
        categories = {
            'IT/Software Development': [
                'software', 'developer', 'programming', 'engineer', 'web', 'mobile',
                'frontend', 'backend', 'fullstack', 'devops', 'cloud', 'java', 'python',
                'javascript', 'react', 'angular', 'node', 'php', 'dotnet', '.net',
                'desarrollo', 'programador', 'desarrollador', 'sistemas', 'typescript',
                'ruby', 'golang', 'kotlin', 'swift', 'android', 'ios', 'data scientist'
            ],
            'Customer Service': [
                'customer service', 'call center', 'support', 'help desk', 'servicio al cliente',
                'atención al cliente', 'soporte', 'representante', 'agent', 'cliente',
                'atención', 'contact center', 'bpo'
            ],
            'Sales/Marketing': [
                'sales', 'marketing', 'ventas', 'comercial', 'business development',
                'account manager', 'vendedor', 'mercadeo', 'publicidad', 'digital marketing',
                'seo', 'sem', 'social media', 'ecommerce', 'e-commerce', 'brand'
            ],
            'Finance/Accounting': [
                'accountant', 'finance', 'accounting', 'contador', 'contabilidad', 'finanzas',
                'auditor', 'financial', 'cpa', 'bookkeeper', 'payroll', 'tax', 'treasury',
                'banking', 'banco', 'inversiones', 'budget'
            ],
            'Human Resources': [
                'human resources', 'hr', 'recruiter', 'recursos humanos', 'reclutamiento',
                'recruitment', 'talent', 'talento', 'hiring', 'payroll', 'compensation',
                'benefits', 'culture', 'employee relations'
            ],
            'Administrative': [
                'administrative', 'assistant', 'secretary', 'office', 'receptionist',
                'administrativo', 'asistente', 'secretaria', 'oficina', 'recepcionista',
                'clerk', 'data entry', 'coordinator'
            ],
            'Healthcare': [
                'nurse', 'doctor', 'medical', 'health', 'healthcare', 'enfermera',
                'médico', 'salud', 'hospital', 'clinic', 'pharmacy', 'farmacia',
                'dentist', 'therapist', 'caregiver'
            ],
            'Education/Training': [
                'teacher', 'professor', 'education', 'training', 'instructor', 'tutor',
                'maestro', 'profesor', 'educación', 'capacitación', 'formación',
                'academic', 'learning', 'curriculum'
            ],
            'Engineering': [
                'civil engineer', 'mechanical', 'electrical', 'industrial engineer',
                'ingeniero', 'ingeniería', 'técnico', 'maintenance', 'mantenimiento',
                'manufacturing engineer', 'quality engineer', 'process engineer'
            ],
            'Design/Creative': [
                'designer', 'graphic', 'ux', 'ui', 'creative', 'diseñador', 'diseño',
                'gráfico', 'creativo', 'photoshop', 'illustrator', 'figma', 'sketch',
                'art director', 'visual', 'branding'
            ],
            'Logistics/Supply Chain': [
                'logistics', 'supply chain', 'warehouse', 'inventory', 'logística',
                'cadena de suministro', 'bodega', 'almacén', 'inventario', 'shipping',
                'procurement', 'purchasing', 'distribution', 'freight'
            ],
            'Management': [
                'manager', 'director', 'supervisor', 'lead', 'gerente', 'jefe',
                'coordinador', 'coordinator', 'chief', 'head', 'vp', 'vice president',
                'executive', 'ceo', 'cto', 'cfo'
            ],
            'Hospitality/Tourism': [
                'hotel', 'restaurant', 'tourism', 'hospitality', 'chef', 'cook',
                'turismo', 'hostelería', 'cocinero', 'camarero', 'waiter', 'bartender',
                'front desk', 'housekeeping', 'concierge'
            ],
            'Legal': [
                'lawyer', 'attorney', 'legal', 'abogado', 'jurídico', 'paralegal',
                'compliance', 'contracts', 'litigation', 'corporate law'
            ],
            'Manufacturing/Production': [
                'production', 'manufacturing', 'operator', 'assembly', 'fabrication',
                'producción', 'manufactura', 'operador', 'ensamblaje', 'planta',
                'factory', 'plant', 'cnc', 'machinist'
            ],
            'Data/Analytics': [
                'data analyst', 'data science', 'analytics', 'business intelligence',
                'bi', 'tableau', 'power bi', 'sql', 'database', 'big data',
                'machine learning', 'estadística', 'análisis'
            ],
            'Quality Assurance': [
                'qa', 'quality assurance', 'tester', 'testing', 'quality control',
                'calidad', 'pruebas', 'qc', 'inspector'
            ],
            'Security': [
                'security', 'seguridad', 'guard', 'vigilante', 'cybersecurity',
                'information security', 'infosec', 'safety'
            ]
        }
        
        # Check each category
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
            return {'_job_salary_type': None, '_job_salary': None, '_job_max_salary': None}
        
        text_lower = text.lower()
        salary_data = {
            '_job_salary_type': 'monthly',
            '_job_salary': None,
            '_job_max_salary': None
        }
        
        if 'hora' in text_lower or 'hour' in text_lower or '/hr' in text_lower:
            salary_data['_job_salary_type'] = 'hourly'
        elif 'año' in text_lower or 'year' in text_lower or 'anual' in text_lower or '/yr' in text_lower:
            salary_data['_job_salary_type'] = 'yearly'
        elif 'mes' in text_lower or 'month' in text_lower or '/mo' in text_lower:
            salary_data['_job_salary_type'] = 'monthly'
        
        numbers = re.findall(r'[\d,]+(?:\.\d{2})?', text)
        if numbers:
            cleaned = [float(n.replace(',', '')) for n in numbers]
            salary_data['_job_salary'] = cleaned[0]
            if len(cleaned) > 1:
                salary_data['_job_max_salary'] = cleaned[1]
        
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
                job_data['_job_description'] = full_description
                
                # Extract category from description
                category = self.extract_category(job_data['_job_title'], full_description)
                if category:
                    job_data['_job_category'] = category
                
                # Extract experience and qualification from description
                exp, career_level = self.extract_experience_from_text(full_description)
                if exp:
                    job_data['_job_experience'] = exp
                if career_level:
                    job_data['_job_career_level'] = career_level
                
                qualification = self.extract_qualification(full_description)
                if qualification:
                    job_data['_job_qualification'] = qualification
                
                # Extract job type if not already found
                if not job_data['_job_type']:
                    job_type = self.extract_job_type(full_description)
                    if job_type:
                        job_data['_job_type'] = job_type
                
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
                        if loc_text and not job_data['_job_location']:
                            job_data['_job_location'] = loc_text
                            job_data['_job_address'] = loc_text
                            job_data['_job_map_location'] = loc_text
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
                        if salary_text and not job_data['_job_salary']:
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
                    job_data['_job_urgent'] = 1
                    if 'urgent' not in job_data['_job_tag']:
                        job_data['_job_tag'].append('urgent')
            except:
                pass
            
            # Apply button URL
            try:
                apply_button = self.driver.find_element(By.CSS_SELECTOR, '#applyButtonLinkContainer a, button#indeedApplyButton')
                apply_url = apply_button.get_attribute('href')
                if apply_url:
                    job_data['_job_apply_url'] = apply_url
                    
                    # Determine apply type
                    if 'indeed.com' in apply_url:
                        job_data['_job_apply_type'] = 'indeed'
                    else:
                        job_data['_job_apply_type'] = 'external'
            except:
                pass
            
            # Company logo from detail pane - try multiple selectors
            try:
                if not job_data['_job_featured_image']:
                    logo_selectors = [
                        'img[alt*="logo"]',
                        'img[alt*="Logo"]',
                        'img.jobsearch-CompanyAvatar-image',
                        'div[data-testid="inlineHeader-companyLogo"] img',
                        'div.jobsearch-InlineCompanyRating img',
                        'div.jobsearch-CompanyInfoWithoutHeaderImage img',
                        'img[class*="CompanyAvatar"]',
                        'img[class*="company"]',
                        'div[class*="CompanyInfo"] img'
                    ]
                    
                    for selector in logo_selectors:
                        try:
                            logo_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                            logo_src = logo_elem.get_attribute('src')
                            # Filter out small icons and Indeed default images
                            if logo_src and 'indeed' not in logo_src.lower() and len(logo_src) > 20:
                                job_data['_job_featured_image'] = logo_src
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
            '_job_tag': 'Costa Rica',
            '_job_expiry_date': None,
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
            '_job_application_deadline_date': None,
            '_job_address': None,
            '_job_location': None,
            '_job_map_location': None
        }
        
        try:
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
                    job_data['_job_title'] = title_elem.text.strip()
                    
                    # Try to get link
                    try:
                        if title_elem.tag_name == 'a':
                            job_data['_job_apply_url'] = title_elem.get_attribute('href')
                        else:
                            link = card.find_element(By.CSS_SELECTOR, 'h2.jobTitle a, a.jcs-JobTitle')
                            job_data['_job_apply_url'] = link.get_attribute('href')
                    except:
                        pass
                    
                    break
                except:
                    continue
            
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
                    job_data['_job_location'] = location_text
                    job_data['_job_address'] = location_text
                    job_data['_job_map_location'] = location_text
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
                job_data['_job_description'] = snippet_text
                
                # Detect job type from snippet
                job_type = self.extract_job_type(snippet_text)
                if job_type:
                    job_data['_job_type'] = job_type
            except:
                pass
            
            # Check for tags
            card_html = card.get_attribute('innerHTML').lower()
            
            if 'patrocinado' in card_html or 'sponsored' in card_html:
                job_data['_job_featured'] = 1
                job_data['_job_tag'].append('sponsored')
            
            if 'urge contratar' in card_html or 'urgently' in card_html or 'urgente' in card_html:
                job_data['_job_urgent'] = 1
                job_data['_job_tag'].append('urgent')
            
            if 'nuevo' in card_html:
                job_data['_job_tag'].append('new')
            
            # Logo - try multiple selectors
            logo_selectors = [
                'img[class*="logo"]',
                'img[class*="avatar"]',
                'img[data-testid*="company"]',
                'img.company-logo',
                'div.company-logo img',
                'td.companyInfo img',
                'img[alt*="logo"]',
                'img[alt*="Logo"]',
                '.companyLogo img',
                'img'  # Last resort - any image in card
            ]
            
            for selector in logo_selectors:
                try:
                    logo = card.find_element(By.CSS_SELECTOR, selector)
                    logo_src = logo.get_attribute('src')
                    # Filter out placeholder/icon images
                    if logo_src and 'indeed' not in logo_src.lower() and len(logo_src) > 20:
                        job_data['_job_featured_image'] = logo_src
                        break
                except:
                    continue
            
        except Exception as e:
            print(f"      ⚠️  Error extracting from card: {e}")
        
        return job_data
    
    def scrape_jobs(self, search_url, max_pages=5, max_jobs=None, extract_full_details=True):
        """Scrape jobs with optional full details extraction"""
        all_jobs = []
        
        print(f"🔍 Starting scrape: {search_url}\n")
        print(f"📋 Extract full details: {'YES' if extract_full_details else 'NO'}\n")
        
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
                        
                        if not job_data['_job_title']:
                            continue
                        
                        print(f"  {idx:2d}. {job_data['_job_title'][:50]:50s}")
                        
                        # Click and extract full details
                        if extract_full_details:
                            print(f"      🔍 Extracting full details...")
                            self.click_job_and_extract_details(card, job_data)
                            
                            # Additional logo extraction attempt if still null
                            if not job_data['_job_featured_image']:
                                try:
                                    # Try to find any company image on the page
                                    all_images = self.driver.find_elements(By.TAG_NAME, 'img')
                                    for img in all_images:
                                        src = img.get_attribute('src')
                                        alt = img.get_attribute('alt') or ''
                                        # Look for company-related images
                                        if src and any(keyword in alt.lower() for keyword in ['logo', 'company', 'employer']):
                                            if 'indeed' not in src.lower() and len(src) > 20:
                                                job_data['_job_featured_image'] = src
                                                break
                                except:
                                    pass
                        
                        # Extract category if still None
                        if not job_data['_job_category']:
                            category = self.extract_category(job_data['_job_title'], job_data['_job_description'])
                            job_data['_job_category'] = category
                        
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
        try:
            self.driver.quit()
        except Exception as e:
            # Ignore cleanup errors on Windows
            pass
    
    def save_to_json(self, jobs, filename='indeed_jobs.json'):
        """Save to JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, ensure_ascii=False, indent=2)
            print(f"💾 Saved {len(jobs)} jobs to {filename}")
        except PermissionError:
            print(f"⚠️  Cannot save to {filename} (file is open). Trying alternative filename...")
            alt_filename = filename.replace('.json', f'_{int(time.time())}.json')
            with open(alt_filename, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, ensure_ascii=False, indent=2)
            print(f"💾 Saved {len(jobs)} jobs to {alt_filename}")
    
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
        except PermissionError:
            print(f"⚠️  Cannot save to {filename} (file is open in another program)")
            print(f"💡 Please close the file and run the script again, or it will save with timestamp")
            alt_filename = filename.replace('.csv', f'_{int(time.time())}.csv')
            keys = jobs[0].keys()
            with open(alt_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for job in jobs:
                    row = job.copy()
                    for key, value in row.items():
                        if isinstance(value, list):
                            row[key] = ', '.join(map(str, value))
                    writer.writerow(row)
            print(f"💾 Saved {len(jobs)} jobs to {alt_filename}")


def main():
    print("="*70)
    print("INDEED COSTA RICA - FULL DETAILS JOB SCRAPER")
    print("="*70)
    print()
    
    # Client's URL
    search_url = "https://cr.indeed.com/jobs?q=&l=costa+rica&from=searchOnHP&vjk=8223ee513792bd50"
    
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
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_filename = f'indeed_cr_jobs_{timestamp}.json'
            csv_filename = f'indeed_cr_jobs_{timestamp}.csv'
            
            scraper.save_to_json(jobs, json_filename)
            scraper.save_to_csv(jobs, csv_filename)
            
            # Print statistics
            print("\n📊 STATISTICS:")
            print("-" * 70)
            print(f"Total jobs: {len(jobs)}")
            print(f"With full description: {sum(1 for j in jobs if j['_job_description'] and len(j['_job_description']) > 200)}")
            print(f"With salary info: {sum(1 for j in jobs if j['_job_salary'])}")
            print(f"Urgent hiring: {sum(1 for j in jobs if j['_job_urgent'] == 1)}")
            print(f"Featured/Sponsored: {sum(1 for j in jobs if j['_job_featured'] == 1)}")
            
            # Category breakdown
            categories = {}
            for job in jobs:
                cat = job['_job_category'] or 'Unknown'
                categories[cat] = categories.get(cat, 0) + 1
            
            print("\n📂 CATEGORIES:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"  {cat}: {count}")
            
            # Job type breakdown
            job_types = {}
            for job in jobs:
                jtype = job['_job_type'] or 'Not specified'
                job_types[jtype] = job_types.get(jtype, 0) + 1
            
            print("\n💼 JOB TYPES:")
            for jtype, count in sorted(job_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {jtype}: {count}")
            
            # Career level breakdown
            career_levels = {}
            for job in jobs:
                level = job['_job_career_level'] or 'Not specified'
                career_levels[level] = career_levels.get(level, 0) + 1
            
            print("\n📈 CAREER LEVELS:")
            for level, count in sorted(career_levels.items(), key=lambda x: x[1], reverse=True):
                print(f"  {level}: {count}")
            
            # Salary type breakdown
            salary_types = {}
            for job in jobs:
                if job['_job_salary']:
                    stype = job['_job_salary_type'] or 'Not specified'
                    salary_types[stype] = salary_types.get(stype, 0) + 1
            
            if salary_types:
                print("\n💰 SALARY TYPES:")
                for stype, count in sorted(salary_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {stype}: {count}")
            
            # Sample job
            print("\n📋 SAMPLE JOB:")
            print("-" * 70)
            sample = jobs[0]
            print(f"Title: {sample['_job_title']}")
            print(f"Category: {sample['_job_category']}")
            print(f"Location: {sample['_job_location']}")
            print(f"Address: {sample['_job_address']}")
            print(f"Type: {sample['_job_type']}")
            print(f"Experience: {sample['_job_experience']} ({sample['_job_career_level']})")
            print(f"Qualification: {sample['_job_qualification']}")
            
            if sample['_job_salary']:
                salary_range = f"{sample['_job_salary']}"
                if sample['_job_max_salary']:
                    salary_range += f" - {sample['_job_max_salary']}"
                print(f"Salary: {salary_range} ({sample['_job_salary_type']})")
            else:
                print(f"Salary: Not specified")
            
            print(f"Featured: {sample['_job_featured']} | Urgent: {sample['_job_urgent']} | Filled: {sample['_job_filled']}")
            print(f"Apply Type: {sample['_job_apply_type']}")
            print(f"Tags: {', '.join(sample['_job_tag'])}" if sample['_job_tag'] else "Tags: None")
            
            if sample['_job_description']:
                desc_preview = sample['_job_description'][:300].replace('\n', ' ')
                print(f"Description: {desc_preview}...")
            else:
                print(f"Description: N/A")
            
            print(f"Apply URL: {sample['_job_apply_url']}")
            
            if sample['_job_featured_image']:
                print(f"Logo: {sample['_job_featured_image'][:80]}...")
            
            print("-" * 70)
            
            # Export summary
            print("\n📦 EXPORTED FILES:")
            print("-" * 70)
            print(f"  ✅ {json_filename}")
            print(f"  ✅ {csv_filename}")
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
            try:
                scraper.close()
            except:
                pass  # Ignore any cleanup errors
        print("\n✅ Done!")


if __name__ == "__main__":
    main()