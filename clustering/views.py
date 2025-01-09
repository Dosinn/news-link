from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from .clustering_ai import parse_and_update_clusters
from .models import Cluster


def show(request):

    return render(request, 'index1.html', {'clusters': Cluster.objects.all()})