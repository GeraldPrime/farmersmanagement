# farmers/urls.py

from django.urls import path
from . import views
from . import redemption_center_views as rc_views

urlpatterns = [
    # // admin urls
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('farmers/', views.farmers_list, name='farmers_list'),
    path('farmers/create/', views.farmer_create, name='farmer_create'),
    path('farmers/<int:pk>/', views.farmer_detail, name='farmer_detail'),
    path('farmers/<int:pk>/edit/', views.farmer_edit, name='farmer_edit'),
    path('farmers/<int:pk>/delete/', views.farmer_delete, name='farmer_delete'),
    path('farmers/<int:pk>/toggle-status/', views.farmer_toggle_status, name='farmer_toggle_status'),
    path('groups/', views.groups_list, name='groups_list'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    path('groups/<int:pk>/edit/', views.group_edit, name='group_edit'),
    path('groups/<int:pk>/delete/', views.group_delete, name='group_delete'),
    path('group-types/', views.group_types_list, name='group_types_list'),
    path('group-types/create/', views.group_type_create, name='group_type_create'),
    path('group-types/<int:pk>/', views.group_type_detail, name='group_type_detail'),
    path('group-types/<int:pk>/edit/', views.group_type_edit, name='group_type_edit'),
    path('group-types/<int:pk>/delete/', views.group_type_delete, name='group_type_delete'),
    path('vendors/', views.vendors_list, name='vendors_list'),
    path('vendors/create/', views.vendor_create, name='vendor_create'),
    path('vendors/<int:pk>/', views.vendor_detail, name='vendor_detail'),
    path('vendors/<int:pk>/edit/', views.vendor_edit, name='vendor_edit'),
    path('vendors/<int:pk>/delete/', views.vendor_delete, name='vendor_delete'),
    path('vendors/<int:pk>/toggle-status/', views.vendor_toggle_status, name='vendor_toggle_status'),
    path('vendors/<int:pk>/credentials/', views.vendor_credentials, name='vendor_credentials'),
    path('api/generate-password/', views.generate_password, name='generate_password'),
    path('redemption-centers/', views.redemption_centers_list, name='redemption_centers_list'),
    path('redemption-centers/create/', views.redemption_center_create, name='redemption_center_create'),
    path('redemption-centers/<int:pk>/', views.redemption_center_detail, name='redemption_center_detail'),
    path('redemption-centers/<int:pk>/edit/', views.redemption_center_edit, name='redemption_center_edit'),
    path('redemption-centers/<int:pk>/delete/', views.redemption_center_delete, name='redemption_center_delete'),
    path('redemption-centers/<int:pk>/toggle-status/', views.redemption_center_toggle_status, name='redemption_center_toggle_status'),
    path('redemption-centers/<int:pk>/credentials/', views.redemption_center_credentials, name='redemption_center_credentials'),
    path('incentives/', views.incentives_list, name='incentives_list'),
    path('incentives/create/', views.incentive_create, name='incentive_create'),
    path('incentives/<int:pk>/', views.incentive_detail, name='incentive_detail'),
    path('incentives/<int:pk>/edit/', views.incentive_edit, name='incentive_edit'),
    path('incentives/<int:pk>/delete/', views.incentive_delete, name='incentive_delete'),
    path('disbursements/', views.disbursements_list, name='disbursements_list'),
    path('api/lgas/', views.get_lgas_by_state, name='get_lgas_by_state'),
    
    # ============================================================================
    # VENDOR URLS - Vendor Interface
    # ============================================================================
    # All URLs below this line are for vendor interface
    # Vendors can access their dashboard, view their registered farmers, and create new farmers
    
    # Vendor Authentication
    path('vendor/login/', views.vendor_login, name='vendor_login'),
    path('vendor/logout/', views.vendor_logout, name='vendor_logout'),
    
    # Vendor Dashboard
    path('vendor/dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    
    # Vendor Farmers Management
    path('vendor/farmers/', views.vendor_farmers_list, name='vendor_farmers_list'),
    path('vendor/farmers/create/', views.vendor_farmer_create, name='vendor_farmer_create'),
    path('vendor/farmers/<int:pk>/', views.vendor_farmer_detail, name='vendor_farmer_detail'),
    
    # Vendor Profile
    path('vendor/profile/', views.vendor_profile, name='vendor_profile'),
    
    # ============================================================================
    # REDEMPTION CENTER URLS - Redemption Center Interface
    # ============================================================================
    # All URLs below this line are for redemption center interface
    # Redemption centers can view allocations, inventory, and disburse incentives to farmers
    
    # Redemption Center Authentication
    path('redemption-center/login/', rc_views.redemption_center_login, name='redemption_center_login'),
    path('redemption-center/logout/', rc_views.redemption_center_logout, name='redemption_center_logout'),
    
    # Redemption Center Dashboard
    path('redemption-center/dashboard/', rc_views.redemption_center_dashboard, name='redemption_center_dashboard'),
    
    # Redemption Center Allocations
    path('redemption-center/allocations/', rc_views.redemption_center_allocations, name='redemption_center_allocations'),
    
    # Redemption Center Disbursements
    path('redemption-center/disburse/', rc_views.redemption_center_disburse, name='redemption_center_disburse'),
    path('redemption-center/disbursements/', rc_views.redemption_center_disbursements, name='redemption_center_disbursements'),
    
    # Redemption Center AJAX Endpoints
    path('api/lookup-farmer-by-nin/', rc_views.lookup_farmer_by_nin, name='lookup_farmer_by_nin'),
    path('api/process-disbursement/', rc_views.process_disbursement, name='process_disbursement'),
    
    # Redemption Center Profile
    path('redemption-center/profile/', rc_views.redemption_center_profile, name='redemption_center_profile'),
]
