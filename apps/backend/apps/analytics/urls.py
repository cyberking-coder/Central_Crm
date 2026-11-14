from django.urls import path

from .views import (
    CampaignReportView,
    DashboardTodayView,
    DashboardWeeklyView,
    DepartmentReportView,
    FunnelReportView,
    LeaderboardView,
    ReportExportView,
    SourceReportView,
)

urlpatterns = [
    path("dashboard/today/", DashboardTodayView.as_view(), name="dashboard-today"),
    path("dashboard/weekly/", DashboardWeeklyView.as_view(), name="dashboard-weekly"),
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
    path("reports/sources/", SourceReportView.as_view(), name="report-sources"),
    path("reports/campaigns/", CampaignReportView.as_view(), name="report-campaigns"),
    path("reports/funnel/", FunnelReportView.as_view(), name="report-funnel"),
    path("reports/departments/", DepartmentReportView.as_view(), name="report-departments"),
    path("reports/<str:kind>/export/", ReportExportView.as_view(), name="report-export"),
]
