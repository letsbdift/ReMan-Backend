from django.urls import path
from . import views

urlpatterns = [
    path('manifest.json', views.pwa_manifest, name='manifest'),
    path('icon-192.png', views.pwa_icon_192, name='icon_192'),
    path('icon-512.png', views.pwa_icon_512, name='icon_512'),

    path('sites/', views.SiteList.as_view(), name='site_list'),
    path('sites/import/', views.site_import, name='site_import'),
    path('sites/import/template/', views.site_import_template, name='site_import_template'),
    path('sites/add/', views.SiteCreate.as_view(), name='site_create'),
    path('sites/<int:pk>/edit/', views.SiteUpdate.as_view(), name='site_update'),
    path('sites/<int:pk>/delete/', views.SiteDelete.as_view(), name='site_delete'),

    path('', views.dashboard, name='dashboard'),
    path('search/', views.global_search, name='global_search'),
    path('activities/', views.ActivityList.as_view(), name='activity_list'),
    
    path('contacts/', views.contact_list, name='contact_list'),
    path('contacts/add/', views.ContactCreate.as_view(), name='contact_create'),
    path('contacts/<int:pk>/edit/', views.ContactUpdate.as_view(), name='contact_update'),
    path('contacts/<int:pk>/delete/', views.ContactDelete.as_view(), name='contact_delete'),
    
    path('leads/', views.lead_list, name='lead_list'),
    path('leads/add/', views.LeadCreate.as_view(), name='lead_create'),
    path('leads/<int:pk>/edit/', views.LeadUpdate.as_view(), name='lead_update'),
    path('leads/<int:pk>/delete/', views.LeadDelete.as_view(), name='lead_delete'),
    
    path('deals/', views.deal_list, name='deal_list'),
    path('deals/add/', views.LandDealCreate.as_view(), name='deal_create'),
    path('deals/<int:pk>/edit/', views.LandDealUpdate.as_view(), name='deal_update'),
    path('deals/<int:pk>/delete/', views.LandDealDelete.as_view(), name='deal_delete'),
    
    path('followups/', views.FollowUpList.as_view(), name='followup_list'),
    path('followups/add/', views.FollowUpCreate.as_view(), name='followup_create'),
    path('followups/<int:pk>/edit/', views.FollowUpUpdate.as_view(), name='followup_update'),
    path('followups/<int:pk>/delete/', views.FollowUpDelete.as_view(), name='followup_delete'),
    
    path('projects/', views.ProjectList.as_view(), name='project_list'),
    path('projects/add/', views.ProjectCreate.as_view(), name='project_create'),
    path('projects/<int:pk>/edit/', views.ProjectUpdate.as_view(), name='project_update'),
    path('projects/<int:pk>/delete/', views.ProjectDelete.as_view(), name='project_delete'),
    
    path('transactions/', views.TransactionList.as_view(), name='transaction_list'),
    path('transactions/add/', views.TransactionCreate.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.TransactionUpdate.as_view(), name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.TransactionDelete.as_view(), name='transaction_delete'),
    
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.ExpenseCreate.as_view(), name='expense_create'),
    path('expenses/<int:pk>/edit/', views.ExpenseUpdate.as_view(), name='expense_update'),
    path('expenses/<int:pk>/delete/', views.ExpenseDelete.as_view(), name='expense_delete'),
    
    path('shared-expenses/', views.shared_expense_list, name='shared_expense_list'),
    path('shared-expenses/group/<int:pk>/', views.SharedPurposeDetailView.as_view(), name='sharedpurpose_detail'),
    path('shared-expenses/group/<int:pk>/delete/', views.SharedPurposeDelete.as_view(), name='sharedpurpose_delete'),
    path('shared-expenses/settle/', views.SettlementCreate.as_view(), name='settlement_create'),
    
    
    path('shared-expenses/item/add/', views.SharedExpenseCreate.as_view(), name='sharedexpense_create'),
    path('shared-expenses/item/<int:pk>/edit/', views.SharedExpenseUpdate.as_view(), name='sharedexpense_update'),
    path('shared-expenses/item/<int:pk>/delete/', views.SharedExpenseDelete.as_view(), name='sharedexpense_delete'),

    path('documents/', views.DocumentList.as_view(), name='document_list'),
    path('documents/add/', views.DocumentCreate.as_view(), name='document_create'),
    path('documents/<int:pk>/edit/', views.DocumentUpdate.as_view(), name='document_update'),
    path('documents/<int:pk>/delete/', views.DocumentDelete.as_view(), name='document_delete'),
]
