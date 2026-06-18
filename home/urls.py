from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("blog/", views.blog_list, name="blog_list"),
    path("blog/<slug:slug>/", views.blog_detail, name="blog_detail"),
    path("api/whatsapp-webhook/", views.whatsapp_webhook, name="whatsapp_webhook"),
    path("api/web-chat/", views.web_chat, name="web_chat"),
]
