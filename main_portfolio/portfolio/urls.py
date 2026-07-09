from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('blog/', views.blog_list_view, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail_view, name='blog_detail'),
    path('visitors/', views.visitors_view, name='visitors'),
    path('contact/submit/', views.contact_submit_view, name='contact_submit'),
]
