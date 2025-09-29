import pytest
import pytz
from datetime import datetime
from django.db import IntegrityError

from assignment.models import User
from daily_aggregator.models import LearningLog


@pytest.mark.django_db
class TestAggregationService:
    def setup_method(self):
        self.test_username = "testuser"
        self.user = User.objects.create_user(username=self.test_username)

    def test_create_learning_log(self):
        log = LearningLog.objects.create(
            user=self.user,
            word_count=100,
            study_time=25,
            timestamp=datetime.now(pytz.UTC),
            timezone='UTC'
        )
        assert log.word_count == 100
        assert log.study_time == 25
    
    def test_idempotency_constraint(self):
        timestamp = datetime.now(pytz.UTC)
        user = self.user
        # Create first log
        LearningLog.objects.create(
            user=user,
            word_count=100,
            study_time=25,
            timestamp=timestamp,
            timezone='UTC',
        )
        
        # Attempt to create duplicate should fail
        with pytest.raises(IntegrityError):
            LearningLog.objects.create(
                user=user,
                word_count=100,
                study_time=25,
                timestamp=timestamp,
                timezone='UTC',
            )
