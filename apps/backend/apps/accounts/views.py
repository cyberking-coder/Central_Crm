"""Auth endpoints: login, logout, me, password reset."""
from __future__ import annotations

from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle

from apps.audit.services import record_audit

from .models import User
from .serializers import (
    LoginSerializer,
    MeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)
from .services import (
    decode_reset_token,
    emit_password_reset_delivery,
    make_reset_token,
    record_login,
)


def _client_ip(request) -> str | None:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class CsrfView(APIView):
    """Sets the CSRF cookie. Frontend calls this before any POST."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(summary="Issue CSRF cookie", responses={200: dict})
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        request=LoginSerializer,
        responses={200: MeSerializer, 400: OpenApiResponse(description="Invalid credentials")},
    )
    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = authenticate(request,
                            username=s.validated_data["email"].lower(),
                            password=s.validated_data["password"])
        if user is None or not user.is_active:
            record_audit(actor=None, action="login.failed",
                         entity_type="User", entity_id=None,
                         request=request,
                         extra={"email": s.validated_data["email"]})
            return Response({"detail": "Invalid credentials"},
                            status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        record_login(user, _client_ip(request))
        record_audit(actor=user, action="login.success",
                     entity_type="User", entity_id=str(user.pk),
                     request=request)
        return Response(MeSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={204: None})
    def post(self, request):
        uid = str(request.user.pk) if request.user.is_authenticated else None
        record_audit(actor=request.user, action="logout",
                     entity_type="User", entity_id=uid, request=request)
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: MeSerializer})
    def get(self, request):
        return Response(MeSerializer(request.user).data)


class PasswordResetRequestView(APIView):
    """
    Always returns 204 so the endpoint doesn't leak account existence.
    When the email matches an active user, a reset token is emitted
    (currently logged; email delivery lands in Phase 9).
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @extend_schema(request=PasswordResetRequestSerializer, responses={204: None})
    def post(self, request):
        s = PasswordResetRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        email = s.validated_data["email"].lower()
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)
        uid, token = make_reset_token(user)
        emit_password_reset_delivery(user, uid, token, request)
        record_audit(actor=None, action="password_reset.requested",
                     entity_type="User", entity_id=str(user.pk),
                     request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @extend_schema(request=PasswordResetConfirmSerializer,
                   responses={204: None, 400: OpenApiResponse(description="Invalid token")})
    def post(self, request):
        s = PasswordResetConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = decode_reset_token(s.validated_data["uid"],
                                  s.validated_data["token"])
        if user is None:
            return Response({"detail": "Invalid or expired token"},
                            status=status.HTTP_400_BAD_REQUEST)
        user.set_password(s.validated_data["new_password"])
        user.save(update_fields=["password"])
        record_audit(actor=user, action="password_reset.completed",
                     entity_type="User", entity_id=str(user.pk),
                     request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)
