from django.contrib import admin
from .models import  PointsTable, Task, TaskAssign

admin.site.register([ PointsTable, Task, TaskAssign])
