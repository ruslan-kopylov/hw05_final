from django.shortcuts import render
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CreationForm


class SingUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


def password_reset_done(request):
    template = 'users/password_reset_done.html'
    return render(request, template)
