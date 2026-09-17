from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from contacts.views import contact_list

urlpatterns = [
    path("", contact_list, name="contacts"),
    path("login/", LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
