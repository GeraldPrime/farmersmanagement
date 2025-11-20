from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import secrets
import string
from .models import Farmer, Group, GroupType, Vendor, RedemptionCenter, State, LGA, Incentive, Disbursement
from .forms import FarmerForm, GroupForm, GroupTypeForm, VendorForm, RedemptionCenterForm, IncentiveForm


def dashboard(request):
    """Dashboard view with statistics"""
    context = {
        'total_farmers': Farmer.objects.count(),
        'active_farmers': Farmer.objects.filter(farmer_status='active').count(),
        'total_groups': Group.objects.count(),
        'active_groups': Group.objects.filter(is_active=True).count(),
        'total_vendors': Vendor.objects.count(),
        'active_vendors': Vendor.objects.filter(vendor_status='active').count(),
        'total_redemption_centers': RedemptionCenter.objects.count(),
        'total_group_types': GroupType.objects.count(),
        'recent_farmers': Farmer.objects.all()[:5],
    }
    return render(request, 'admin/dashboard.html', context)


def farmers_list(request):
    """List all farmers"""
    farmers = Farmer.objects.select_related('group_type', 'group_name', 'vendor', 'state', 'LGA').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        farmers = farmers.filter(
            Q(firstname__icontains=search_query) |
            Q(surname__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(NIN__icontains=search_query) |
            Q(farmer_id__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        farmers = farmers.filter(farmer_status=status_filter)
    
    # Filter by group type
    group_type_filter = request.GET.get('group_type', '')
    if group_type_filter:
        farmers = farmers.filter(group_type_id=group_type_filter)
    
    # Filter by group
    group_filter = request.GET.get('group', '')
    if group_filter:
        farmers = farmers.filter(group_name_id=group_filter)
    
    context = {
        'farmers': farmers,
        'search_query': search_query,
        'status_filter': status_filter,
        'group_type_filter': group_type_filter,
        'group_filter': group_filter,
        'group_types': GroupType.objects.all().order_by('name'),
        'groups': Group.objects.all().order_by('group_name'),
    }
    return render(request, 'admin/farmers/list.html', context)


def farmer_create(request):
    """Create a new farmer"""
    if request.method == 'POST':
        form = FarmerForm(request.POST, request.FILES)
        if form.is_valid():
            farmer = form.save()
            messages.success(request, f'Farmer {farmer.get_full_name()} has been created successfully!')
            return redirect('farmers_list')
        else:
            # Form has errors - show them
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = FarmerForm()
    
    context = {
        'form': form,
        'title': 'Add New Farmer',
    }
    return render(request, 'admin/farmers/form.html', context)


def farmer_edit(request, pk):
    """Edit an existing farmer"""
    farmer = get_object_or_404(Farmer, pk=pk)
    
    if request.method == 'POST':
        form = FarmerForm(request.POST, request.FILES, instance=farmer)
        if form.is_valid():
            farmer = form.save()
            messages.success(request, f'Farmer {farmer.get_full_name()} has been updated successfully!')
            return redirect('farmers_list')
        else:
            # Form has errors - show them
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = FarmerForm(instance=farmer)
    
    context = {
        'form': form,
        'farmer': farmer,
        'title': 'Edit Farmer',
    }
    return render(request, 'admin/farmers/form.html', context)


def farmer_detail(request, pk):
    """View farmer details"""
    farmer = get_object_or_404(Farmer.objects.select_related('group_type', 'group_name', 'vendor', 'state', 'LGA'), pk=pk)
    context = {
        'farmer': farmer,
    }
    return render(request, 'admin/farmers/detail.html', context)


@require_http_methods(["POST"])
def farmer_toggle_status(request, pk):
    """Toggle farmer status (active/inactive)"""
    farmer = get_object_or_404(Farmer, pk=pk)
    
    # Toggle status
    if farmer.farmer_status == 'active':
        farmer.farmer_status = 'inactive'
        new_status = 'inactive'
        status_text = 'deactivated'
    else:
        farmer.farmer_status = 'active'
        new_status = 'active'
        status_text = 'activated'
    
    farmer.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Farmer {farmer.get_full_name()} has been {status_text} successfully.',
        'new_status': new_status,
        'status_text': farmer.get_farmer_status_display()
    })


def farmer_delete(request, pk):
    """Delete a farmer"""
    farmer = get_object_or_404(Farmer, pk=pk)
    if request.method == 'POST':
        farmer_name = farmer.get_full_name()
        farmer.delete()
        messages.success(request, f'Farmer {farmer_name} has been deleted successfully!')
        return redirect('farmers_list')
    context = {
        'farmer': farmer,
    }
    return render(request, 'admin/farmers/delete.html', context)


def groups_list(request):
    """List all groups"""
    groups = Group.objects.select_related('group_type', 'group_leader').annotate(
        member_count=Count('members')
    ).all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        groups = groups.filter(
            Q(group_name__icontains=search_query) |
            Q(group_type__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        if status_filter == 'active':
            groups = groups.filter(is_active=True)
        elif status_filter == 'inactive':
            groups = groups.filter(is_active=False)
    
    # Filter by group type
    type_filter = request.GET.get('type', '')
    if type_filter:
        groups = groups.filter(group_type_id=type_filter)
    
    context = {
        'groups': groups,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'group_types': GroupType.objects.all().order_by('name'),
    }
    return render(request, 'admin/groups/list.html', context)


def group_create(request):
    """Create a new group"""
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            messages.success(request, f'Group "{group.group_name}" has been created successfully!')
            return redirect('groups_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = GroupForm()
    
    context = {
        'form': form,
        'title': 'Add New Group',
    }
    return render(request, 'admin/groups/form.html', context)


def group_edit(request, pk):
    """Edit an existing group"""
    group = get_object_or_404(Group, pk=pk)
    
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            group = form.save()
            messages.success(request, f'Group "{group.group_name}" has been updated successfully!')
            return redirect('groups_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = GroupForm(instance=group)
    
    context = {
        'form': form,
        'group': group,
        'title': 'Edit Group',
    }
    return render(request, 'admin/groups/form.html', context)


def group_detail(request, pk):
    """View group details"""
    group = get_object_or_404(
        Group.objects.select_related('group_type', 'group_leader').annotate(
            member_count=Count('members')
        ),
        pk=pk
    )
    members = Farmer.objects.filter(group_name=group).select_related('state', 'LGA', 'vendor')
    
    context = {
        'group': group,
        'members': members,
    }
    return render(request, 'admin/groups/detail.html', context)


def group_delete(request, pk):
    """Delete a group"""
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group_name = group.group_name
        group.delete()
        messages.success(request, f'Group "{group_name}" has been deleted successfully!')
        return redirect('groups_list')
    context = {
        'group': group,
    }
    return render(request, 'admin/groups/delete.html', context)


def group_types_list(request):
    """List all group types"""
    group_types = GroupType.objects.annotate(
        groups_count=Count('groups')
    ).all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        group_types = group_types.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    context = {
        'group_types': group_types,
        'search_query': search_query,
    }
    return render(request, 'admin/group_types/list.html', context)


def group_type_create(request):
    """Create a new group type"""
    if request.method == 'POST':
        form = GroupTypeForm(request.POST)
        if form.is_valid():
            group_type = form.save()
            messages.success(request, f'Group Type "{group_type.name}" has been created successfully!')
            return redirect('group_types_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = GroupTypeForm()
    
    context = {
        'form': form,
        'title': 'Add New Group Type',
    }
    return render(request, 'admin/group_types/form.html', context)


def group_type_edit(request, pk):
    """Edit an existing group type"""
    group_type = get_object_or_404(GroupType, pk=pk)
    
    if request.method == 'POST':
        form = GroupTypeForm(request.POST, instance=group_type)
        if form.is_valid():
            group_type = form.save()
            messages.success(request, f'Group Type "{group_type.name}" has been updated successfully!')
            return redirect('group_types_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = GroupTypeForm(instance=group_type)
    
    context = {
        'form': form,
        'group_type': group_type,
        'title': 'Edit Group Type',
    }
    return render(request, 'admin/group_types/form.html', context)


def group_type_detail(request, pk):
    """View group type details"""
    group_type = get_object_or_404(
        GroupType.objects.annotate(
            groups_count=Count('groups')
        ),
        pk=pk
    )
    groups = Group.objects.filter(group_type=group_type).select_related('group_type').annotate(
        member_count=Count('members')
    )
    
    context = {
        'group_type': group_type,
        'groups': groups,
    }
    return render(request, 'admin/group_types/detail.html', context)


def group_type_delete(request, pk):
    """Delete a group type"""
    from django.db.models import ProtectedError
    
    group_type = get_object_or_404(GroupType, pk=pk)
    
    # Check if group type is being used
    groups_count = group_type.groups.count()
    
    if request.method == 'POST':
        try:
            group_type_name = group_type.name
            group_type.delete()
            messages.success(request, f'Group Type "{group_type_name}" has been deleted successfully!')
            return redirect('group_types_list')
        except ProtectedError:
            messages.error(request, f'Cannot delete "{group_type.name}" because it is being used by {groups_count} group(s). Please delete or change the type of those groups first.')
            return redirect('group_types_list')
    
    context = {
        'group_type': group_type,
        'groups_count': groups_count,
    }
    return render(request, 'admin/group_types/delete.html', context)


def vendors_list(request):
    """List all vendors"""
    vendors = Vendor.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        vendors = vendors.filter(
            Q(vendor_firstname__icontains=search_query) |
            Q(vendor_surname__icontains=search_query) |
            Q(vendor_middlename__icontains=search_query) |
            Q(vendor_company_name__icontains=search_query) |
            Q(vendor_registration_no__icontains=search_query) |
            Q(vendor_email_address__icontains=search_query) |
            Q(vendor_phone__icontains=search_query)
        )
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        vendors = vendors.filter(vendor_status=status_filter)
    
    context = {
        'vendors': vendors,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'admin/vendors/list.html', context)


def vendor_create(request):
    """Create a new vendor"""
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            vendor = form.save()
            messages.success(request, f'Vendor "{vendor.get_full_name()}" has been created successfully!')
            return redirect('vendors_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = VendorForm()
    
    context = {
        'form': form,
        'title': 'Add New Vendor',
    }
    return render(request, 'admin/vendors/form.html', context)


def vendor_edit(request, pk):
    """Edit an existing vendor"""
    vendor = get_object_or_404(Vendor, pk=pk)
    
    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            vendor = form.save()
            messages.success(request, f'Vendor "{vendor.get_full_name()}" has been updated successfully!')
            return redirect('vendors_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = VendorForm(instance=vendor)
    
    context = {
        'form': form,
        'vendor': vendor,
        'title': 'Edit Vendor',
    }
    return render(request, 'admin/vendors/form.html', context)


def vendor_detail(request, pk):
    """View vendor details"""
    vendor = get_object_or_404(Vendor, pk=pk)
    registered_farmers = Farmer.objects.filter(vendor=vendor).select_related('state', 'LGA', 'group_name')
    farmers_count = registered_farmers.count()
    
    context = {
        'vendor': vendor,
        'registered_farmers': registered_farmers,
        'farmers_count': farmers_count,
    }
    return render(request, 'admin/vendors/detail.html', context)


def vendor_delete(request, pk):
    """Delete a vendor"""
    vendor = get_object_or_404(Vendor, pk=pk)
    farmers_count = vendor.registered_farmers.count()
    
    if request.method == 'POST':
        vendor_name = vendor.get_full_name()
        vendor.delete()
        messages.success(request, f'Vendor "{vendor_name}" has been deleted successfully!')
        return redirect('vendors_list')
    
    context = {
        'vendor': vendor,
        'farmers_count': farmers_count,
    }
    return render(request, 'admin/vendors/delete.html', context)


@require_http_methods(["POST"])
def vendor_toggle_status(request, pk):
    """Toggle vendor status (active/inactive)"""
    vendor = get_object_or_404(Vendor, pk=pk)
    
    if vendor.vendor_status == 'active':
        vendor.vendor_status = 'inactive'
    else:
        vendor.vendor_status = 'active'
    
    vendor.save()
    
    return JsonResponse({
        'success': True,
        'status': vendor.vendor_status,
        'message': f'Vendor status updated to {vendor.vendor_status.title()}'
    })


@require_http_methods(["GET", "POST"])
def vendor_credentials(request, pk):
    """Get or update vendor login credentials"""
    vendor = get_object_or_404(Vendor, pk=pk)
    
    if request.method == 'GET':
        # Return current credentials info
        username = vendor.user.username if vendor.user else None
        suggested_username = f"{vendor.vendor_firstname.lower()}{vendor.vendor_surname.lower()}"
        
        return JsonResponse({
            'success': True,
            'has_credentials': vendor.user is not None,
            'username': username,
            'suggested_username': suggested_username,
        })
    
    elif request.method == 'POST':
        # Create or update credentials
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Username is required'
            }, status=400)
        
        if not password:
            return JsonResponse({
                'success': False,
                'error': 'Password is required'
            }, status=400)
        
        # Check if username already exists (excluding current vendor's user)
        existing_user = User.objects.filter(username=username).exclude(
            id=vendor.user.id if vendor.user else None
        ).first()
        
        if existing_user:
            return JsonResponse({
                'success': False,
                'error': 'Username already exists. Please choose a different username.'
            }, status=400)
        
        # Create or update user
        if vendor.user:
            # Update existing user
            vendor.user.username = username
            vendor.user.set_password(password)
            vendor.user.save()
            action = 'updated'
        else:
            # Create new user
            user = User.objects.create_user(
                username=username,
                password=password,
                email=vendor.vendor_email_address,
                first_name=vendor.vendor_firstname,
                last_name=vendor.vendor_surname,
                is_staff=False,
                is_superuser=False
            )
            vendor.user = user
            vendor.save()
            action = 'created'
        
        return JsonResponse({
            'success': True,
            'message': f'Credentials {action} successfully',
            'username': username
        })


def generate_random_password():
    """Generate a random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for i in range(12))
    return password


@require_http_methods(["GET"])
def generate_password(request):
    """Generate a random password"""
    password = generate_random_password()
    return JsonResponse({
        'success': True,
        'password': password
    })


def redemption_centers_list(request):
    """List all redemption centers"""
    centers = RedemptionCenter.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        centers = centers.filter(
            Q(fullname__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_no__icontains=search_query) |
            Q(redemption_center_address__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        centers = centers.filter(redemption_center_status=status_filter)
    
    context = {
        'centers': centers,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'admin/redemption_centers/list.html', context)


def redemption_center_create(request):
    """Create a new redemption center"""
    if request.method == 'POST':
        form = RedemptionCenterForm(request.POST)
        if form.is_valid():
            center = form.save()
            messages.success(request, f'Redemption Center "{center.fullname}" has been created successfully!')
            return redirect('redemption_centers_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = RedemptionCenterForm()
    
    context = {
        'form': form,
        'title': 'Add New Redemption Center',
    }
    return render(request, 'admin/redemption_centers/form.html', context)


def redemption_center_edit(request, pk):
    """Edit an existing redemption center"""
    center = get_object_or_404(RedemptionCenter, pk=pk)
    
    if request.method == 'POST':
        form = RedemptionCenterForm(request.POST, instance=center)
        if form.is_valid():
            center = form.save()
            messages.success(request, f'Redemption Center "{center.fullname}" has been updated successfully!')
            return redirect('redemption_centers_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = RedemptionCenterForm(instance=center)
    
    context = {
        'form': form,
        'center': center,
        'title': 'Edit Redemption Center',
    }
    return render(request, 'admin/redemption_centers/form.html', context)


def redemption_center_detail(request, pk):
    """View redemption center details"""
    center = get_object_or_404(RedemptionCenter, pk=pk)
    
    # Get all disbursements for this center
    disbursements = Disbursement.objects.filter(
        redemption_center=center
    ).select_related('farmer', 'incentive', 'disbursed_by').order_by('-disbursement_date')[:50]  # Latest 50
    
    # Get all incentive allocations
    all_incentives = Incentive.objects.filter(redemption_center=center).order_by('-date_sent', '-created_at')
    
    # Get inventory (all incentives with remaining quantity)
    inventory = []
    all_incentives_with_stats = []
    
    for incentive in all_incentives:
        remaining = incentive.get_remaining_quantity()
        disbursed = incentive.get_disbursed_quantity()
        incentive_data = {
            'incentive': incentive,
            'total_quantity': incentive.quantity,
            'disbursed_quantity': disbursed,
            'remaining_quantity': remaining,
            'percentage_remaining': (remaining / incentive.quantity * 100) if incentive.quantity > 0 else 0,
        }
        all_incentives_with_stats.append(incentive_data)
        
        # Only add to inventory if there's remaining quantity
        if remaining > 0:
            inventory.append(incentive_data)
    
    # Get statistics
    total_disbursements = Disbursement.objects.filter(redemption_center=center).count()
    total_items_disbursed = Disbursement.objects.filter(
        redemption_center=center
    ).aggregate(total=Sum('quantity'))['total'] or 0
    total_farmers_served = Disbursement.objects.filter(
        redemption_center=center
    ).values('farmer').distinct().count()
    total_allocations = all_incentives.count()
    total_items_allocated = all_incentives.aggregate(total=Sum('quantity'))['total'] or 0
    
    context = {
        'center': center,
        'disbursements': disbursements,
        'incentives': all_incentives_with_stats,
        'inventory': inventory,
        'total_disbursements': total_disbursements,
        'total_items_disbursed': total_items_disbursed,
        'total_farmers_served': total_farmers_served,
        'total_allocations': total_allocations,
        'total_items_allocated': total_items_allocated,
    }
    return render(request, 'admin/redemption_centers/detail.html', context)


def redemption_center_delete(request, pk):
    """Delete a redemption center"""
    center = get_object_or_404(RedemptionCenter, pk=pk)
    
    if request.method == 'POST':
        center_name = center.fullname
        center.delete()
        messages.success(request, f'Redemption Center "{center_name}" has been deleted successfully!')
        return redirect('redemption_centers_list')
    
    context = {
        'center': center,
    }
    return render(request, 'admin/redemption_centers/delete.html', context)


@require_http_methods(["POST"])
def redemption_center_toggle_status(request, pk):
    """Toggle redemption center status (active/inactive)"""
    center = get_object_or_404(RedemptionCenter, pk=pk)
    
    if center.redemption_center_status == 'active':
        center.redemption_center_status = 'inactive'
    else:
        center.redemption_center_status = 'active'
    
    center.save()
    
    return JsonResponse({
        'success': True,
        'status': center.redemption_center_status,
        'message': f'Redemption center status updated to {center.redemption_center_status.title()}'
    })


@require_http_methods(["GET", "POST"])
def redemption_center_credentials(request, pk):
    """Get or update redemption center login credentials"""
    center = get_object_or_404(RedemptionCenter, pk=pk)
    
    if request.method == 'GET':
        # Return current credentials info
        username = center.user.username if center.user else None
        # Generate suggested username from fullname (remove spaces, lowercase)
        suggested_username = center.fullname.lower().replace(' ', '').replace('-', '').replace('_', '')
        
        return JsonResponse({
            'success': True,
            'has_credentials': center.user is not None,
            'username': username,
            'suggested_username': suggested_username,
        })
    
    elif request.method == 'POST':
        # Create or update credentials
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Username is required'
            }, status=400)
        
        if not password:
            return JsonResponse({
                'success': False,
                'error': 'Password is required'
            }, status=400)
        
        # Check if username already exists (excluding current center's user)
        existing_user = User.objects.filter(username=username).exclude(
            id=center.user.id if center.user else None
        ).first()
        
        if existing_user:
            return JsonResponse({
                'success': False,
                'error': 'Username already exists. Please choose a different username.'
            }, status=400)
        
        # Create or update user
        if center.user:
            # Update existing user
            center.user.username = username
            center.user.set_password(password)
            center.user.save()
            action = 'updated'
        else:
            # Create new user
            user = User.objects.create_user(
                username=username,
                password=password,
                email=center.email,
                first_name=center.fullname.split()[0] if center.fullname.split() else '',
                last_name=' '.join(center.fullname.split()[1:]) if len(center.fullname.split()) > 1 else '',
                is_staff=False,
                is_superuser=False
            )
            center.user = user
            center.save()
            action = 'created'
        
        return JsonResponse({
            'success': True,
            'message': f'Credentials {action} successfully',
            'username': username
        })


def get_lgas_by_state(request):
    """API endpoint to get LGAs for a given state"""
    state_id = request.GET.get('state_id')
    if state_id:
        lgas = LGA.objects.filter(state_id=state_id).order_by('name')
        lga_list = [{'id': lga.id, 'name': lga.name} for lga in lgas]
        return JsonResponse({'lgas': lga_list})
    return JsonResponse({'lgas': []})


def incentives_list(request):
    """List all incentives"""
    incentives = Incentive.objects.select_related('redemption_center').all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        incentives = incentives.filter(
            Q(incentive_name__icontains=search_query) |
            Q(redemption_center__fullname__icontains=search_query)
        )
    
    # Filter by redemption center
    center_filter = request.GET.get('center', '')
    if center_filter:
        incentives = incentives.filter(redemption_center_id=center_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        incentives = incentives.filter(date_sent__gte=date_from)
    if date_to:
        incentives = incentives.filter(date_sent__lte=date_to)
    
    context = {
        'incentives': incentives,
        'search_query': search_query,
        'center_filter': center_filter,
        'date_from': date_from,
        'date_to': date_to,
        'redemption_centers': RedemptionCenter.objects.all().order_by('fullname'),
    }
    return render(request, 'admin/incentives/list.html', context)


def incentive_create(request):
    """Create a new incentive"""
    if request.method == 'POST':
        form = IncentiveForm(request.POST)
        if form.is_valid():
            redemption_center = form.cleaned_data.get('redemption_center')
            # Double-check that redemption center is active
            if redemption_center and redemption_center.redemption_center_status != 'active':
                messages.error(request, f'Cannot assign incentive to inactive redemption center "{redemption_center.fullname}". Please select an active redemption center.')
                context = {
                    'form': form,
                    'title': 'Add New Incentive',
                }
                return render(request, 'admin/incentives/form.html', context)
            
            incentive = form.save()
            messages.success(request, f'Incentive "{incentive.incentive_name}" has been created successfully!')
            return redirect('incentives_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = IncentiveForm()
    
    context = {
        'form': form,
        'title': 'Add New Incentive',
    }
    return render(request, 'admin/incentives/form.html', context)


def incentive_edit(request, pk):
    """Edit an existing incentive"""
    incentive = get_object_or_404(Incentive, pk=pk)
    
    if request.method == 'POST':
        form = IncentiveForm(request.POST, instance=incentive)
        if form.is_valid():
            redemption_center = form.cleaned_data.get('redemption_center')
            # Double-check that redemption center is active
            if redemption_center and redemption_center.redemption_center_status != 'active':
                messages.error(request, f'Cannot assign incentive to inactive redemption center "{redemption_center.fullname}". Please select an active redemption center.')
                context = {
                    'form': form,
                    'incentive': incentive,
                    'title': 'Edit Incentive',
                }
                return render(request, 'admin/incentives/form.html', context)
            
            incentive = form.save()
            messages.success(request, f'Incentive "{incentive.incentive_name}" has been updated successfully!')
            return redirect('incentives_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = IncentiveForm(instance=incentive)
    
    context = {
        'form': form,
        'incentive': incentive,
        'title': 'Edit Incentive',
    }
    return render(request, 'admin/incentives/form.html', context)


def incentive_detail(request, pk):
    """View incentive details"""
    incentive = get_object_or_404(
        Incentive.objects.select_related('redemption_center'),
        pk=pk
    )
    
    context = {
        'incentive': incentive,
    }
    return render(request, 'admin/incentives/detail.html', context)


def incentive_delete(request, pk):
    """Delete an incentive"""
    incentive = get_object_or_404(Incentive, pk=pk)
    
    if request.method == 'POST':
        incentive_name = incentive.incentive_name
        incentive.delete()
        messages.success(request, f'Incentive "{incentive_name}" has been deleted successfully!')
        return redirect('incentives_list')
    
    context = {
        'incentive': incentive,
    }
    return render(request, 'admin/incentives/delete.html', context)


def disbursements_list(request):
    """List all disbursements across all redemption centers"""
    disbursements = Disbursement.objects.select_related(
        'farmer', 'incentive', 'redemption_center', 'disbursed_by'
    ).order_by('-disbursement_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        disbursements = disbursements.filter(
            Q(farmer__firstname__icontains=search_query) |
            Q(farmer__surname__icontains=search_query) |
            Q(farmer__NIN__icontains=search_query) |
            Q(incentive__incentive_name__icontains=search_query) |
            Q(redemption_center__fullname__icontains=search_query)
        )
    
    # Filter by redemption center
    center_filter = request.GET.get('center', '')
    if center_filter:
        disbursements = disbursements.filter(redemption_center_id=center_filter)
    
    # Filter by incentive
    incentive_filter = request.GET.get('incentive', '')
    if incentive_filter:
        disbursements = disbursements.filter(incentive_id=incentive_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        disbursements = disbursements.filter(disbursement_date__date__gte=date_from)
    if date_to:
        disbursements = disbursements.filter(disbursement_date__date__lte=date_to)
    
    # Get statistics
    total_disbursements = disbursements.count()
    total_quantity = disbursements.aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    # Get unique farmers count
    unique_farmers = disbursements.values('farmer').distinct().count()
    
    context = {
        'disbursements': disbursements,
        'search_query': search_query,
        'center_filter': center_filter,
        'incentive_filter': incentive_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_disbursements': total_disbursements,
        'total_quantity': total_quantity,
        'unique_farmers': unique_farmers,
        'redemption_centers': RedemptionCenter.objects.all().order_by('fullname'),
        'incentives': Incentive.objects.all().order_by('incentive_name'),
    }
    return render(request, 'admin/disbursements/list.html', context)


# ============================================================================
# VENDOR VIEWS - Vendor Interface
# ============================================================================
# All views below this line are for vendor interface
# Vendors can access their dashboard, view their registered farmers, and create new farmers

def vendor_login(request):
    """Vendor login view"""
    if request.user.is_authenticated and hasattr(request.user, 'vendor_profile'):
        # Check if vendor is active before allowing access
        vendor = request.user.vendor_profile
        if vendor.vendor_status == 'active':
            return redirect('vendor_dashboard')
        else:
            # Logout inactive vendor
            logout(request)
            messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
            return redirect('vendor_login')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if user is linked to a vendor
            if hasattr(user, 'vendor_profile'):
                vendor = user.vendor_profile
                
                # Check if vendor is active
                if vendor.vendor_status != 'active':
                    messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
                    return render(request, 'vendors/login.html')
                
                # All checks passed - login successful
                login(request, user)
                messages.success(request, f'Welcome back, {vendor.get_full_name()}!')
                return redirect('vendor_dashboard')
            else:
                messages.error(request, 'No login credentials have been created for your account. Please contact the admin to set up your login credentials.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'vendors/login.html')


@login_required
def vendor_logout(request):
    """Vendor logout view"""
    if hasattr(request.user, 'vendor_profile'):
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('vendor_login')


@login_required
def vendor_dashboard(request):
    """Vendor dashboard showing statistics"""
    # Ensure user is a vendor
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, 'Access denied. Vendor account required.')
        return redirect('vendor_login')
    
    vendor = request.user.vendor_profile
    
    # Check if vendor is active
    if vendor.vendor_status != 'active':
        logout(request)
        messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
        return redirect('vendor_login')
    
    # Get vendor's registered farmers
    farmers = Farmer.objects.filter(vendor=vendor)
    total_farmers = farmers.count()
    active_farmers = farmers.filter(farmer_status='active').count()
    inactive_farmers = farmers.filter(farmer_status='inactive').count()
    
    # Get farmers by state
    farmers_by_state = farmers.values('state__name').annotate(count=Count('farmer_id')).order_by('-count')[:5]
    
    # Get recent farmers
    recent_farmers = farmers.order_by('-date_registered')[:5]
    
    context = {
        'vendor': vendor,
        'total_farmers': total_farmers,
        'active_farmers': active_farmers,
        'inactive_farmers': inactive_farmers,
        'farmers_by_state': farmers_by_state,
        'recent_farmers': recent_farmers,
    }
    return render(request, 'vendors/dashboard.html', context)


@login_required
def vendor_farmers_list(request):
    """List all farmers registered by the vendor"""
    # Ensure user is a vendor
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, 'Access denied. Vendor account required.')
        return redirect('vendor_login')
    
    vendor = request.user.vendor_profile
    
    # Check if vendor is active
    if vendor.vendor_status != 'active':
        logout(request)
        messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
        return redirect('vendor_login')
    farmers = Farmer.objects.filter(vendor=vendor).select_related('group_type', 'group_name', 'state', 'LGA')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        farmers = farmers.filter(
            Q(firstname__icontains=search_query) |
            Q(surname__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(NIN__icontains=search_query) |
            Q(farmer_id__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        farmers = farmers.filter(farmer_status=status_filter)
    
    # Filter by group type
    group_type_filter = request.GET.get('group_type', '')
    if group_type_filter:
        farmers = farmers.filter(group_type_id=group_type_filter)
    
    # Filter by group
    group_filter = request.GET.get('group', '')
    if group_filter:
        farmers = farmers.filter(group_name_id=group_filter)
    
    context = {
        'farmers': farmers,
        'search_query': search_query,
        'status_filter': status_filter,
        'group_type_filter': group_type_filter,
        'group_filter': group_filter,
        'group_types': GroupType.objects.all().order_by('name'),
        'groups': Group.objects.all().order_by('group_name'),
    }
    return render(request, 'vendors/farmers_list.html', context)


@login_required
def vendor_farmer_create(request):
    """Create a new farmer (vendor can only create farmers for themselves)"""
    # Ensure user is a vendor
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, 'Access denied. Vendor account required.')
        return redirect('vendor_login')
    
    vendor = request.user.vendor_profile
    
    # Check if vendor is active
    if vendor.vendor_status != 'active':
        logout(request)
        messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
        return redirect('vendor_login')
    
    if request.method == 'POST':
        form = FarmerForm(request.POST, request.FILES)
        if form.is_valid():
            farmer = form.save(commit=False)
            # Auto-assign vendor
            farmer.vendor = vendor
            farmer.save()
            messages.success(request, f'Farmer {farmer.get_full_name()} has been registered successfully!')
            return redirect('vendor_farmers_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = FarmerForm()
        # Pre-select the vendor (though it will be auto-assigned on save)
    
    context = {
        'form': form,
        'title': 'Register New Farmer',
        'vendor': vendor,
    }
    return render(request, 'vendors/farmer_create.html', context)


@login_required
def vendor_farmer_detail(request, pk):
    """View farmer details (vendor can only view their own farmers)"""
    # Ensure user is a vendor
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, 'Access denied. Vendor account required.')
        return redirect('vendor_login')
    
    vendor = request.user.vendor_profile
    
    # Check if vendor is active
    if vendor.vendor_status != 'active':
        logout(request)
        messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
        return redirect('vendor_login')
    farmer = get_object_or_404(Farmer, pk=pk, vendor=vendor)
    
    context = {
        'farmer': farmer,
        'vendor': vendor,
    }
    return render(request, 'vendors/farmer_detail.html', context)


@login_required
def vendor_profile(request):
    """View vendor profile information"""
    # Ensure user is a vendor
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, 'Access denied. Vendor account required.')
        return redirect('vendor_login')
    
    vendor = request.user.vendor_profile
    
    # Check if vendor is active
    if vendor.vendor_status != 'active':
        logout(request)
        messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
        return redirect('vendor_login')
    user = request.user
    
    # Get statistics
    total_farmers = Farmer.objects.filter(vendor=vendor).count()
    active_farmers = Farmer.objects.filter(vendor=vendor, farmer_status='active').count()
    
    context = {
        'vendor': vendor,
        'user': user,
        'total_farmers': total_farmers,
        'active_farmers': active_farmers,
    }
    return render(request, 'vendors/profile.html', context)
