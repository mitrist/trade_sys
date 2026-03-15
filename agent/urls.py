from django.urls import path
from agent import views as agent_views
from agent.api_views import (
    AgentRunAnalysisView,
    AgentRunDetailView,
    AgentRunFeedbackView,
    AgentRunListCreateView,
    AgentRunLogsView,
    AgentRunSignalsView,
)

app_name = "agent"
urlpatterns = [
    path("", agent_views.agent_dashboard, name="dashboard"),
    path("runs/<int:pk>/page/", agent_views.agent_run_detail, name="run-detail-page"),
    path("runs/", AgentRunListCreateView.as_view(), name="run-list-create"),
    path("runs/<int:pk>/", AgentRunDetailView.as_view(), name="run-detail"),
    path("runs/<int:pk>/analysis/", AgentRunAnalysisView.as_view(), name="run-analysis"),
    path("runs/<int:pk>/signals/", AgentRunSignalsView.as_view(), name="run-signals"),
    path("runs/<int:pk>/logs/", AgentRunLogsView.as_view(), name="run-logs"),
    path("runs/<int:pk>/feedback/", AgentRunFeedbackView.as_view(), name="run-feedback"),
]
