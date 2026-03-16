from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("playground/", views.playground, name="playground"),
    path("playground/search/", views.search_results, name="search_results"),
]
