from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from contacts.views import contact_list, suggest_contact_tag

urlpatterns = [
    path("", contact_list, name="contacts"),
    path("contacts/<int:pk>/suggest-tag/", suggest_contact_tag, name="suggest_contact_tag"),
    path("login/", LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
