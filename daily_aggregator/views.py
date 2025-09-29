from django.shortcuts import get_object_or_404, render
from rest_framework import generics, status, permissions, viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from assignment.models import User
from daily_aggregator.models import LearningLog
from daily_aggregator.serializers import (
    LearningLogCreateSerializer,
    LearningLogListSerializer,
    SummarySerializer,
    UserSummaryQuerySerializer,
)
from django.db import IntegrityError

from daily_aggregator.services import UserSummaryAggregator


# Create your views here.
class LogRegistrationView(generics.CreateAPIView):
    """
    F1: Log Registration POST API
    F4: Idempotence for duplicate submissions from the same user.

    takes word_count, study_time, timestamp etc in json format as input
    and creates a learning log entry for the user
    """

    queryset = LearningLog.objects.all()
    serializer_class = LearningLogCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=False):
            try:
                self.perform_create(serializer)
                res_serializer = LearningLogListSerializer(serializer.instance)
                return Response(res_serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                # Handling the duplicate entry from the same user and same timestamp for idempotency
                return Response(
                    {"message": "Duplicate entry"}, status=status.HTTP_200_OK
                )
            except Exception as e:
                raise e
                print("Err at log.create(): ", e)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSummaryView(APIView):
    """
    F2: Aggregation Retrieval - GET /users/{id}/summary
    F3: Simple Moving Average (SMA).
    F5: Multiple Timezone support

    Provides user summary.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        # Validate query parameters using serializer
        query_serializer = UserSummaryQuerySerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return Response(query_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, id=user_id)
        validated_data = query_serializer.validated_data
        # print("validated_data: ", validated_data)

        try:
            aggregated_data = UserSummaryAggregator().get_user_summary(
                user=user,
                from_date=validated_data["from_date"],
                to_date=validated_data["to_date"],
                granularity=validated_data["granularity"],
                tz_name=validated_data["timezone"],
                window_size=validated_data["window_size"],
            )

            # Serialize the response data
            data_serializer = SummarySerializer(aggregated_data, many=True)

            return Response(
                {
                    "user_id": user_id,
                    "granularity": validated_data["granularity"],
                    "timezone": validated_data["timezone"],
                    "window_size": validated_data["window_size"],
                    "total_periods": len(aggregated_data),
                    "data": data_serializer.data,
                }
            )

        except Exception as e:
            # raise e
            return Response(
                {"error": f"Error processing request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
