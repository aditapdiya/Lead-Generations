from django.urls import path
from .views import show_leads , export_today_leads_excel , add_course
from . import views
urlpatterns = [
    path("", show_leads, name="show_leads"),
    path('leads/export-today/', export_today_leads_excel, name='export_today_leads'),
    path('add-course/', add_course, name='add_course'),
    path('update-course/<int:course_id>/', views.update_course, name='update_course'),
    path('delete-course/<int:course_id>/', views.delete_course, name='delete_course'),
     
]

