# scraper/urls.py 


from django.urls import path
from .views import show_leads , export_today_leads_excel , add_course,user_login, user_logout, register
from . import views

urlpatterns = [
    path("", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path("leads/", show_leads, name="show_leads"),
    path('leads/export-today/', export_today_leads_excel, name='export_today_leads'),
    path('add-course/', add_course, name='add_course'),
    path('update-course/<int:course_id>/', views.update_course, name='update_course'),
    path('delete-course/<int:course_id>/', views.delete_course, name='delete_course'),
    path("register/", register, name="register"),
    path('users/', views.manage_users, name='manage_users'),
    path('users/update/<int:user_id>/', views.update_user, name='update_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
]





