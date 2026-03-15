from rest_framework import status
from rest_framework.generics import GenericAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response

from agent.models import AgentRun, AgentSignal
from agent.serializers import (
    AgentAnalysisBulkSerializer,
    AgentFeedbackCreateSerializer,
    AgentFeedbackSerializer,
    AgentLogBulkSerializer,
    AgentRunCreateSerializer,
    AgentRunPatchSerializer,
    AgentRunSerializer,
    AgentSignalBulkSerializer,
)


class AgentRunListCreateView(ListCreateAPIView):
    """GET /api/agent/runs/ — список запусков. POST — создать запуск (тело: trigger, input_params)."""
    queryset = AgentRun.objects.all()
    serializer_class = AgentRunSerializer

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AgentRunCreateSerializer
        return AgentRunSerializer

    def create(self, request: Request, *args, **kwargs):
        ser = AgentRunCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        run = ser.save()
        return Response(
            AgentRunSerializer(run).data,
            status=status.HTTP_201_CREATED,
        )


class AgentRunDetailView(GenericAPIView):
    """GET /api/agent/runs/<id>/ — детали. PATCH — обновить статус/summary/finished_at."""
    queryset = AgentRun.objects.all()
    serializer_class = AgentRunSerializer

    def get(self, request: Request, pk=None):
        run = get_object_or_404(AgentRun, pk=pk)
        return Response(AgentRunSerializer(run).data)

    def patch(self, request: Request, pk=None):
        run = get_object_or_404(AgentRun, pk=pk)
        ser = AgentRunPatchSerializer(run, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(AgentRunSerializer(run).data)


class AgentRunAnalysisView(GenericAPIView):
    """POST /api/agent/runs/<id>/analysis/ — добавить массив анализов. Тело: { "items": [ { "symbol", "analysis_type", "content" }, ... ] }."""
    queryset = AgentRun.objects.all()
    serializer_class = AgentAnalysisBulkSerializer

    def post(self, request: Request, pk=None):
        run = get_object_or_404(AgentRun, pk=pk)
        ser = AgentAnalysisBulkSerializer(data=request.data, context={"run": run})
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"status": "ok", "run_id": run.pk}, status=status.HTTP_201_CREATED)


class AgentRunSignalsView(GenericAPIView):
    """POST /api/agent/runs/<id>/signals/ — добавить массив сигналов."""
    queryset = AgentRun.objects.all()
    serializer_class = AgentSignalBulkSerializer

    def post(self, request: Request, pk=None):
        run = get_object_or_404(AgentRun, pk=pk)
        ser = AgentSignalBulkSerializer(data=request.data, context={"run": run})
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"status": "ok", "run_id": run.pk}, status=status.HTTP_201_CREATED)


class AgentRunLogsView(GenericAPIView):
    """POST /api/agent/runs/<id>/logs/ — добавить массив логов."""
    queryset = AgentRun.objects.all()
    serializer_class = AgentLogBulkSerializer

    def post(self, request: Request, pk=None):
        run = get_object_or_404(AgentRun, pk=pk)
        ser = AgentLogBulkSerializer(data=request.data, context={"run": run})
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"status": "ok", "run_id": run.pk}, status=status.HTTP_201_CREATED)


class AgentRunFeedbackView(GenericAPIView):
    """GET /api/agent/runs/<id>/feedback/ — список обратной связи. POST — создать (тело: signal_id?, feedback_type, comment)."""
    queryset = AgentRun.objects.all()

    def get(self, request: Request, pk=None):
        run = get_object_or_404(AgentRun, pk=pk)
        feedbacks = run.feedbacks.select_related("signal", "user").order_by("created_at")
        return Response(AgentFeedbackSerializer(feedbacks, many=True).data)

    def post(self, request: Request, pk=None):
        run = get_object_or_404(AgentRun, pk=pk)
        data = request.data.copy()
        signal_id = data.pop("signal_id", None) or data.get("signal")
        if signal_id is not None:
            try:
                signal = AgentSignal.objects.get(pk=signal_id, run=run)
                data["signal"] = signal.pk
            except AgentSignal.DoesNotExist:
                data["signal"] = None
        ser = AgentFeedbackCreateSerializer(
            data=data, context={"run": run, "request": request}
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(AgentFeedbackSerializer(ser.instance).data, status=status.HTTP_201_CREATED)
