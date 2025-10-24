"""
Indeed Costa Rica Complete Job Scraper with Full Details (nodriver + BeautifulSoup)

Requirements:
pip install nodriver beautifulsoup4 lxml

Run:
python indeed_arc_details_scraper.py
"""

import asyncio
import time
import random
import re
import json
import csv
import warnings
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

import nodriver as nd

warnings.filterwarnings("ignore", category=DeprecationWarning)


class IndeedFullDetailsScraper:
    def __init__(self, headless=False):
        # placeholders; actual browser/page started in async start()
        self.browser = None
        self.page = None
        self.headless = headless

    # -------------------------
    # Async startup / cloudflare
    # -------------------------
    async def start(self, start_url="https://cr.indeed.com/jobs?q=&l=costa+rica"):
        """Start nodriver browser and ensure the real page is loaded (no Cloudflare challenge)."""
        print("🚀 Starting nodriver browser...")
        self.browser = await nd.start()
        # open page
        self.page = await self.browser.get(start_url)
        print("🌐 Navigated to", start_url)

        # wait loop: check innerText for challenge or job markers
        max_attempts = 40
        for attempt in range(max_attempts):
            await asyncio.sleep(20 + random.random() * 1.5)
            try:
                inner_text = await self.page.evaluate("document.documentElement.innerText")
            except Exception:
                inner_text = ""

            text_low = (inner_text[:500] or "").lower()

            # print(text_low)

            # heuristics for Cloudflare / recaptcha
            if "verify you are human" in text_low or "cf-browser-verification" in text_low or "recaptcha" in text_low or "checking your browser" in text_low:
                print(f"⏳ Cloudflare/challenge detected (attempt {attempt+1}/{max_attempts}). refreshing...")
                try:
                    await self.page.reload()
                except Exception:
                    pass
                await asyncio.sleep(3 + random.random() * 3)
                continue

            # heuristics for real Indeed page (spanish headings or known markers)
            if "empleos en costa rica" in text_low:
                print("✅ Real Indeed page detected.")
                return True

            # falling back: check if there's a significant amount of text / HTML
            # html_len = len(await self.page.evaluate("document.documentElement.outerHTML") or "")
            # if html_len > 2000:
            #     print("✅ Page has content (len:", html_len, ") — proceeding.")
            #     return True

            # otherwise refresh and retry
            try:
                await self.page.reload()
            except Exception:
                pass

        # if reached here, give user a chance to manually solve in the opened browser
        print("❗ Reached wait limit. If a captcha is shown, please solve it in the opened browser.")
        # don't block indefinitely — let user press Enter to continue
        try:
            input("Press Enter after solving the captcha in the browser (or Ctrl+C to abort)...")
        except KeyboardInterrupt:
            raise
        return True

    # -------------------------
    # Utilities (copied/adapted)
    # -------------------------
    def extract_category(self, title, description):
        if not title and not description:
            return None
        text = f"{title or ''} {description or ''}".lower()
        categories = {
            'Desarrollo de TI/Software': [
                'software', 'developer', 'programming', 'engineer', 'web', 'mobile',
                'frontend', 'backend', 'fullstack', 'devops', 'cloud', 'java', 'python',
                'javascript', 'react', 'angular', 'node', 'php', 'dotnet', '.net',
                'desarrollo', 'programador', 'desarrollador', 'sistemas', 'typescript',
                'ruby', 'golang', 'kotlin', 'swift', 'android', 'ios', 'data scientist'
            ],
            'Servicio al cliente': [
                'customer service', 'call center', 'support', 'help desk', 'servicio al cliente',
                'atención al cliente', 'soporte', 'representante', 'agent', 'cliente',
                'atención', 'contact center', 'bpo'
            ],
            # (rest omitted for brevity — re-use your full categories mapping)
        }
        # Note: include all categories as in your original — truncated here for readability
        # Merge back the rest of category lists in real use
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        return 'General/Other'

    def parse_date(self, date_str):
        if not date_str:
            return None
        s = date_str.lower().strip()
        if 'hoy' in s or 'today' in s or 'just posted' in s:
            return datetime.now().strftime('%Y-%m-%d')
        if 'hace' in s or 'ago' in s:
            numbers = re.findall(r'\d+', s)
            if numbers:
                num = int(numbers[0])
                if 'hora' in s or 'hour' in s:
                    date = datetime.now()
                else:
                    date = datetime.now() - timedelta(days=num)
                return date.strftime('%Y-%m-%d')
        months_map = {
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12,
            'jan': 1, 'apr': 4, 'aug': 8, 'dec': 12
        }
        for month_name, month_num in months_map.items():
            if month_name in s:
                parts = re.findall(r'\d+', s)
                if len(parts) >= 1:
                    day = int(parts[0])
                    year = int(parts[1]) if len(parts) > 1 and len(parts[1]) == 4 else datetime.now().year
                    return f"{year}-{month_num:02d}-{day:02d}"
        return datetime.now().strftime('%Y-%m-%d')

    def extract_salary(self, text):
        if not text:
            return {'_job_salary_type': None, '_job_salary': None, '_job_max_salary': None}
        text_lower = text.lower()
        salary_data = {'_job_salary_type': 'monthly', '_job_salary': None, '_job_max_salary': None}
        if 'hora' in text_lower or 'hour' in text_lower or '/hr' in text_lower:
            salary_data['_job_salary_type'] = 'hora'
        elif 'año' in text_lower or 'year' in text_lower or 'anual' in text_lower or '/yr' in text_lower:
            salary_data['_job_salary_type'] = 'anual'
        elif 'mes' in text_lower or 'month' in text_lower or '/mo' in text_lower:
            salary_data['_job_salary_type'] = 'mensual'
        numbers = re.findall(r'[\d\.,]+(?:\.\d{2})?', text)
        if numbers:
            cleaned = []
            for n in numbers:
                n2 = n.replace('.', '').replace(',', '')
                try:
                    cleaned.append(float(n2))
                except Exception:
                    continue
            if cleaned:
                salary_data['_job_salary'] = cleaned[0]
                if len(cleaned) > 1:
                    salary_data['_job_max_salary'] = cleaned[1]
        return salary_data

    def extract_experience_from_text(self, text):
        if not text:
            return None, None
        s = text.lower()
        exp_patterns = [
            r'(\d+)\+?\s*(años?|years?)\s*(?:de\s*)?(?:experiencia|experience)',
            r'(?:experiencia|experience)\s*(?:de\s*)?(\d+)\+?\s*(años?|years?)',
            r'(\d+)\s*-\s*(\d+)\s*(años?|years?)',
        ]
        for pattern in exp_patterns:
            m = re.search(pattern, s)
            if m:
                years = int(m.group(1))
                if years >= 7:
                    return f"{years}+ años", 'sénior'
                elif years >= 3:
                    return f"{years}+ años", 'medio'
                elif years >= 1:
                    return f"{years}+ años", 'júnior'
                else:
                    return f"{years} años", 'entry'
        if any(w in s for w in ['senior', 'sr.', 'lead', 'principal']):
            return '5+ años', 'sénior'
        if any(w in s for w in ['junior', 'jr.', 'entry level', 'sin experiencia']):
            return '0-2 años', 'júnior'
        if any(w in s for w in ['mid', 'intermediate', 'intermedio']):
            return '2-5 años', 'medio'
        return None, None

    def extract_qualification(self, text):
        if not text:
            return None
        s = text.lower()
        if any(word in s for word in ['phd', 'doctorado', 'doctorate', 'ph.d']):
            return 'doctorado'
        if any(word in s for word in ['maestría', 'master', 'msc', 'mba', "master's"]):
            return 'maestro'
        if any(word in s for word in ['licenciatura', 'bachelor', 'grado', 'university degree', "bachelor's"]):
            return 'bachiller'
        if any(word in s for word in ['técnico', 'technical', 'associate', 'diploma']):
            return 'asociada'
        if any(word in s for word in ['secundaria', 'high school', 'bachillerato']):
            return 'escuela secundaria'
        return None

    def extract_job_type(self, text):
        if not text:
            return None
        s = text.lower()
        if 'tiempo completo' in s or 'full time' in s or 'full-time' in s:
            return 'tiempo completo'
        if 'medio tiempo' in s or 'part time' in s or 'part-time' in s:
            return 'medio tiempo'
        if 'temporal' in s or 'temporary' in s:
            return 'temporal'
        if 'contrato' in s or 'contract' in s:
            return 'contrato'
        if 'internship' in s or 'pasantía' in s or 'intern' in s:
            return 'internship'
        if 'freelance' in s or 'por proyecto' in s:
            return 'freelance'
        return None

    # -------------------------
    # Parsing helpers (BeautifulSoup)
    # -------------------------
    def extract_job_from_card_soup(self, card):
        """card is a BeautifulSoup tag for single job card"""
        job_data = {
            '_job_featured_image': None,
            '_job_title': None,
            '_job_featured': 0,
            '_job_filled': 0,
            '_job_urgent': 0,
            '_job_description': None,
            '_job_category': None,
            '_job_type': None,
            '_job_tag': 'Costa Rica-',
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

        # Title
        title = None
        # common selectors
        selectors = [
            ('a', 'h2.jobTitle span'),
            ('a', 'h2.jobTitle'),
            ('a', 'a.jcs-JobTitle'),
            ('a', 'a.tapItem')
        ]
        # Try generic patterns
        t = card.select_one('h2.jobTitle span') or card.select_one('h2.jobTitle') or card.select_one('a.jcs-JobTitle') or card.select_one('a.tapItem')
        if t:
            job_data['_job_title'] = t.get_text(strip=True)

        # Apply url
        link = card.select_one('a.tapItem') or card.select_one('a.jcs-JobTitle') or card.select_one('h2.jobTitle a')
        if link and link.has_attr('href'):
            href = link['href']
            # relative links on Indeed often start with /rc/ or /company/ or /viewjob
            if href.startswith('/'):
                href = 'https://cr.indeed.com' + href
            job_data['_job_apply_url'] = href

        # Location
        loc = card.select_one('div[data-testid="text-location"]') or card.select_one('.companyLocation') or card.select_one('.location')
        if loc:
            job_data['_job_location'] = loc.get_text(strip=True)
            job_data['_job_address'] = job_data['_job_location']

        # Salary (card-level)
        sal = card.select_one('.salary-snippet-container') or card.select_one('.salary-snippet') or card.select_one('span.salaryText') or card.select_one('div.salary')
        if sal:
            sal_text = sal.get_text(" ", strip=True)
            salary_info = self.extract_salary(sal_text)
            job_data.update(salary_info)

        # Snippet description
        snippet = card.select_one('.job-snippet') or card.select_one('.summary') or card.select_one('div.job-snippet')
        if snippet:
            snippet_text = snippet.get_text(" ", strip=True)
            job_data['_job_description'] = snippet_text
            jt = self.extract_job_type(snippet_text)
            if jt:
                job_data['_job_type'] = jt

        # Tags: sponsored/urgent/new
        inner = str(card).lower()
        if 'patrocinado' in inner or 'sponsored' in inner:
            job_data['_job_featured'] = 1
            job_data['_job_tag'].append('sponsored')
        if 'urge contratar' in inner or 'urgently' in inner or 'urgente' in inner:
            job_data['_job_urgent'] = 1
            job_data['_job_tag'].append('urgent')
        if 'nuevo' in inner or 'nuevo' in (job_data['_job_description'] or '').lower():
            job_data['_job_tag'].append('new')

        # Logo heuristics inside card
        img = card.select_one('img')
        if img and img.has_attr('src'):
            src = img['src']
            if src and 'indeed' not in src.lower() and len(src) > 20:
                job_data['_job_featured_image'] = src

        return job_data

    # -------------------------
    # Main scraping logic
    # -------------------------
    async def scrape_jobs(self, search_url, max_pages=3, max_jobs=None, extract_full_details=True):
        all_jobs = []
        print(f"🔍 Starting scrape: {search_url}")
        for page_no in range(max_pages):
            if page_no == 0:
                url = search_url
            else:
                sep = '&' if '?' in search_url else '?'
                url = f"{search_url}{sep}start={page_no * 10}"

            print(f"\n📄 Page {page_no + 1}/{max_pages}: {url}")
            try:
                await self.page.get(url)
                # wait a bit for JS to render
                await asyncio.sleep(3 + random.random() * 2)

                # optional extra scrolling to load lazy content
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight/3);")
                await asyncio.sleep(0.7 + random.random() * 1.5)
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(1 + random.random() * 1.5)

                html = await self.page.evaluate("document.documentElement.outerHTML")
                soup = BeautifulSoup(html, "lxml")

                # Try multiple selectors for job cards
                card_selectors = [
                    'a.tapItem',            # common modern selector
                    'div.job_seen_beacon',
                    'div[data-jk]',
                    'td.resultContent',
                    'li.css-5lfssm'
                ]
                job_cards = []
                for sel in card_selectors:
                    found = soup.select(sel)
                    if found:
                        job_cards = found
                        break

                if not job_cards:
                    print("  ⚠️ No job cards found on this page — saving debug and continuing.")
                    with open(f"debug_page_{page_no+1}.html", "w", encoding="utf-8") as f:
                        f.write(html)
                    # continue to next page or stop
                    break

                print(f"  ✅ Found {len(job_cards)} job card elements (using selector).")

                for idx, card in enumerate(job_cards, start=1):
                    try:
                        job_data = self.extract_job_from_card_soup(card)
                        if not job_data['_job_title']:
                            continue

                        print(f"  {idx:3d}. {job_data['_job_title'][:80]:80s}")

                        # If requested, fetch detail page to get full description
                        if extract_full_details and job_data['_job_apply_url']:
                            # small randomized delay
                            await asyncio.sleep(0.6 + random.random() * 0.8)
                            try:
                                # navigate to detail page (keeps same page)
                                await self.page.get(job_data['_job_apply_url'])
                                await asyncio.sleep(2 + random.random() * 1.5)
                                detail_html = await self.page.evaluate("document.documentElement.outerHTML")
                                detail_soup = BeautifulSoup(detail_html, "lxml")

                                # description selectors
                                desc = detail_soup.select_one('#jobDescriptionText') or detail_soup.select_one('div#jobDescriptionText') or detail_soup.select_one('.jobsearch-JobComponent-description') or detail_soup.select_one('.jobsearch-jobDescriptionText')
                                if desc:
                                    full_desc = desc.get_text("\n", strip=True)
                                    job_data['_job_description'] = full_desc

                                    # extract experience / qualification / type / category
                                    exp, lev = self.extract_experience_from_text(full_desc)
                                    if exp:
                                        job_data['_job_experience'] = exp
                                    if lev:
                                        job_data['_job_career_level'] = lev
                                    qual = self.extract_qualification(full_desc)
                                    if qual:
                                        job_data['_job_qualification'] = qual
                                    jt = self.extract_job_type(full_desc)
                                    if jt and not job_data['_job_type']:
                                        job_data['_job_type'] = jt
                                    cat = self.extract_category(job_data['_job_title'], full_desc)
                                    if cat:
                                        job_data['_job_category'] = cat

                                # salary in detail page
                                sal = detail_soup.select_one('#salaryInfoAndJobType') or detail_soup.select_one('div.salary') or detail_soup.select_one('span[class*="salary"]')
                                if sal:
                                    info = self.extract_salary(sal.get_text(" ", strip=True))
                                    job_data.update(info)

                                # try company logo on detail page
                                logo = detail_soup.select_one('div[data-testid="inlineHeader-companyLogo"] img') or detail_soup.select_one('.jobsearch-CompanyAvatar-image') or detail_soup.select_one('img[alt*="logo"]')
                                if logo and logo.has_attr('src'):
                                    src = logo['src']
                                    if 'indeed' not in src.lower() and len(src) > 20:
                                        job_data['_job_featured_image'] = src

                                # optionally return to listing page (fast)
                                await self.page.get(url)
                                await asyncio.sleep(0.8 + random.random() * 0.8)
                            except Exception as e:
                                # On error, continue - we don't want to stop the whole run
                                print(f"      ⚠️ Detail page error: {e}")

                        # fallback category detection
                        if not job_data['_job_category']:
                            job_data['_job_category'] = self.extract_category(job_data['_job_title'], job_data['_job_description'])

                        all_jobs.append(job_data)
                        if max_jobs and len(all_jobs) >= max_jobs:
                            print(f"\n✅ Reached max jobs limit ({max_jobs})")
                            return all_jobs

                        # polite small delay
                        await asyncio.sleep(0.3 + random.random() * 0.9)
                    except Exception as e:
                        print(f"    ❌ Error extracting job card: {e}")
                        continue

                # delay between pages
                if page_no < max_pages - 1:
                    delay = random.uniform(2.0, 5.0)
                    print(f"  ⏳ Waiting {delay:.1f}s before next page...")
                    await asyncio.sleep(delay)

            except Exception as e:
                print(f"  ❌ Page error: {e}")
                break

        return all_jobs

    # -------------------------
    # Save / close helpers
    # -------------------------
    def save_to_json(self, jobs, filename='indeed_jobs.json'):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, ensure_ascii=False, indent=2)
            print(f"💾 Saved {len(jobs)} jobs to {filename}")
        except Exception as e:
            print("⚠️ Save JSON error:", e)

    def save_to_csv(self, jobs, filename='indeed_jobs.csv'):
        if not jobs:
            print("⚠️ No jobs to save")
            return
        try:
            keys = list(jobs[0].keys())
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for job in jobs:
                    row = job.copy()
                    for k, v in row.items():
                        if isinstance(v, list):
                            row[k] = ', '.join(map(str, v))
                    writer.writerow(row)
            print(f"💾 Saved {len(jobs)} jobs to {filename}")
        except Exception as e:
            print("⚠️ Save CSV error:", e)

    async def close(self):
        if self.browser:
            try:
                await self.browser.stop()
            except Exception:
                pass


# -------------------------
# Runner
# -------------------------
def main():
    search_url = "https://cr.indeed.com/jobs?q=&l=costa+rica&from=searchOnHP"

    # Force headless mode for GitHub Actions or servers
    scraper = IndeedFullDetailsScraper(headless=True)

    async def arun():
        try:
            try:
                await scraper.start(start_url=search_url)
            except Exception as e:
                print(f"⚠️ Browser start failed: {e}. Retrying once...")
                await asyncio.sleep(5)
                await scraper.close()
                await scraper.start(start_url=search_url)

            jobs = await scraper.scrape_jobs(
                search_url,
                max_pages=3,
                max_jobs=None,
                extract_full_details=True,
            )

            if jobs:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                json_fn = f"indeed_cr_jobs_{timestamp}.json"
                csv_fn = f"indeed_cr_jobs_{timestamp}.csv"
                scraper.save_to_json(jobs, json_fn)
                scraper.save_to_csv(jobs, csv_fn)
                print(f"\n✅ Scraped {len(jobs)} jobs. Files: {json_fn}, {csv_fn}")
            else:
                print("\n❌ No jobs scraped — check debug files.")
        except Exception as e:
            print(f"🔥 Fatal error during scrape: {e}")
        finally:
            try:
                await scraper.close()
            except Exception as e:
                print(f"⚠️ Error closing browser: {e}")
            print("\n🔒 Browser closed.\n✅ Done!")

    nd.loop().run_until_complete(arun())
if __name__ == "__main__":
    main()
