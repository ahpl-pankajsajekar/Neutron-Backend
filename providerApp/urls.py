from django.urls import path
from . import views

urlpatterns = [
    path('dc-api-integration/', views.ADD_DC_APIIntegrations.as_view()),
    path('empanelment/add/', views.EmpanelmentCreateAPIView.as_view()),
    path('empanelment/get/', views.EmpanelmentDetailAPIView.as_view()),
    path('empanelment/delete/', views.EmpanelmentDeleteAPIView.as_view()),

    # testing
    path('selfemp/add/', views.FileUploadView.as_view()),


    # Search DC  ex. { "q": "Mumbai", "t": [ { "item_value": "100001", "item_label": "2 D Echocardiography" } ] }
    path('search/', views.SearchDCAPIView.as_view()),
    # DC
    path('DC/detail/', views.DCDetailAPIView.as_view()),
    path('DC/update/', views.DCUpdateAPIView.as_view()),
    # Self Empanelment
    path('selfempanelment/add/<int:id>/', views.SelfEmpanelmentCreateAPIView.as_view()),
    # For verification
    path('selfempanelments/', views.SelfEmpanelmentList.as_view()),
    path('selfempanelment/', views.SelfEmpanelmentAPIView.as_view()),
    path('selfempanelment/update/', views.SelfEmpanelmentUpdateAPIView.as_view()),

    # Change Dc Status
    path('dcstatus/', views.DCStatusChangeAPIView.as_view()),

]
