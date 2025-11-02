from accounts.views import role_based_redirect
from django.urls import path

from .views import HomePageView, AboutPageView, HelpPageView

urlpatterns = [
    path("", role_based_redirect, name="home_redirect"),
    path("home/", HomePageView.as_view(), name="home"),
    path("about/", AboutPageView.as_view(), name="about"),
    path("help/", HelpPageView.as_view(), name="help"),
]
