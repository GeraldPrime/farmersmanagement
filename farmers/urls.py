# farmers/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # ============================================================================
    # ADMIN AUTHENTICATION
    # ============================================================================
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),

    # ============================================================================
    # ADMIN URLS
    # ============================================================================
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Farmers
    path('farmers/', views.farmers_list, name='farmers_list'),
    path('farmers/verify/', views.farmer_verify, name='farmer_verify'),
    path('farmers/create/', views.farmer_create, name='farmer_create'),
    path('farmers/<int:pk>/', views.farmer_detail, name='farmer_detail'),
    path('farmers/<int:pk>/edit/', views.farmer_edit, name='farmer_edit'),
    path('farmers/<int:pk>/delete/', views.farmer_delete, name='farmer_delete'),
    path('farmers/<int:pk>/toggle-status/', views.farmer_toggle_status, name='farmer_toggle_status'),

    # Groups
    path('groups/', views.groups_list, name='groups_list'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    path('groups/<int:pk>/edit/', views.group_edit, name='group_edit'),
    path('groups/<int:pk>/delete/', views.group_delete, name='group_delete'),

    # Group Types
    path('group-types/', views.group_types_list, name='group_types_list'),
    path('group-types/create/', views.group_type_create, name='group_type_create'),
    path('group-types/<int:pk>/', views.group_type_detail, name='group_type_detail'),
    path('group-types/<int:pk>/edit/', views.group_type_edit, name='group_type_edit'),
    path('group-types/<int:pk>/delete/', views.group_type_delete, name='group_type_delete'),

    # Vendors
    path('vendors/', views.vendors_list, name='vendors_list'),
    path('vendors/create/', views.vendor_create, name='vendor_create'),
    path('vendors/<int:pk>/', views.vendor_detail, name='vendor_detail'),
    path('vendors/<int:pk>/edit/', views.vendor_edit, name='vendor_edit'),
    path('vendors/<int:pk>/delete/', views.vendor_delete, name='vendor_delete'),
    path('vendors/<int:pk>/toggle-status/', views.vendor_toggle_status, name='vendor_toggle_status'),
    path('vendors/<int:pk>/credentials/', views.vendor_credentials, name='vendor_credentials'),

    # Incentives
    path('incentives/', views.incentives_list, name='incentives_list'),
    path('incentives/create/', views.incentive_create, name='incentive_create'),
    path('incentives/<int:pk>/', views.incentive_detail, name='incentive_detail'),
    path('incentives/<int:pk>/edit/', views.incentive_edit, name='incentive_edit'),
    path('incentives/<int:pk>/delete/', views.incentive_delete, name='incentive_delete'),

    # Disbursements
    path('disbursements/', views.disbursements_list, name='disbursements_list'),
    path('disbursements/disburse/', views.admin_disburse, name='admin_disburse'),

    # ============================================================================
    # API / AJAX ENDPOINTS
    # ============================================================================
    path('api/lgas/', views.get_lgas_by_state, name='get_lgas_by_state'),
    path('api/generate-password/', views.generate_password, name='generate_password'),
    path('api/verify-identity/', views.verify_farmer_identity, name='verify_farmer_identity'),
    path('api/admin/lookup-farmer/', views.admin_lookup_farmer, name='admin_lookup_farmer'),
    path('api/admin/process-disbursement/', views.admin_process_disbursement, name='admin_process_disbursement'),

    # ============================================================================
    # VENDOR URLS
    # ============================================================================
    path('vendor/login/', views.vendor_login, name='vendor_login'),
    path('vendor/logout/', views.vendor_logout, name='vendor_logout'),
    path('vendor/dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('vendor/farmers/', views.vendor_farmers_list, name='vendor_farmers_list'),
    path('vendor/farmers/verify/', views.vendor_farmer_verify, name='vendor_farmer_verify'),
    path('vendor/farmers/create/', views.vendor_farmer_create, name='vendor_farmer_create'),
    path('vendor/farmers/<int:pk>/', views.vendor_farmer_detail, name='vendor_farmer_detail'),
    path('vendor/profile/', views.vendor_profile, name='vendor_profile'),
]
