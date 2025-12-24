from allauth.account.views import SignupView
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from user import views

app_name = 'user'

urlpatterns = [
    path('register/', SignupView.as_view(template_name='user/register.html'), name='register'),
    path('login/', LoginView.as_view(template_name='user/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='mailing:home'), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile-edit/', views.ProfileUpdateView.as_view(), name='profile-update'),
    path('password-reset/',
         views.CustomPasswordResetView.as_view(),
         name='password_reset'),

    path('password-reset/done/',
         views.CustomPasswordResetDoneView.as_view(),
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/',
         views.CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),

    path('password-reset-complete/',
         views.CustomPasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
]
