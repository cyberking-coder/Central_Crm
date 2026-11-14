from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ExpenseViewSet, InvoiceViewSet, PaymentViewSet

invoices_router = DefaultRouter()
invoices_router.include_root_view = False
invoices_router.register("", InvoiceViewSet, basename="invoice")

payments_router = DefaultRouter()
payments_router.include_root_view = False
payments_router.register("", PaymentViewSet, basename="payment")

expenses_router = DefaultRouter()
expenses_router.include_root_view = False
expenses_router.register("", ExpenseViewSet, basename="expense")

urlpatterns = [
    path("invoices/", include(invoices_router.urls)),
    path("payments/", include(payments_router.urls)),
    path("expenses/", include(expenses_router.urls)),
]
