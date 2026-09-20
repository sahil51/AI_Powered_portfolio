from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('', views.home_view, name='home'),
    path('blog/', views.blog_list_view, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail_view, name='blog_detail'),
    path('visitors/', views.visitors_view, name='visitors'),
    path('contact/submit/', views.contact_submit_view, name='contact_submit'),
    path('api/blog/create/', views.api_create_blog_post, name='api_create_blog_post'),
    path('api/blog/add/', views.api_create_blog_post, name='api_add_blog_post'),
    path('api/chat/', views.chat_proxy_view, name='chat_proxy'),
]

