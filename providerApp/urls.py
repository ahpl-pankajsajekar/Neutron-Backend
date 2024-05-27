from django.urls import path
from . import views

urlpatterns = [
    path('dc-api-integration/', views.ADD_DC_APIIntegrations.as_view()),

    path('empanelment/add/', views.EmpanelmentCreateAPIView.as_view()),
    path('empanelment/delete/', views.EmpanelmentDeleteAPIView.as_view()),

    # Verified selfEmpanelment select
    path('selfemp/select/docusign/', views.SelfEmpanelmentSelectForDocusign.as_view()), # legal team get only verified selfEmp

    path('selfemp/select/', views.SelfEmpanelmentSelect.as_view()), # network team
    path('selfemp/select/legal/', views.SelfEmpanelmentSelectForLegal.as_view()),  # legal team
    # store data from verification page [Post]
    path('selfemp/verification/', views.SelfEmpanelmentVerificationAPIView.as_view()),
    path('selfemp/verification/legal/', views.SelfEmpanelmentVerificationByLegalAPIView.as_view()),
    # gives documents data for verification [get]
    path('empanelment/', views.selfEmpanelmentDetailAPIView.as_view()),
    path('empanelment/details/legal/', views.selfEmpanelmentDetailForLegalAPIView.as_view()),


    # testing
    path('selfemp/add/', views.FileUploadView.as_view()),


    # Search DC  ex. { "q": "Mumbai", "t": [ { "item_value": "100001", "item_label": "2 D Echocardiography" } ] }
    path('search/', views.SearchDCAPIView.as_view()),
    # DC
    path('DC/analytic/', views.DCAnalyticsAPIView.as_view()),
    path('DC/detail/', views.DCDetailAPIView.as_view()),
    path('DC/update/', views.DCUpdateAPIView.as_view()),
    # Self Empanelment
    path('selfempanelment/add/<int:id>/', views.SelfEmpanelmentCreateAPIView.as_view()),
    # update self empanelemnt
    path('selfempanelment/update/<int:id>/', views.SelfEmpanelmentUpdateAPIView.as_view()),
    # For verification
    path('selfempanelments/', views.SelfEmpanelmentList.as_view()),
    path('selfempanelment/', views.SelfEmpanelmentAPIView.as_view()),
    
    # Change Dc Status
    path('dcstatus/', views.DCStatusChangeAPIView.as_view()),

    # Docusign Agreement it will not used
    path('docusignAgreement/', views.docusignAgreementFileAPIView.as_view()),
    # Docusign Agreement send 
    path('docusignAgreement/sent/', views.docusignAgreementSentAPIView.as_view()),
    # Docusign Agreement check status
    path('docusignAgreement/envelope/checkstatus/', views.docusignCheckStatusAPIView.as_view()),
    # Docusign Agreement check status not used
    path('docusignAgreement/envelope/document/save/', views.SaveToMongoDocusignDocumentContentAPIView.as_view()),
    # Docusign Agreement  save pdf and view
    path('docusignAgreement/envelope/document/saveAndview/', views.SaveIntoDBAndViewDocusignDocumentContentAPIView.as_view()),

    # webhook
    path('docusignAgreement/envelope/webhook/', views.DocusignEnvelopeWebhookAPIView.as_view()),
    path('freshdesk/webhook/', views.FreshDeskGetTicketCreatedWebhookAPIView.as_view()),
    path('freshdesk/webhook/ticket/', views.FreshDeskGetTicketUpdateWebhookAPIView.as_view()),

    path('candidateForm/ticket/', views.candidateDCFormAPIView.as_view() ),

    # tickets
    path('tickets/', views.ShowAllTicketsAPIView.as_view() ),
    path('operation/ticket/', views.TicketCreatedAPIView.as_view() ),
]