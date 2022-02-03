from django.contrib.auth.views import LogoutView, LoginView, PasswordResetView
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('logout/',
         LogoutView.as_view(template_name='users/logged_out.html'),
         name='logout'),
    path('signup/', views.SingUp.as_view(), name='signup'),
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'password_reset_form/',
        PasswordResetView.as_view(
            template_name='users/password_reset_form.html',
            success_url='../password_reset_done/'),
        name='password_reset_form'
    ),
    path(
        'password_reset_done/',
        views.password_reset_done,
        name='password_reset_done'
    ),
]
