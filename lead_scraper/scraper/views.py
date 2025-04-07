from django.shortcuts import render, redirect
from django.utils.timezone import now
from datetime import timedelta
from .models import Lead
import requests
from bs4 import BeautifulSoup
import os
import re  # ✅ Make sure re is imported
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")

# 🔍 Google Search Scraper
def scrape_google():
    query = "best python courses for students site:quora.com OR site:reddit.com OR site:stackoverflow.com OR site:linkedin.com"
    search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CSE_ID}&dateRestrict=m1"
    
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()

        if "items" in data:
            for item in data["items"]:
                title = item.get("title", "No Name")
                link = item.get("link")

                if not Lead.objects.filter(profile_link=link).exists():
                    email = extract_email_from_url(link)

                    Lead.objects.create(
                        name=title,
                        profile_link=link,
                        source="Google Search",
                        email=email if email else None
                    )
    except requests.exceptions.RequestException as e:
        print(f"Error scraping Google: {e}")


# Email Extractor
def extract_email_from_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        page = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(page.content, 'html.parser')

        # Method 1: Extract emails from text
        text = soup.get_text()
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

        # Method 2: Extract mailto links
        mailtos = [a['href'][7:] for a in soup.find_all('a', href=True) if a['href'].startswith('mailto:')]
        all_emails = emails + mailtos

        return all_emails[0] if all_emails else None
    except Exception as e:
        print(f"Error extracting email from {url}: {e}")
        return None


# Coursera Scraper
def scrape_coursera():
    url = "https://www.coursera.org/learn/python/reviews"
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        reviews = soup.find_all("div", class_="review-text")
        reviewers = soup.find_all("div", class_="reviewerName")

        for i, review in enumerate(reviews[:5]):
            review_text = review.text.strip()
            reviewer_name = reviewers[i].text.strip() if i < len(reviewers) else "Anonymous"

            if not Lead.objects.filter(name=review_text).exists():
                Lead.objects.create(
                    name=reviewer_name,
                    profile_link=url,
                    source="Coursera",
                    email=None
                )

    except Exception as e:
        print(f"Error scraping Coursera: {e}")
        driver.quit()


#  View to Show and Refresh Leads
def show_leads(request):
    if request.method == "POST":
        scrape_google()
        # scrape_coursera()
        return redirect("show_leads")

    # Show only recent leads
    thirty_days_ago = now() - timedelta(days=30)
    fresh_leads = Lead.objects.filter(created_at__gte=thirty_days_ago)

    return render(request, "scraper/lead.html", {"leads": fresh_leads})
