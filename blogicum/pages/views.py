from django.shortcuts import render
from django.views.generic import TemplateView


def about(request):
    return render(request, 'pages/about.html')


def rules(request):
    return render(request, 'pages/rules.html')


def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)


def page_internal_server_error(request):
    return render(request, 'pages/500.html', status=500)


def page_csrf_forbidden(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403)
