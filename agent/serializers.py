from rest_framework import serializers
from agent.models import AgentAnalysis, AgentFeedback, AgentLog, AgentRun, AgentSignal


class AgentRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentRun
        fields = ("id", "started_at", "finished_at", "status", "trigger", "run_type", "input_params", "summary")
        read_only_fields = ("id", "started_at")


class AgentRunCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentRun
        fields = ("trigger", "input_params", "run_type")


class AgentAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentAnalysis
        fields = ("id", "symbol", "analysis_type", "content", "created_at")


class AgentAnalysisBulkSerializer(serializers.Serializer):
    items = AgentAnalysisSerializer(many=True)

    def create(self, validated_data):
        run = self.context["run"]
        for item in validated_data["items"]:
            AgentAnalysis.objects.create(run=run, **item)
        return run


class AgentSignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentSignal
        fields = (
            "id", "symbol", "side", "price_level", "stop_level", "target_level",
            "reason", "rule", "confidence", "created_at",
        )


class AgentSignalBulkSerializer(serializers.Serializer):
    items = AgentSignalSerializer(many=True)

    def create(self, validated_data):
        run = self.context["run"]
        for item in validated_data["items"]:
            AgentSignal.objects.create(run=run, **item)
        return run


class AgentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentLog
        fields = ("id", "level", "message", "source", "created_at")


class AgentLogBulkSerializer(serializers.Serializer):
    items = AgentLogSerializer(many=True)

    def create(self, validated_data):
        run = self.context["run"]
        for item in validated_data["items"]:
            AgentLog.objects.create(run=run, **item)
        return run


class AgentRunPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentRun
        fields = ("status", "summary", "finished_at")


class AgentFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentFeedback
        fields = ("id", "run", "signal", "feedback_type", "comment", "user", "created_at")
        read_only_fields = ("id", "run", "user", "created_at")


class AgentFeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentFeedback
        fields = ("signal", "feedback_type", "comment")

    def create(self, validated_data):
        run = self.context["run"]
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        return AgentFeedback.objects.create(
            run=run,
            user=user,
            **validated_data,
        )
