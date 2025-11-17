from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from .models import Farmer, Group, GroupType, Vendor, RedemptionCenter, State, LGA, Incentive
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
    
    context = {
        'centers': centers,
        'search_query': search_query,
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
    
    context = {
        'center': center,
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
