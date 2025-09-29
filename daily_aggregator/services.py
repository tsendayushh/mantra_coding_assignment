import pytz
from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncHour, TruncDay, TruncMonth
from datetime import datetime, timedelta

from assignment.models import User
from daily_aggregator.models import LearningLog


class UserSummaryAggregator:
    """ """

    GRANULARITY_MAP = {"hour": TruncHour, "day": TruncDay, "month": TruncMonth}

    def get_user_summary(
        self,
        user: User,
        from_date: datetime,
        to_date: datetime,
        granularity: str,  # "hour", "day", "month"
        tz_name: str = "",
        window_size: int = 3,  # Default window size for calculating the moving average
    ):
        if granularity not in self.GRANULARITY_MAP:
            raise ValueError(f"Invalid granularity: {granularity}")
        # The trunc func for the granularity
        trunc_func = self.GRANULARITY_MAP[granularity]

        tz = pytz.timezone(tz_name) if tz_name else pytz.UTC

        # Convert the dates to UTC
        if from_date.tzinfo is None:
            from_date = tz.localize(from_date)
        if to_date.tzinfo is None:
            to_date = tz.localize(to_date)
        from_date_utc = from_date.astimezone(pytz.UTC)
        to_date_utc = to_date.astimezone(pytz.UTC)

        # First aggregating based on the granularity with tz aware truc
        queryset = (
            LearningLog.objects.filter(
                user=user, timestamp__gte=from_date_utc, timestamp__lte=to_date_utc
            )
            .annotate(
                # convert to target timezone, then truncate
                period_start=trunc_func("timestamp", tzinfo=tz)
            )
            .values("period_start")
            .annotate(
                total_word_count=Sum("word_count"),
                total_study_time=Sum("study_time"),
                log_count=Count("id"),
                average_word_count=Avg("word_count"),
                average_study_time=Avg("study_time"),
            )
            .order_by("period_start")
        )
        # average_word_count=Avg("word_count", output_field=models.FloatField()),
        # average_study_time=Avg("study_time", output_field=models.FloatField()),
        return self.calculate_SMA(queryset, granularity, window_size)

    @classmethod
    def calculate_SMA(cls, queryset, granularity, window_size):
        """
        Process the aggregated queryset results(buckets) and calculate moving averages
        """
        results = []
        word_count_window = []
        study_time_window = []

        for row in queryset:
            # Calculate period end based on granularity
            period_start = row["period_start"]

            if granularity == "hour":
                period_end = period_start + timedelta(hours=1)
            elif granularity == "day":
                period_end = period_start + timedelta(days=1)
            else:  # month
                # Handle month end properly
                if period_start.month == 12:
                    period_end = period_start.replace(
                        year=period_start.year + 1, month=1
                    )
                else:
                    period_end = period_start.replace(month=period_start.month + 1)

            # Add to moving window
            word_count_window.append(row["total_word_count"])
            study_time_window.append(row["total_study_time"])

            # Maintain window size
            if len(word_count_window) > window_size:
                word_count_window.pop(0)
                study_time_window.pop(0)

            # Filling the first n buckets with null
            moving_avg_words = None
            moving_avg_study = None

            if len(word_count_window) >= window_size:
                moving_avg_words = sum(word_count_window) / len(word_count_window)
                moving_avg_study = sum(study_time_window) / len(study_time_window)

            results.append(
                {
                    "period_start": period_start,
                    "period_end": period_end,
                    "total_word_count": row["total_word_count"],
                    "total_study_time": row["total_study_time"],
                    "average_word_count": float(row["average_word_count"] or 0),
                    "average_study_time": float(row["average_study_time"] or 0),
                    "moving_average_word_count": moving_avg_words,
                    "moving_average_study_time": moving_avg_study,
                }
            )

        return results
