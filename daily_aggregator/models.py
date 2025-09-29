from django.db import models
from assignment.models import User


# Create your models here.
class LearningLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="learning_logs"
    )
    word_count = models.IntegerField()
    study_time = models.IntegerField()  # Assumed to be in minutes

    timestamp = models.DateTimeField()
    client_timestamp = models.DateTimeField(
        null=True, blank=True
    )  # Original client timestamp
    timezone = models.CharField(max_length=50, default="UTC")

    # Considering the combination of user and timestamp for unique key for idempotence
    # key = models.CharField(max_length=255, null=True, blank=True) # Idempotency key

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "learning_logs"
        verbose_name = "Learning Log"
        verbose_name_plural = "Learning Logs"

        unique_together = ("user", "timestamp") # Ensuring idempotency
