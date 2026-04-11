import base64
import secrets
import string
import requests as http_requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import (
    FarmerForm, GroupForm, GroupTypeForm, VendorForm,
    IncentiveForm, VendorFarmerForm,
)
from .models import Farmer, Group, GroupType, Vendor, State, LGA, Incentive, Disbursement


# ============================================================================
# HELPERS
# ============================================================================

def _vendor_required(request):
    """Return the vendor if request.user is a valid active vendor, else None."""
    if not request.user.is_authenticated:
        return None
    if not hasattr(request.user, 'vendor_profile'):
        return None
    return request.user.vendor_profile


def _check_vendor_active(request):
    """Return (vendor, None) if active, or (None, redirect_response) if not."""
    vendor = _vendor_required(request)
    if vendor is None:
        messages.error(request, 'Access denied. Vendor account required.')
        return None, redirect('vendor_login')
    if vendor.vendor_status != 'active':
        logout(request)
        messages.error(request, 'Your account is inactive. Please contact the admin.')
        return None, redirect('vendor_login')
    return vendor, None


def _map_gender(raw: str) -> str:
    """Map FICOVEN gender strings to model choices."""
    val = (raw or '').lower().strip()
    if val in ('m', 'male'):
        return 'male'
    if val in ('f', 'female'):
        return 'female'
    return ''


# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

def dashboard(request):
    context = {
        'total_farmers': Farmer.objects.count(),
        'active_farmers': Farmer.objects.filter(farmer_status='active').count(),
        'total_groups': Group.objects.count(),
        'active_groups': Group.objects.filter(is_active=True).count(),
        'total_vendors': Vendor.objects.count(),
        'active_vendors': Vendor.objects.filter(vendor_status='active').count(),
        'total_group_types': GroupType.objects.count(),
        'total_incentives': Incentive.objects.count(),
        'total_disbursements': Disbursement.objects.count(),
        'recent_farmers': Farmer.objects.all()[:5],
    }
    return render(request, 'admin/dashboard.html', context)


# ============================================================================
# FARMERS (ADMIN)
# ============================================================================

def farmers_list(request):
    farmers = Farmer.objects.select_related('group_type', 'group_name', 'vendor', 'state', 'LGA').all()

    search_query = request.GET.get('search', '')
    if search_query:
        farmers = farmers.filter(
            Q(firstname__icontains=search_query) |
            Q(surname__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(NIN__icontains=search_query) |
            Q(farmer_id__icontains=search_query)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        farmers = farmers.filter(farmer_status=status_filter)

    group_type_filter = request.GET.get('group_type', '')
    if group_type_filter:
        farmers = farmers.filter(group_type_id=group_type_filter)

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


def farmer_verify(request):
    """Step 1 for admin: verify farmer identity before registration."""
    if request.method == 'POST':
        # Confirmation that verification was done — proceed to create
        return redirect('farmer_create')
    # Clear any stale verification data when landing here fresh
    if request.GET.get('reset'):
        request.session.pop('verified_farmer', None)
    return render(request, 'admin/farmers/verify.html')


def farmer_create(request):
    """Create a new farmer (admin). Requires verified session data."""
    verified_data = request.session.get('verified_farmer')
    if not verified_data:
        messages.info(request, 'Please verify the farmer identity first.')
        return redirect('farmer_verify')

    if request.method == 'POST':
        form = FarmerForm(request.POST, request.FILES)
        if form.is_valid():
            farmer = form.save(commit=False)
            # If no photo uploaded but API returned one, save it
            if not request.FILES.get('picture') and verified_data.get('photo'):
                try:
                    img_bytes = base64.b64decode(verified_data['photo'])
                    farmer.picture.save(
                        f"farmer_{farmer.NIN}.jpg",
                        ContentFile(img_bytes),
                        save=False
                    )
                except Exception:
                    pass
            farmer.save()
            request.session.pop('verified_farmer', None)
            messages.success(request, f'Farmer {farmer.get_full_name()} has been created successfully!')
            return redirect('farmers_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        initial = {
            'firstname': verified_data.get('firstname', ''),
            'surname': verified_data.get('lastname', ''),
            'middlename': verified_data.get('middlename', ''),
            'gender': _map_gender(verified_data.get('gender', '')),
            'date_of_birth': verified_data.get('date_of_birth', ''),
            'phone': verified_data.get('phone', ''),
            'NIN': verified_data.get('nin', ''),
            'BVN': verified_data.get('bvn', ''),
            'address': verified_data.get('address', ''),
        }
        form = FarmerForm(initial=initial)

    context = {
        'form': form,
        'title': 'Add New Farmer',
        'verified_data': verified_data,
    }
    return render(request, 'admin/farmers/form.html', context)


def farmer_edit(request, pk):
    farmer = get_object_or_404(Farmer, pk=pk)
    if request.method == 'POST':
        form = FarmerForm(request.POST, request.FILES, instance=farmer)
        if form.is_valid():
            farmer = form.save()
            messages.success(request, f'Farmer {farmer.get_full_name()} has been updated successfully!')
            return redirect('farmers_list')
        else:
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
    farmer = get_object_or_404(
        Farmer.objects.select_related('group_type', 'group_name', 'vendor', 'state', 'LGA'),
        pk=pk
    )
    return render(request, 'admin/farmers/detail.html', {'farmer': farmer})


@require_http_methods(["POST"])
def farmer_toggle_status(request, pk):
    farmer = get_object_or_404(Farmer, pk=pk)
    if farmer.farmer_status == 'active':
        farmer.farmer_status = 'inactive'
        status_text = 'deactivated'
    else:
        farmer.farmer_status = 'active'
        status_text = 'activated'
    farmer.save()
    return JsonResponse({
        'success': True,
        'message': f'Farmer {farmer.get_full_name()} has been {status_text} successfully.',
        'new_status': farmer.farmer_status,
        'status_text': farmer.get_farmer_status_display()
    })


def farmer_delete(request, pk):
    farmer = get_object_or_404(Farmer, pk=pk)
    if request.method == 'POST':
        farmer_name = farmer.get_full_name()
        farmer.delete()
        messages.success(request, f'Farmer {farmer_name} has been deleted successfully!')
        return redirect('farmers_list')
    return render(request, 'admin/farmers/delete.html', {'farmer': farmer})


# ============================================================================
# GROUPS (ADMIN)
# ============================================================================

def groups_list(request):
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

    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        groups = groups.filter(is_active=True)
    elif status_filter == 'inactive':
        groups = groups.filter(is_active=False)

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
    return render(request, 'admin/groups/form.html', {'form': form, 'title': 'Add New Group'})


def group_edit(request, pk):
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
    return render(request, 'admin/groups/form.html', {'form': form, 'group': group, 'title': 'Edit Group'})


def group_detail(request, pk):
    group = get_object_or_404(
        Group.objects.select_related('group_type', 'group_leader').annotate(
            member_count=Count('members')
        ),
        pk=pk
    )
    members = Farmer.objects.filter(group_name=group).select_related('state', 'LGA', 'vendor')
    return render(request, 'admin/groups/detail.html', {'group': group, 'members': members})


def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group_name = group.group_name
        group.delete()
        messages.success(request, f'Group "{group_name}" has been deleted successfully!')
        return redirect('groups_list')
    return render(request, 'admin/groups/delete.html', {'group': group})


# ============================================================================
# GROUP TYPES (ADMIN)
# ============================================================================

def group_types_list(request):
    group_types = GroupType.objects.annotate(groups_count=Count('groups')).all()
    search_query = request.GET.get('search', '')
    if search_query:
        group_types = group_types.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    return render(request, 'admin/group_types/list.html', {
        'group_types': group_types, 'search_query': search_query
    })


def group_type_create(request):
    if request.method == 'POST':
        form = GroupTypeForm(request.POST)
        if form.is_valid():
            gt = form.save()
            messages.success(request, f'Group Type "{gt.name}" has been created successfully!')
            return redirect('group_types_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = GroupTypeForm()
    return render(request, 'admin/group_types/form.html', {'form': form, 'title': 'Add New Group Type'})


def group_type_edit(request, pk):
    group_type = get_object_or_404(GroupType, pk=pk)
    if request.method == 'POST':
        form = GroupTypeForm(request.POST, instance=group_type)
        if form.is_valid():
            gt = form.save()
            messages.success(request, f'Group Type "{gt.name}" has been updated successfully!')
            return redirect('group_types_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        form = GroupTypeForm(instance=group_type)
    return render(request, 'admin/group_types/form.html', {'form': form, 'group_type': group_type, 'title': 'Edit Group Type'})


def group_type_detail(request, pk):
    group_type = get_object_or_404(
        GroupType.objects.annotate(groups_count=Count('groups')), pk=pk
    )
    groups = Group.objects.filter(group_type=group_type).select_related('group_type').annotate(
        member_count=Count('members')
    )
    return render(request, 'admin/group_types/detail.html', {'group_type': group_type, 'groups': groups})


def group_type_delete(request, pk):
    from django.db.models import ProtectedError
    group_type = get_object_or_404(GroupType, pk=pk)
    groups_count = group_type.groups.count()
    if request.method == 'POST':
        try:
            name = group_type.name
            group_type.delete()
            messages.success(request, f'Group Type "{name}" has been deleted successfully!')
            return redirect('group_types_list')
        except ProtectedError:
            messages.error(request, f'Cannot delete "{group_type.name}" — it is used by {groups_count} group(s).')
            return redirect('group_types_list')
    return render(request, 'admin/group_types/delete.html', {'group_type': group_type, 'groups_count': groups_count})


# ============================================================================
# VENDORS (ADMIN)
# ============================================================================

def vendors_list(request):
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
    return render(request, 'admin/vendors/list.html', {
        'vendors': vendors, 'search_query': search_query, 'status_filter': status_filter
    })


def vendor_create(request):
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
    return render(request, 'admin/vendors/form.html', {'form': form, 'title': 'Add New Vendor'})


def vendor_edit(request, pk):
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
    return render(request, 'admin/vendors/form.html', {'form': form, 'vendor': vendor, 'title': 'Edit Vendor'})


def vendor_detail(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    registered_farmers = Farmer.objects.filter(vendor=vendor).select_related('state', 'LGA', 'group_name')
    return render(request, 'admin/vendors/detail.html', {
        'vendor': vendor,
        'registered_farmers': registered_farmers,
        'farmers_count': registered_farmers.count(),
    })


def vendor_delete(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    farmers_count = vendor.registered_farmers.count()
    if request.method == 'POST':
        vendor_name = vendor.get_full_name()
        vendor.delete()
        messages.success(request, f'Vendor "{vendor_name}" has been deleted successfully!')
        return redirect('vendors_list')
    return render(request, 'admin/vendors/delete.html', {'vendor': vendor, 'farmers_count': farmers_count})


@require_http_methods(["POST"])
def vendor_toggle_status(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    vendor.vendor_status = 'inactive' if vendor.vendor_status == 'active' else 'active'
    vendor.save()
    return JsonResponse({
        'success': True,
        'status': vendor.vendor_status,
        'message': f'Vendor status updated to {vendor.vendor_status.title()}'
    })


@require_http_methods(["GET", "POST"])
def vendor_credentials(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'has_credentials': vendor.user is not None,
            'username': vendor.user.username if vendor.user else None,
            'suggested_username': f"{vendor.vendor_firstname.lower()}{vendor.vendor_surname.lower()}",
        })

    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()

    if not username:
        return JsonResponse({'success': False, 'error': 'Username is required'}, status=400)
    if not password:
        return JsonResponse({'success': False, 'error': 'Password is required'}, status=400)

    existing = User.objects.filter(username=username).exclude(
        id=vendor.user.id if vendor.user else None
    ).first()
    if existing:
        return JsonResponse({'success': False, 'error': 'Username already exists.'}, status=400)

    if vendor.user:
        vendor.user.username = username
        vendor.user.set_password(password)
        vendor.user.save()
        action = 'updated'
    else:
        user = User.objects.create_user(
            username=username, password=password,
            email=vendor.vendor_email_address,
            first_name=vendor.vendor_firstname,
            last_name=vendor.vendor_surname,
            is_staff=False, is_superuser=False
        )
        vendor.user = user
        vendor.save()
        action = 'created'

    return JsonResponse({'success': True, 'message': f'Credentials {action} successfully', 'username': username})


# ============================================================================
# INCENTIVES (ADMIN)
# ============================================================================

def incentives_list(request):
    incentives = Incentive.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        incentives = incentives.filter(
            Q(incentive_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        incentives = incentives.filter(date_created__gte=date_from)
    if date_to:
        incentives = incentives.filter(date_created__lte=date_to)

    incentives_with_stats = []
    for incentive in incentives:
        remaining = incentive.get_remaining_quantity()
        disbursed = incentive.get_disbursed_quantity()
        incentives_with_stats.append({
            'incentive': incentive,
            'disbursed_quantity': disbursed,
            'remaining_quantity': remaining,
        })

    return render(request, 'admin/incentives/list.html', {
        'incentives': incentives_with_stats,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
    })


def incentive_create(request):
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
    return render(request, 'admin/incentives/form.html', {'form': form, 'title': 'Add New Incentive'})


def incentive_edit(request, pk):
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
    return render(request, 'admin/incentives/form.html', {'form': form, 'incentive': incentive, 'title': 'Edit Incentive'})


def incentive_detail(request, pk):
    incentive = get_object_or_404(Incentive, pk=pk)
    disbursements = Disbursement.objects.filter(incentive=incentive).select_related('farmer', 'disbursed_by')
    context = {
        'incentive': incentive,
        'disbursements': disbursements,
        'remaining_quantity': incentive.get_remaining_quantity(),
        'disbursed_quantity': incentive.get_disbursed_quantity(),
    }
    return render(request, 'admin/incentives/detail.html', context)


def incentive_delete(request, pk):
    incentive = get_object_or_404(Incentive, pk=pk)
    if request.method == 'POST':
        name = incentive.incentive_name
        incentive.delete()
        messages.success(request, f'Incentive "{name}" has been deleted successfully!')
        return redirect('incentives_list')
    return render(request, 'admin/incentives/delete.html', {'incentive': incentive})


# ============================================================================
# DISBURSEMENTS (ADMIN)
# ============================================================================

def disbursements_list(request):
    disbursements = Disbursement.objects.select_related(
        'farmer', 'incentive', 'disbursed_by'
    ).order_by('-disbursement_date')

    search_query = request.GET.get('search', '')
    if search_query:
        disbursements = disbursements.filter(
            Q(farmer__firstname__icontains=search_query) |
            Q(farmer__surname__icontains=search_query) |
            Q(farmer__NIN__icontains=search_query) |
            Q(incentive__incentive_name__icontains=search_query)
        )

    incentive_filter = request.GET.get('incentive', '')
    if incentive_filter:
        disbursements = disbursements.filter(incentive_id=incentive_filter)

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        disbursements = disbursements.filter(disbursement_date__date__gte=date_from)
    if date_to:
        disbursements = disbursements.filter(disbursement_date__date__lte=date_to)

    total_disbursements = disbursements.count()
    total_quantity = disbursements.aggregate(total=Sum('quantity'))['total'] or 0
    unique_farmers = disbursements.values('farmer').distinct().count()

    return render(request, 'admin/disbursements/list.html', {
        'disbursements': disbursements,
        'search_query': search_query,
        'incentive_filter': incentive_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_disbursements': total_disbursements,
        'total_quantity': total_quantity,
        'unique_farmers': unique_farmers,
        'incentives': Incentive.objects.all().order_by('incentive_name'),
    })


def admin_disburse(request):
    """Admin page to disburse an incentive to a farmer."""
    available_incentives = []
    for incentive in Incentive.objects.all():
        remaining = incentive.get_remaining_quantity()
        if remaining > 0:
            available_incentives.append({
                'incentive': incentive,
                'remaining_quantity': remaining,
            })

    return render(request, 'admin/disbursements/disburse.html', {
        'available_incentives': available_incentives,
    })


@require_http_methods(["POST"])
def admin_lookup_farmer(request):
    """AJAX: look up a farmer by NIN for the disburse page."""
    nin = request.POST.get('nin', '').strip()
    if not nin:
        return JsonResponse({'error': 'NIN is required'}, status=400)
    try:
        farmer = Farmer.objects.get(NIN=nin)
        if farmer.farmer_status != 'active':
            return JsonResponse({'error': 'Farmer account is inactive.'}, status=400)
        picture_url = request.build_absolute_uri(farmer.picture.url) if farmer.picture else None
        return JsonResponse({
            'success': True,
            'farmer': {
                'farmer_id': farmer.farmer_id,
                'full_name': farmer.get_full_name(),
                'phone': farmer.phone,
                'state': farmer.state.name if farmer.state else '',
                'lga': farmer.LGA.name if farmer.LGA else '',
                'picture_url': picture_url,
            }
        })
    except Farmer.DoesNotExist:
        return JsonResponse({'error': f'No farmer found with NIN: {nin}'}, status=404)


@require_http_methods(["POST"])
def admin_process_disbursement(request):
    """AJAX: process a disbursement from admin."""
    try:
        incentive_id = request.POST.get('incentive_id')
        farmer_id = request.POST.get('farmer_id')
        quantity = int(request.POST.get('quantity', 1))
        notes = request.POST.get('notes', '').strip()

        if not incentive_id or not farmer_id:
            return JsonResponse({'error': 'Incentive and farmer are required'}, status=400)
        if quantity < 1:
            return JsonResponse({'error': 'Quantity must be at least 1'}, status=400)

        incentive = get_object_or_404(Incentive, pk=incentive_id)
        remaining = incentive.get_remaining_quantity()
        if quantity > remaining:
            return JsonResponse({
                'error': f'Insufficient quantity. Only {remaining} units remaining.'
            }, status=400)

        farmer = get_object_or_404(Farmer, pk=farmer_id)
        if farmer.farmer_status != 'active':
            return JsonResponse({'error': 'Farmer account is inactive.'}, status=400)

        if Disbursement.objects.filter(incentive=incentive, farmer=farmer).exists():
            return JsonResponse({
                'error': 'This farmer has already received this incentive.'
            }, status=400)

        disbursement = Disbursement.objects.create(
            incentive=incentive,
            farmer=farmer,
            quantity=quantity,
            disbursed_by=request.user,
            notes=notes,
        )
        return JsonResponse({
            'success': True,
            'message': f'Successfully disbursed {quantity} unit(s) of {incentive.incentive_name} to {farmer.get_full_name()}.',
            'disbursement_id': disbursement.disbursement_id,
            'remaining_quantity': incentive.get_remaining_quantity(),
        })
    except ValueError:
        return JsonResponse({'error': 'Invalid quantity value'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


# ============================================================================
# IDENTITY VERIFICATION API (shared by admin + vendor)
# ============================================================================

@require_http_methods(["POST"])
def verify_farmer_identity(request):
    """
    AJAX endpoint: calls FICOVEN identity API (NIN / BVN / Phone),
    stores result in session, returns sanitised data to the frontend.
    """
    id_type = request.POST.get('id_type', '').strip()
    id_value = request.POST.get('id_value', '').strip()

    if not id_type or not id_value:
        return JsonResponse({'error': 'ID type and value are required'}, status=400)

    api_key = getattr(settings, 'FICOVEN_API_KEY', '')
    base_url = getattr(settings, 'FICOVEN_BASE_URL', 'https://identity.ficoven.com')

    if id_type == 'nin':
        url = f"{base_url}/api/verify-nin"
        headers = {
            'Content-Type': 'application/json',
            'x-api-token': api_key,
            'Origin': base_url,
            'Referer': f"{base_url}/",
        }
        payload = {'nin': id_value}

    elif id_type == 'bvn':
        supabase_url = getattr(settings, 'FICOVEN_SUPABASE_URL', '')
        supabase_anon = getattr(settings, 'FICOVEN_SUPABASE_ANON', '')
        ficoven_email = getattr(settings, 'FICOVEN_EMAIL', '')
        ficoven_password = getattr(settings, 'FICOVEN_PASSWORD', '')

        if not all([supabase_url, supabase_anon, ficoven_email, ficoven_password]):
            return JsonResponse({'error': 'BVN verification is not configured on this server.'}, status=500)

        try:
            auth_resp = http_requests.post(
                f"{supabase_url}/auth/v1/token?grant_type=password",
                headers={'apikey': supabase_anon, 'Content-Type': 'application/json'},
                json={'email': ficoven_email, 'password': ficoven_password},
                timeout=15,
            )
            jwt_data = auth_resp.json()
            if auth_resp.status_code != 200 or 'access_token' not in jwt_data:
                return JsonResponse({'error': 'BVN verification service unavailable. Please try NIN or Phone.'}, status=500)
            jwt_token = jwt_data['access_token']
        except Exception:
            return JsonResponse({'error': 'BVN verification service unreachable. Please try NIN or Phone.'}, status=500)

        url = f"{supabase_url}/functions/v1/verify-bvn"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {jwt_token}",
            'x-api-token': api_key,
            'apikey': supabase_anon,
        }
        payload = {'bvn': id_value}

    elif id_type == 'phone':
        url = f"{base_url}/api/verify-phone"
        headers = {
            'Content-Type': 'application/json',
            'x-api-token': api_key,
            'Origin': base_url,
            'Referer': f"{base_url}/",
        }
        payload = {'phone': id_value}

    else:
        return JsonResponse({'error': 'Invalid ID type. Use nin, bvn, or phone.'}, status=400)

    try:
        resp = http_requests.post(url, headers=headers, json=payload, timeout=15)
        data = resp.json()
    except http_requests.exceptions.Timeout:
        return JsonResponse({'error': 'Verification service timed out. Please try again.'}, status=504)
    except Exception:
        return JsonResponse({'error': 'Could not reach verification service. Please try again.'}, status=500)

    if resp.status_code == 200 and data.get('success'):
        person = data.get('data', {})

        # Store in session (photo kept for auto-save on form submit)
        request.session['verified_farmer'] = {
            'firstname': person.get('firstname', ''),
            'lastname': person.get('lastname', ''),
            'middlename': person.get('middlename', ''),
            'gender': person.get('gender', ''),
            'date_of_birth': person.get('birthdate', ''),
            'phone': person.get('phone', ''),
            'nin': person.get('nin', '') or (id_value if id_type == 'nin' else ''),
            'bvn': person.get('bvn', '') or (id_value if id_type == 'bvn' else ''),
            'address': person.get('address') or person.get('residential_address', ''),
            'photo': person.get('photo', ''),
            'id_type': id_type,
            'id_value': id_value,
        }

        photo_url = ''
        if person.get('photo'):
            photo_url = f"data:image/jpeg;base64,{person['photo']}"

        return JsonResponse({
            'success': True,
            'person': {
                'firstname': person.get('firstname', ''),
                'lastname': person.get('lastname', ''),
                'middlename': person.get('middlename', ''),
                'gender': person.get('gender', ''),
                'date_of_birth': person.get('birthdate', ''),
                'phone': person.get('phone', ''),
                'nin': person.get('nin', '') or (id_value if id_type == 'nin' else ''),
                'bvn': person.get('bvn', '') or (id_value if id_type == 'bvn' else ''),
                'address': person.get('address') or person.get('residential_address', ''),
            },
            'photo_url': photo_url,
            'units_remaining': data.get('units_remaining', 'N/A'),
        })

    # Error responses
    error_map = {
        401: 'Invalid or expired API token. Please contact admin.',
        402: 'Verification unit balance is exhausted. Please contact admin.',
        403: 'Verification account suspended. Please contact admin.',
        400: f"Verification failed: {data.get('message') or data}",
    }
    error_msg = error_map.get(resp.status_code, f'Verification failed. Please check the {id_type.upper()} and try again.')
    return JsonResponse({'error': error_msg}, status=400)


# ============================================================================
# UTILITY ENDPOINTS (ADMIN)
# ============================================================================

def generate_random_password():
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(12))


@require_http_methods(["GET"])
def generate_password(request):
    return JsonResponse({'success': True, 'password': generate_random_password()})


def get_lgas_by_state(request):
    state_id = request.GET.get('state_id')
    if state_id:
        lgas = LGA.objects.filter(state_id=state_id).order_by('name')
        return JsonResponse({'lgas': [{'id': lga.id, 'name': lga.name} for lga in lgas]})
    return JsonResponse({'lgas': []})


# ============================================================================
# ADMIN AUTHENTICATION
# ============================================================================

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect(request.GET.get('next', 'dashboard'))

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        messages.error(request, 'Invalid credentials or insufficient permissions.')

    return render(request, 'admin/portal_login.html', {'next': request.GET.get('next', '')})


def admin_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('admin_login')


# ============================================================================
# VENDOR AUTHENTICATION
# ============================================================================

def vendor_login(request):
    if request.user.is_authenticated and hasattr(request.user, 'vendor_profile'):
        vendor = request.user.vendor_profile
        if vendor.vendor_status == 'active':
            return redirect('vendor_dashboard')
        logout(request)
        messages.error(request, 'Your account is inactive. Please contact admin.')
        return redirect('vendor_login')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if hasattr(user, 'vendor_profile'):
                vendor = user.vendor_profile
                if vendor.vendor_status != 'active':
                    messages.error(request, 'Your account is inactive. Please contact admin.')
                    return render(request, 'vendors/login.html')
                login(request, user)
                messages.success(request, f'Welcome back, {vendor.get_full_name()}!')
                return redirect('vendor_dashboard')
            else:
                messages.error(request, 'No vendor account found. Please contact admin.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'vendors/login.html')


@login_required
def vendor_logout(request):
    if hasattr(request.user, 'vendor_profile'):
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('vendor_login')


# ============================================================================
# VENDOR DASHBOARD & FARMERS
# ============================================================================

@login_required
def vendor_dashboard(request):
    vendor, err = _check_vendor_active(request)
    if err:
        return err

    farmers = Farmer.objects.filter(vendor=vendor)
    farmers_by_state = farmers.values('state__name').annotate(count=Count('farmer_id')).order_by('-count')[:5]

    return render(request, 'vendors/dashboard.html', {
        'vendor': vendor,
        'total_farmers': farmers.count(),
        'active_farmers': farmers.filter(farmer_status='active').count(),
        'inactive_farmers': farmers.filter(farmer_status='inactive').count(),
        'farmers_by_state': farmers_by_state,
        'recent_farmers': farmers.order_by('-date_registered')[:5],
    })


@login_required
def vendor_farmers_list(request):
    vendor, err = _check_vendor_active(request)
    if err:
        return err

    farmers = Farmer.objects.filter(vendor=vendor).select_related('group_type', 'group_name', 'state', 'LGA')

    search_query = request.GET.get('search', '')
    if search_query:
        farmers = farmers.filter(
            Q(firstname__icontains=search_query) |
            Q(surname__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(NIN__icontains=search_query) |
            Q(farmer_id__icontains=search_query)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        farmers = farmers.filter(farmer_status=status_filter)

    group_type_filter = request.GET.get('group_type', '')
    if group_type_filter:
        farmers = farmers.filter(group_type_id=group_type_filter)

    return render(request, 'vendors/farmers_list.html', {
        'farmers': farmers,
        'search_query': search_query,
        'status_filter': status_filter,
        'group_type_filter': group_type_filter,
        'group_types': GroupType.objects.all().order_by('name'),
        'groups': Group.objects.all().order_by('group_name'),
    })


@login_required
def vendor_farmer_verify(request):
    """Step 1 for vendor: verify farmer identity before registration."""
    if request.method == 'POST':
        return redirect('vendor_farmer_create')
    if request.GET.get('reset'):
        request.session.pop('verified_farmer', None)
    vendor, err = _check_vendor_active(request)
    if err:
        return err
    return render(request, 'vendors/farmer_verify.html', {'vendor': vendor})


@login_required
def vendor_farmer_create(request):
    """Create a new farmer (vendor). Requires verified session data."""
    vendor, err = _check_vendor_active(request)
    if err:
        return err

    verified_data = request.session.get('verified_farmer')
    if not verified_data:
        messages.info(request, 'Please verify the farmer identity first.')
        return redirect('vendor_farmer_verify')

    if request.method == 'POST':
        form = VendorFarmerForm(request.POST, request.FILES)
        if form.is_valid():
            farmer = form.save(commit=False)
            farmer.vendor = vendor
            if not request.FILES.get('picture') and verified_data.get('photo'):
                try:
                    img_bytes = base64.b64decode(verified_data['photo'])
                    farmer.picture.save(
                        f"farmer_{farmer.NIN}.jpg",
                        ContentFile(img_bytes),
                        save=False
                    )
                except Exception:
                    pass
            farmer.save()
            request.session.pop('verified_farmer', None)
            messages.success(request, f'Farmer {farmer.get_full_name()} has been registered successfully!')
            return redirect('vendor_farmers_list')
        else:
            messages.error(request, 'Please correct the errors below and try again.')
    else:
        initial = {
            'firstname': verified_data.get('firstname', ''),
            'surname': verified_data.get('lastname', ''),
            'middlename': verified_data.get('middlename', ''),
            'gender': _map_gender(verified_data.get('gender', '')),
            'date_of_birth': verified_data.get('date_of_birth', ''),
            'phone': verified_data.get('phone', ''),
            'NIN': verified_data.get('nin', ''),
            'BVN': verified_data.get('bvn', ''),
            'address': verified_data.get('address', ''),
        }
        form = VendorFarmerForm(initial=initial)

    return render(request, 'vendors/farmer_create.html', {
        'form': form,
        'title': 'Register New Farmer',
        'vendor': vendor,
        'verified_data': verified_data,
    })


@login_required
def vendor_farmer_detail(request, pk):
    vendor, err = _check_vendor_active(request)
    if err:
        return err
    farmer = get_object_or_404(Farmer, pk=pk, vendor=vendor)
    return render(request, 'vendors/farmer_detail.html', {'farmer': farmer, 'vendor': vendor})


@login_required
def vendor_profile(request):
    vendor, err = _check_vendor_active(request)
    if err:
        return err
    total_farmers = Farmer.objects.filter(vendor=vendor).count()
    active_farmers = Farmer.objects.filter(vendor=vendor, farmer_status='active').count()
    return render(request, 'vendors/profile.html', {
        'vendor': vendor,
        'user': request.user,
        'total_farmers': total_farmers,
        'active_farmers': active_farmers,
    })
