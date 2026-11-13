from django.urls import path

from .views import DashboardTodayView, DashboardWeeklyView, LeaderboardView

urlpatterns = [
    path("dashboard/today/", DashboardTodayView.as_view(), name="dashboard-today"),
    path("dashboard/weekly/", DashboardWeeklyView.as_view(), name="dashboard-weekly"),
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
]
