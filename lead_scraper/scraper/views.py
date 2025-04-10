# scraper/view.py

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
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")



def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('show_leads')  # redirect to leads after login
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'scraper/login.html')


@login_required
def user_logout(request):
    logout(request)
    return redirect('login')  # back to login page


def scrape_google():
    current_year = datetime.datetime.now().year
    courses = Course.objects.all()
    new_lead_count = 0  # Track new leads

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
                        new_lead_count += 1  # Count this as a new lead
        except requests.exceptions.RequestException as e:
            print(f"Error scraping Google: {e}")

    return new_lead_count


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
    

from collections import defaultdict

@login_required
def show_leads(request):
    if request.method == "POST":
        new_leads = scrape_google()
        request.session['new_lead_count'] = new_leads
        return redirect("show_leads")

    new_lead_count = request.session.pop('new_lead_count', None)
    thirty_days_ago = now() - timedelta(days=30)
    fresh_leads = Lead.objects.filter(created_at__gte=thirty_days_ago).order_by('-created_at')

    grouped_leads = defaultdict(list)
    for lead in fresh_leads:
        date_str = lead.created_at.strftime('%Y-%m-%d')
        grouped_leads[date_str].append(lead)

    sorted_leads_by_day = dict(sorted(grouped_leads.items(), reverse=True))  # latest date first

    return render(request, "scraper/lead.html", {
        "grouped_leads": sorted_leads_by_day,
        "new_lead_count": new_lead_count
    })


@login_required
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

@login_required
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
