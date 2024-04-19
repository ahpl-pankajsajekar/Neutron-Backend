from django.urls import include, path
from . import views
from rest_framework_simplejwt.views import  TokenRefreshView


urlpatterns = [
    # Login user
    path('login/', views.loginAPIView.as_view()),
    ## Register User
    path('register/', views.UserRegistrationAPIView.as_view(), name='register'),

    # Forgot Password
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    # Tocken
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
