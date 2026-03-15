from django.contrib import admin
from agent.models import AgentAnalysis, AgentFeedback, AgentLog, AgentRun, AgentSignal


class AgentAnalysisInline(admin.TabularInline):
    model = AgentAnalysis
    extra = 0


class AgentSignalInline(admin.TabularInline):
    model = AgentSignal
    extra = 0


class AgentLogInline(admin.TabularInline):
    model = AgentLog
    extra = 0


class AgentFeedbackInline(admin.TabularInline):
    model = AgentFeedback
    extra = 0
    fk_name = "run"


@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = ("id", "started_at", "status", "run_type", "trigger")
    list_filter = ("status", "run_type", "trigger")
    inlines = [AgentAnalysisInline, AgentSignalInline, AgentLogInline, AgentFeedbackInline]
