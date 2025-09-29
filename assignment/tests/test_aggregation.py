import pytest
import pytz
from datetime import datetime, timedelta

from assignment.models import User
from daily_aggregator.services import UserSummaryAggregator
from daily_aggregator.models import LearningLog


@pytest.mark.django_db
class TestAggregationService:
    def test_get_user_summary(self):
        # Create test data across multiple days
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=pytz.UTC)
        user = User.objects.create_user(
            f"testuser",
            email=f"testuser@example.com",
            password="testpassword",
        )

        for i in range(5):
            LearningLog.objects.create(
                user=user,
                word_count=100 + (i * 10),
                study_time=30 + (i * 5),
                timestamp=base_time + timedelta(days=i),
            )

        from_date = base_time - timedelta(days=1)
        to_date = base_time + timedelta(days=6)

        # Test the pure ORM version
        results = UserSummaryAggregator().get_user_summary(
            user=user,
            from_date=from_date,
            to_date=to_date,
            granularity="day",
            window_size=3,
        )

        assert len(results) == 5
        assert results[0]["total_word_count"] == 100
        assert results[0]["moving_average_word_count"] is None  # Insufficient data
        assert results[2]["moving_average_word_count"] is not None  # Asserting that the moving averages are calculated from the nth element
