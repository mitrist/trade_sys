import json
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from agent.models import AgentFeedback, AgentRun, AgentSignal


def _load_strategy_rules():
    path = Path(__file__).resolve().parent / "strategy_rules.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        rules = json.load(f)
    return {r["id"]: r for r in rules}


@login_required
@require_http_methods(["GET"])
def agent_dashboard(request):
    """Список запусков агента (таблица/карточки): дата, статус, тип, длительность, summary."""
    status_filter = request.GET.get("status", "").strip()
    run_type_filter = request.GET.get("run_type", "").strip()
    qs = AgentRun.objects.all().order_by("-started_at")[:200]
    if status_filter:
        qs = qs.filter(status=status_filter)
    if run_type_filter:
        qs = qs.filter(run_type=run_type_filter)
    runs = []
    for r in qs:
        duration = None
        if r.finished_at and r.started_at:
            duration = (r.finished_at - r.started_at).total_seconds()
        run_type_display = dict(AgentRun.RUN_TYPE_CHOICES).get(r.run_type, r.run_type or "—")
        runs.append({
            "id": r.id,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "status": r.status,
            "trigger": r.trigger,
            "run_type": r.run_type,
            "run_type_display": run_type_display,
            "input_params": r.input_params,
            "summary": (r.summary or "")[:200],
            "duration_sec": duration,
        })
    return render(
        request,
        "agent/dashboard.html",
        {"runs": runs, "status_filter": status_filter, "run_type_filter": run_type_filter},
    )


@login_required
@require_http_methods(["GET", "POST"])
def agent_run_detail(request, pk):
    """Страница одного запуска: параметры, анализ, сигналы, логи."""
    run = get_object_or_404(AgentRun, pk=pk)

    if request.method == "POST":
        feedback_type = request.POST.get("feedback_type", "").strip()
        comment = request.POST.get("comment", "").strip()
        signal_id = request.POST.get("signal_id", "").strip() or None
        if feedback_type in ("correction", "override", "approve"):
            signal = None
            if signal_id:
                try:
                    signal = run.signals.get(pk=int(signal_id))
                except (ValueError, AgentSignal.DoesNotExist):
                    pass
            AgentFeedback.objects.create(
                run=run,
                signal=signal,
                feedback_type=feedback_type,
                comment=comment,
                user=request.user,
            )
        return redirect("agent:run-detail-page", pk=pk)
    analyses = list(run.analyses.select_related().order_by("created_at"))
    signals = list(run.signals.select_related().order_by("created_at"))
    logs = list(run.logs.select_related().order_by("created_at"))
    duration = None
    if run.finished_at and run.started_at:
        duration = (run.finished_at - run.started_at).total_seconds()
    log_level_filter = request.GET.get("log_level", "").strip()
    if log_level_filter:
        logs = [l for l in logs if l.level == log_level_filter]
    input_params_json = json.dumps(run.input_params, indent=2, ensure_ascii=False) if run.input_params else ""
    reasoning_steps = [a for a in analyses if a.analysis_type == "reasoning_step"]
    reasoning_steps_data = []
    for a in reasoning_steps:
        c = a.content or {}
        input_display = json.dumps(c.get("input_data"), indent=2, ensure_ascii=False) if c.get("input_data") is not None else ""
        reasoning_steps_data.append({
            "step": c.get("step"),
            "description": c.get("description", ""),
            "input_display": input_display,
            "conclusion": c.get("conclusion", ""),
            "rule": c.get("rule", ""),
        })
    other_analyses = [a for a in analyses if a.analysis_type != "reasoning_step"]
    analyses_data = [
        {"obj": a, "content_display": json.dumps(a.content, indent=2, ensure_ascii=False) if a.content else ""}
        for a in other_analyses
    ]
    feedbacks = list(run.feedbacks.select_related("signal", "user").order_by("created_at"))
    strategy_rules_map = _load_strategy_rules()
    signals_with_rules = []
    for s in signals:
        rule_info = strategy_rules_map.get(s.rule, {}) if s.rule else {}
        signals_with_rules.append({
            "signal": s,
            "rule_name": rule_info.get("name", s.rule or "—"),
            "rule_excerpt": rule_info.get("excerpt", ""),
        })
    return render(
        request,
        "agent/run_detail.html",
        {
            "run": run,
            "input_params_json": input_params_json,
            "reasoning_steps_data": reasoning_steps_data,
            "analyses_data": analyses_data,
            "signals_with_rules": signals_with_rules,
            "feedbacks": feedbacks,
            "logs": logs,
            "duration_sec": duration,
            "log_level_filter": log_level_filter,
        },
    )
