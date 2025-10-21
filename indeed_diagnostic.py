"""
Indeed Diagnostic Tool
Opens the page and analyzes what's actually there
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import re

def diagnose_indeed_page():
    print("="*70)
    print("INDEED PAGE DIAGNOSTIC")
    print("="*70)
    print()
    
    # Initialize browser
    print("🚀 Starting browser...")
    options = uc.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = uc.Chrome(options=options)
    
    try:
        # Load the page
        url = "https://cr.indeed.com/jobs?q=&l=costa+rica&from=searchOnHP"
        print(f"📡 Loading: {url}\n")
        driver.get(url)
        
        # Wait for user to see page
        print("⏸️  PAUSED - Browser will stay open for 10 seconds")
        print("   Look at the browser window - do you see jobs?")
        time.sleep(10)
        
        # Get page info
        print("\n" + "="*70)
        print("PAGE ANALYSIS")
        print("="*70)
        
        # Current URL
        current_url = driver.current_url
        print(f"\n📍 Current URL: {current_url}")
        
        # Check for redirects or blocks
        if 'google.com/sorry' in current_url:
            print("❌ BLOCKED - Google CAPTCHA detected")
            print("   Solution: Use residential proxy or VPN")
            return
        
        if 'captcha' in current_url.lower():
            print("❌ BLOCKED - CAPTCHA detected")
            return
        
        # Page title
        print(f"📄 Page Title: {driver.title}")
        
        # Get page source
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Save full HTML
        with open('diagnostic_full_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("\n💾 Saved: diagnostic_full_page.html")
        
        # Take screenshot
        driver.save_screenshot('diagnostic_screenshot.png')
        print("📸 Saved: diagnostic_screenshot.png")
        
        # Look for common Indeed elements
        print("\n" + "-"*70)
        print("ELEMENT SEARCH RESULTS")
        print("-"*70)
        
        searches = {
            'div.job_seen_beacon': 'Standard job cards',
            'div[data-jk]': 'Jobs with data-jk attribute',
            'td.resultContent': 'Result content cells',
            'li.css-5lfssm': 'List item jobs',
            'div.slider_item': 'Slider items',
            'h2.jobTitle': 'Job titles (h2)',
            'span.companyName': 'Company names',
            'a[href*="/viewjob"]': 'View job links',
            'a[href*="jk="]': 'Job key links',
        }
        
        for selector, description in searches.items():
            elements = soup.select(selector)
            print(f"\n{selector:30s} -> {len(elements):3d} found ({description})")
            
            if elements and len(elements) > 0:
                # Show first example
                first = elements[0]
                print(f"   Sample: {str(first)[:150]}...")
        
        # Look for any links that might be jobs
        print("\n" + "-"*70)
        print("ALL LINKS ANALYSIS")
        print("-"*70)
        
        all_links = soup.find_all('a', href=True)
        print(f"\nTotal links found: {len(all_links)}")
        
        job_related_links = []
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if any(keyword in href for keyword in ['/viewjob', 'jk=', '/pagead/', '/rc/clk']):
                job_related_links.append((text[:60], href[:100]))
        
        if job_related_links:
            print(f"\n✅ Found {len(job_related_links)} potential job links:\n")
            for idx, (text, href) in enumerate(job_related_links[:10], 1):
                print(f"{idx:2d}. {text:60s}")
                print(f"    {href}")
        else:
            print("\n❌ No job-related links found")
        
        # Look for common job text
        print("\n" + "-"*70)
        print("TEXT CONTENT ANALYSIS")
        print("-"*70)
        
        page_text = soup.get_text().lower()
        
        keywords = ['empleos', 'jobs', 'trabajo', 'vacante', 'company', 'empresa', 'salary', 'salario']
        print("\nKeyword presence:")
        for keyword in keywords:
            count = page_text.count(keyword)
            print(f"  '{keyword}': {count} times")
        
        # Look for specific job titles we know exist
        print("\n" + "-"*70)
        print("KNOWN JOB TITLES CHECK")
        print("-"*70)
        
        known_titles = [
            'Fire Alarm Engineer',
            'Spanish Interpreter',
            'Medical Coordinator',
            'Sales Representative',
            'Engineer'
        ]
        
        print("\nSearching for known job titles:")
        for title in known_titles:
            if title.lower() in page_text:
                print(f"  ✅ Found: {title}")
                
                # Find the context
                idx = page_text.find(title.lower())
                context = page_text[max(0, idx-100):idx+100]
                print(f"     Context: ...{context}...")
            else:
                print(f"  ❌ Not found: {title}")
        
        # Check for anti-bot messages
        print("\n" + "-"*70)
        print("ANTI-BOT / ERROR DETECTION")
        print("-"*70)
        
        error_indicators = [
            'captcha', 'robot', 'automated', 'suspicious activity',
            'blocked', 'access denied', 'error', 'verificación'
        ]
        
        found_errors = []
        for indicator in error_indicators:
            if indicator in page_text:
                found_errors.append(indicator)
        
        if found_errors:
            print(f"\n⚠️  WARNING: Found these indicators: {', '.join(found_errors)}")
        else:
            print("\n✅ No anti-bot messages detected")
        
        # Final recommendations
        print("\n" + "="*70)
        print("RECOMMENDATIONS")
        print("="*70)
        
        if not job_related_links and 'empleos' not in page_text:
            print("\n❌ PROBLEM: Page doesn't contain job listings")
            print("\nPossible causes:")
            print("  1. Indeed is blocking automated access")
            print("  2. Wrong URL or region restrictions")
            print("  3. Page requires interaction (clicking, scrolling)")
            print("\nSolutions:")
            print("  ✓ Try with a VPN to Costa Rica")
            print("  ✓ Use residential proxy")
            print("  ✓ Add more human-like delays and interactions")
            print("  ✓ Try Indeed RSS feeds instead")
        elif job_related_links:
            print("\n✅ GOOD: Found job-related content")
            print(f"   Found {len(job_related_links)} potential jobs")
            print("\nNext steps:")
            print("  ✓ Use the selectors that found jobs")
            print("  ✓ Extract data from those elements")
        
        print("\n" + "="*70)
        print("Check the files created:")
        print("  - diagnostic_full_page.html (full page HTML)")
        print("  - diagnostic_screenshot.png (what the page looks like)")
        print("="*70)
        
        # Keep browser open for inspection
        print("\n⏸️  Browser will stay open for 30 seconds...")
        print("   You can manually inspect the page")
        print("   Press Ctrl+C to close immediately")
        
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n⚠️  Closing...")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n🔒 Closing browser...")
        try:
            driver.quit()
        except:
            pass
        print("✅ Done!")


if __name__ == "__main__":
    diagnose_indeed_page()