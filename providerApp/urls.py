from django.urls import path
from . import views

urlpatterns = [
    path('dc-api-integration/', views.ADD_DC_APIIntegrations.as_view()),
    path('search/', views.SearchDCAPIView.as_view()),
    path('DCView/', views.DCDetailAPIView.as_view()),
    path('empanelment/add/', views.EmpanelmentCreateAPIView.as_view()),
    path('empanelment/get/', views.EmpanelmentDetailAPIView.as_view()),
    path('empanelment/update/', views.EmpanelmentUpdateAPIView.as_view()),
    path('empanelment/delete/', views.EmpanelmentDeleteAPIView.as_view()),
]
