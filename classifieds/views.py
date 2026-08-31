from django.shortcuts import render

# Create your views here.

def index(request):
    """Homepage view — renders classifieds/templates/classifieds/index.html"""
    return render(request, 'classifieds/index.html')