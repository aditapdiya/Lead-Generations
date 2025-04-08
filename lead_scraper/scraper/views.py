from django.shortcuts import render, redirect
from django.utils.timezone import now
from datetime import timedelta
from .models import Lead , Course
import requests
from bs4 import BeautifulSoup
import os
import re 
import openpyxl
from django.http import HttpResponse
from .forms import CourseForm
from django.shortcuts import get_object_or_404
import datetime
API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")



#hello this is a new update
def scrape_google():
    current_year = datetime.datetime.now().year
    courses = Course.objects.all()
    for course in courses:
        query =  f"best {course} courses for students of {current_year} site:quora.com OR site:reddit.com OR site:stackoverflow.com OR site:linkedin.com"
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

def extract_email_from_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        page = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(page.content, 'html.parser')

        text = soup.get_text()
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

        mailtos = [a['href'][7:] for a in soup.find_all('a', href=True) if a['href'].startswith('mailto:')]
        all_emails = emails + mailtos

        return all_emails[0] if all_emails else None
    except Exception as e:
        print(f"Error extracting email from {url}: {e}")
        return None

def show_leads(request):
    if request.method == "POST":
        scrape_google()
        return redirect("show_leads")
    thirty_days_ago = now() - timedelta(days=30)
    fresh_leads = Lead.objects.filter(created_at__gte=thirty_days_ago)
    return render(request, "scraper/lead.html", {"leads": fresh_leads})

def export_today_leads_excel(request):
    today = now().date()
    today_leads = Lead.objects.filter(created_at__date=today)
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Today\'s Leads'
    sheet.append(["Name", "Profile Link", "Source", "Email", "Date Added"])
    
    for lead in today_leads:
        sheet.append([lead.name, lead.profile_link, lead.source, lead.email, lead.created_at.strftime('%Y-%m-%d %H:%M')])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=today_leads.xlsx'
    workbook.save(response)
    return response

def add_course(request):
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("add_course")  
    else:
        form = CourseForm()
    
    courses = Course.objects.all()  
    return render(request, "scraper/add_course.html", {"form": form, "courses": courses})

def update_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('add_course')
    else:
        form = CourseForm(instance=course)
    return render(request, 'scraper/update_course.html', {'form': form, 'course': course})

def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course.delete()
        return redirect('add_course')
    return render(request, 'scraper/delete_course.html', {'course': course})
