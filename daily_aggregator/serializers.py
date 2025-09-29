import pytz
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import serializers

from assignment.models import User
from daily_aggregator.models import LearningLog


# class LearningLogSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = LearningLog


class LearningLogCreateSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(required=False)
    timezone = serializers.CharField(required=False, default="UTC")

    class Meta:
        model = LearningLog
        fields = ["word_count", "study_time", "timestamp", "timezone"]

    def validate_timezone(self, value):
        try:
            pytz.timezone(value)
        except pytz.exceptions.UnknownTimeZoneError:
            raise serializers.ValidationError("Invalid timezone")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        # print("hello: ", self.context)

        # Handle timestamp and timezone
        client_timestamp = validated_data.get("timestamp")
        tz_name = validated_data.get("timezone", "UTC")

        if client_timestamp:
            # Convert to UTC for storage
            tz = pytz.timezone(tz_name)
            if timezone.is_naive(client_timestamp):
                client_timestamp = tz.localize(client_timestamp)
            timestamp_utc = client_timestamp.astimezone(pytz.UTC)
        else:
            timestamp_utc = timezone.now()
            client_timestamp = timestamp_utc

        return LearningLog.objects.create(
            user=user,
            word_count=validated_data["word_count"],
            study_time=validated_data["study_time"],
            timestamp=timestamp_utc,
            client_timestamp=client_timestamp,
            timezone=tz_name,
        )


class LearningLogListSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningLog
        # fields = ['word_count', 'study_time', 'timestamp', 'timezone']
        fields = "__all__"


class UserSummaryQuerySerializer(serializers.Serializer):
    """Serializer for validating summary query parameters"""

    from_date = serializers.DateTimeField()
    to_date = serializers.DateTimeField()
    granularity = serializers.ChoiceField(
        choices=["hour", "day", "month"], default="day"
    )
    timezone = serializers.CharField(default="UTC")
    window_size = serializers.IntegerField(default=3, min_value=1, max_value=365)

    def validate_timezone(self, value):
        try:
            pytz.timezone(value)
        except pytz.exceptions.UnknownTimeZoneError:
            raise serializers.ValidationError("Invalid timezone")
        return value

    def validate(self, data):
        if data["from_date"] >= data["to_date"]:
            raise serializers.ValidationError("'from' date must be before 'to' date")
        return data


class SummarySerializer(serializers.Serializer):
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField()
    total_word_count = serializers.IntegerField()
    total_study_time = serializers.IntegerField()
    average_word_count = serializers.FloatField()
    average_study_time = serializers.FloatField()
    moving_average_word_count = serializers.FloatField(allow_null=True)
    moving_average_study_time = serializers.FloatField(allow_null=True)
