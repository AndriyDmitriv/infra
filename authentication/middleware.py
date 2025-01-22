from django.shortcuts import redirect
from django.urls import reverse

class RequireLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and request.path not in [reverse('authentication:login'), reverse('authentication:register')]:
            return redirect('authentication:login')
        return self.get_response(request)