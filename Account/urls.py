from django.urls import include, path
from . import views
from rest_framework_simplejwt_mongoengine.views import  TokenRefreshView


urlpatterns = [
    # Login user
    path('login/', views.loginAPIView.as_view()),
    ## Register User
    path('register/', views.UserRegistrationAPIView.as_view(), name='register'),
    ## change password User
    path('updatepassword/', views.ChangePasswordAPIView.as_view(), name='changepassword'),

    # Get user
    path('getuser/', views.GetUserAPIView.as_view(), name='GetUser'),
    # update by user
    path('user/update/', views.UpdateUserAPIView.as_view(), name='UpdateUser'),


    # temp
    path('envelop/', views.CreateEnvelopeView.as_view(), name='CreateEnvelopeView'),

    # Forgot Password
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    # Tocken
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


    path('pdf/', views.writeOnPdf.as_view(),),



]
