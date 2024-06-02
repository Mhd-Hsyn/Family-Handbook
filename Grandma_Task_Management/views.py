from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(request):
    return HttpResponse("<h1>Project Family Handbook --Grandma Reward & Task Management</h1>")
