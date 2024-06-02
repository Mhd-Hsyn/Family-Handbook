from django.db import models
from api.models import BaseModel,Auth


class PointsTable(BaseModel):
    auth_id = models.ForeignKey(Auth, on_delete=models.CASCADE, blank=True, null=True)
    points = models.IntegerField(default=0)

class Task(BaseModel):
    ROLE_CHOICES = [
        ("individual", "individual"),
        ("team_work", "team_work"),
    ]
    task_name = models.CharField(max_length=5000,default="")
    date_from = models.DateField(blank=True,null=True)
    date_to = models.DateField(blank=True,null=True)
    start_time = models.TimeField(blank=True,null=True)
    end_time = models.TimeField(blank=True,null=True)
    description = models.TextField(default="")
    Acceptance = models.CharField(max_length=60, choices=ROLE_CHOICES)
    Rewards = models.IntegerField(default=0)
    task_priority = models.IntegerField(default=0)

class TaskAssign(BaseModel):
    auth_id = models.ForeignKey(Auth, on_delete=models.CASCADE, blank=True, null=True)
    task_id = models.ForeignKey(Task, on_delete=models.CASCADE, blank=True, null=True)
