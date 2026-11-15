from django.urls import path

from .views import (
    ApiTokenDeleteView,
    ApiTokenListCreateView,
    CsrfView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
)

urlpatterns = [
    path("csrf/", CsrfView.as_view(), name="auth-csrf"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("password/reset/request/", PasswordResetRequestView.as_view(),
         name="auth-password-reset-request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(),
         name="auth-password-reset-confirm"),
    path("tokens/", ApiTokenListCreateView.as_view(), name="auth-tokens"),
    path("tokens/<uuid:pk>/", ApiTokenDeleteView.as_view(),
         name="auth-token-delete"),
]
