from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from contacts.views import contact_list
from contacts import suggestion_views

urlpatterns = [
    path("", contact_list, name="contacts"),
    path("contacts/<int:contact_id>/suggest-tag/", suggestion_views.suggest_tag, name="suggest_tag"),
    path("suggestions/<uuid:suggestion_id>/", suggestion_views.review_tag, name="review_tag"),
    path("suggestions/<uuid:suggestion_id>/accept/", suggestion_views.accept_tag, name="accept_tag"),
    path("suggestions/<uuid:suggestion_id>/decline/", suggestion_views.decline_tag, name="decline_tag"),
    path("login/", LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
