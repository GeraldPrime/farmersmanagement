from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum, F
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Farmer, RedemptionCenter, Incentive, Disbursement
)


# ============================================================================
# REDEMPTION CENTER VIEWS - Redemption Center Interface
# ============================================================================
# All views in this file are for redemption center interface
# Redemption centers can view allocations, inventory, and disburse incentives to farmers


def redemption_center_login(request):
    """Redemption center login view"""
    if request.user.is_authenticated and hasattr(request.user, 'redemption_center_profile'):
        # Check if redemption center is active before allowing access
        redemption_center = request.user.redemption_center_profile
        if redemption_center.redemption_center_status == 'active':
            return redirect('redemption_center_dashboard')
        else:
            # Logout inactive redemption center
            logout(request)
            messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
            return redirect('redemption_center_login')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if user is linked to a redemption center
            if hasattr(user, 'redemption_center_profile'):
                redemption_center = user.redemption_center_profile
                
                # Check if redemption center is active
                if redemption_center.redemption_center_status != 'active':
                    messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
                    return render(request, 'redemption_centers/login.html')
                
                # All checks passed - login successful
                login(request, user)
                messages.success(request, f'Welcome back, {redemption_center.fullname}!')
                return redirect('redemption_center_dashboard')
            else:
                messages.error(request, 'No login credentials have been created for your account. Please contact the admin to set up your login credentials.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'redemption_centers/login.html')


@login_required
def redemption_center_logout(request):
    """Redemption center logout view"""
    if hasattr(request.user, 'redemption_center_profile'):
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('redemption_center_login')


@login_required
def redemption_center_dashboard(request):
    """Redemption center dashboard showing recent allocations and inventory"""
    # Ensure user is a redemption center
    if not hasattr(request.user, 'redemption_center_profile'):
        messages.error(request, 'Access denied. Redemption center account required.')
        return redirect('redemption_center_login')
    
    redemption_center = request.user.redemption_center_profile
    
    # Check if redemption center is active
    if redemption_center.redemption_center_status != 'active':
        logout(request)
        messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
        return redirect('redemption_center_login')
    
    # Get recent allocations (last 5)
    recent_allocations = Incentive.objects.filter(
        redemption_center=redemption_center
    ).order_by('-date_sent', '-created_at')[:5]
    
    # Get inventory (all incentives with remaining quantity > 0)
    inventory = []
    all_incentives = Incentive.objects.filter(redemption_center=redemption_center)
    
    for incentive in all_incentives:
        remaining = incentive.get_remaining_quantity()
        if remaining > 0:
            disbursed = incentive.get_disbursed_quantity()
            inventory.append({
                'incentive': incentive,
                'total_quantity': incentive.quantity,
                'disbursed_quantity': disbursed,
                'remaining_quantity': remaining,
                'percentage_remaining': (remaining / incentive.quantity * 100) if incentive.quantity > 0 else 0,
            })
    
    # Get statistics
    total_allocations = all_incentives.count()
    total_items_allocated = all_incentives.aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    total_items_disbursed = Disbursement.objects.filter(
        redemption_center=redemption_center
    ).aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    total_items_remaining = total_items_allocated - total_items_disbursed
    
    # Get recent disbursements (last 5)
    recent_disbursements = Disbursement.objects.filter(
        redemption_center=redemption_center
    ).select_related('farmer', 'incentive').order_by('-disbursement_date')[:5]
    
    # Get disbursements by incentive
    disbursements_by_incentive = Disbursement.objects.filter(
        redemption_center=redemption_center
    ).values('incentive__incentive_name').annotate(
        count=Count('disbursement_id'),
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]
    
    context = {
        'redemption_center': redemption_center,
        'recent_allocations': recent_allocations,
        'inventory': inventory,
        'total_allocations': total_allocations,
        'total_items_allocated': total_items_allocated,
        'total_items_disbursed': total_items_disbursed,
        'total_items_remaining': total_items_remaining,
        'recent_disbursements': recent_disbursements,
        'disbursements_by_incentive': disbursements_by_incentive,
    }
    return render(request, 'redemption_centers/dashboard.html', context)


@login_required
def redemption_center_allocations(request):
    """List all incentive allocations for the redemption center"""
    # Ensure user is a redemption center
    if not hasattr(request.user, 'redemption_center_profile'):
        messages.error(request, 'Access denied. Redemption center account required.')
        return redirect('redemption_center_login')
    
    redemption_center = request.user.redemption_center_profile
    
    # Check if redemption center is active
    if redemption_center.redemption_center_status != 'active':
        logout(request)
        messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
        return redirect('redemption_center_login')
    
    # Get all allocations
    allocations = Incentive.objects.filter(
        redemption_center=redemption_center
    ).order_by('-date_sent', '-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        allocations = allocations.filter(
            Q(incentive_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        allocations = allocations.filter(date_sent__gte=date_from)
    if date_to:
        allocations = allocations.filter(date_sent__lte=date_to)
    
    # Add remaining quantity to each allocation
    allocations_with_remaining = []
    for allocation in allocations:
        remaining = allocation.get_remaining_quantity()
        disbursed = allocation.get_disbursed_quantity()
        allocations_with_remaining.append({
            'allocation': allocation,
            'remaining_quantity': remaining,
            'disbursed_quantity': disbursed,
            'percentage_remaining': (remaining / allocation.quantity * 100) if allocation.quantity > 0 else 0,
        })
    
    context = {
        'redemption_center': redemption_center,
        'allocations': allocations_with_remaining,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'redemption_centers/allocations.html', context)


@login_required
def redemption_center_disburse(request):
    """Disburse incentives to farmers using NIN lookup"""
    # Ensure user is a redemption center
    if not hasattr(request.user, 'redemption_center_profile'):
        messages.error(request, 'Access denied. Redemption center account required.')
        return redirect('redemption_center_login')
    
    redemption_center = request.user.redemption_center_profile
    
    # Check if redemption center is active
    if redemption_center.redemption_center_status != 'active':
        logout(request)
        messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
        return redirect('redemption_center_login')
    
    # Get available incentives (with remaining quantity > 0)
    available_incentives = []
    all_incentives = Incentive.objects.filter(redemption_center=redemption_center)
    
    for incentive in all_incentives:
        remaining = incentive.get_remaining_quantity()
        if remaining > 0:
            available_incentives.append({
                'incentive': incentive,
                'remaining_quantity': remaining,
            })
    
    context = {
        'redemption_center': redemption_center,
        'available_incentives': available_incentives,
    }
    return render(request, 'redemption_centers/disburse.html', context)


@login_required
@require_http_methods(["POST"])
def lookup_farmer_by_nin(request):
    """AJAX endpoint to lookup farmer by NIN"""
    if not hasattr(request.user, 'redemption_center_profile'):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    nin = request.POST.get('nin', '').strip()
    
    if not nin:
        return JsonResponse({'error': 'NIN is required'}, status=400)
    
    try:
        farmer = Farmer.objects.get(NIN=nin)
        
        # Check if farmer is active
        if farmer.farmer_status != 'active':
            return JsonResponse({
                'error': 'Farmer account is inactive. Only active farmers can receive incentives.',
                'farmer': None
            }, status=400)
        
        # Get farmer picture URL (full URL)
        picture_url = None
        if farmer.picture:
            picture_url = request.build_absolute_uri(farmer.picture.url)
        
        # Return farmer information
        return JsonResponse({
            'success': True,
            'farmer': {
                'farmer_id': farmer.farmer_id,
                'full_name': farmer.get_full_name(),
                'firstname': farmer.firstname,
                'surname': farmer.surname,
                'middlename': farmer.middlename,
                'phone': farmer.phone,
                'state': farmer.state.name if farmer.state else '',
                'lga': farmer.LGA.name if farmer.LGA else '',
                'address': farmer.address,
                'status': farmer.farmer_status,
                'picture_url': picture_url,
            }
        })
    except Farmer.DoesNotExist:
        return JsonResponse({
            'error': f'No farmer found with NIN: {nin}. Please verify the NIN and try again.',
            'farmer': None
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'An error occurred: {str(e)}',
            'farmer': None
        }, status=500)


@login_required
@require_http_methods(["POST"])
def process_disbursement(request):
    """Process incentive disbursement to a farmer"""
    if not hasattr(request.user, 'redemption_center_profile'):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    redemption_center = request.user.redemption_center_profile
    
    try:
        incentive_id = request.POST.get('incentive_id')
        farmer_id = request.POST.get('farmer_id')
        quantity = int(request.POST.get('quantity', 1))
        notes = request.POST.get('notes', '').strip()
        
        if not incentive_id or not farmer_id:
            return JsonResponse({'error': 'Incentive and farmer are required'}, status=400)
        
        if quantity < 1:
            return JsonResponse({'error': 'Quantity must be at least 1'}, status=400)
        
        # Get incentive
        incentive = get_object_or_404(Incentive, pk=incentive_id, redemption_center=redemption_center)
        
        # Check remaining quantity
        remaining = incentive.get_remaining_quantity()
        if quantity > remaining:
            return JsonResponse({
                'error': f'Insufficient quantity. Only {remaining} units remaining for this incentive.'
            }, status=400)
        
        # Get farmer
        farmer = get_object_or_404(Farmer, pk=farmer_id)
        
        # Check if farmer is active
        if farmer.farmer_status != 'active':
            return JsonResponse({
                'error': 'Farmer account is inactive. Only active farmers can receive incentives.'
            }, status=400)
        
        # Check if farmer has already received this incentive (prevent duplicates)
        if Disbursement.objects.filter(incentive=incentive, farmer=farmer).exists():
            return JsonResponse({
                'error': f'This farmer has already received this incentive from this allocation. Each farmer can only receive each incentive once per allocation.'
            }, status=400)
        
        # Create disbursement
        disbursement = Disbursement.objects.create(
            incentive=incentive,
            farmer=farmer,
            quantity=quantity,
            redemption_center=redemption_center,
            disbursed_by=request.user,
            notes=notes
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


@login_required
def redemption_center_disbursements(request):
    """View all disbursements made by the redemption center"""
    # Ensure user is a redemption center
    if not hasattr(request.user, 'redemption_center_profile'):
        messages.error(request, 'Access denied. Redemption center account required.')
        return redirect('redemption_center_login')
    
    redemption_center = request.user.redemption_center_profile
    
    # Check if redemption center is active
    if redemption_center.redemption_center_status != 'active':
        logout(request)
        messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
        return redirect('redemption_center_login')
    
    # Get all disbursements
    disbursements = Disbursement.objects.filter(
        redemption_center=redemption_center
    ).select_related('farmer', 'incentive', 'disbursed_by').order_by('-disbursement_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        disbursements = disbursements.filter(
            Q(farmer__firstname__icontains=search_query) |
            Q(farmer__surname__icontains=search_query) |
            Q(farmer__NIN__icontains=search_query) |
            Q(incentive__incentive_name__icontains=search_query)
        )
    
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
    total_quantity_disbursed = disbursements.aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    # Get unique farmers count
    unique_farmers = disbursements.values('farmer').distinct().count()
    
    # Get available incentives for filter
    available_incentives = Incentive.objects.filter(
        redemption_center=redemption_center
    ).order_by('incentive_name')
    
    context = {
        'redemption_center': redemption_center,
        'disbursements': disbursements,
        'search_query': search_query,
        'incentive_filter': incentive_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_disbursements': total_disbursements,
        'total_quantity_disbursed': total_quantity_disbursed,
        'unique_farmers': unique_farmers,
        'available_incentives': available_incentives,
    }
    return render(request, 'redemption_centers/disbursements.html', context)


@login_required
def redemption_center_profile(request):
    """View redemption center profile information"""
    # Ensure user is a redemption center
    if not hasattr(request.user, 'redemption_center_profile'):
        messages.error(request, 'Access denied. Redemption center account required.')
        return redirect('redemption_center_login')
    
    redemption_center = request.user.redemption_center_profile
    
    # Check if redemption center is active
    if redemption_center.redemption_center_status != 'active':
        logout(request)
        messages.error(request, 'Your account is inactive. Please contact the admin to activate your account.')
        return redirect('redemption_center_login')
    
    # Get statistics
    total_allocations = Incentive.objects.filter(redemption_center=redemption_center).count()
    total_disbursements = Disbursement.objects.filter(redemption_center=redemption_center).count()
    total_farmers_served = Disbursement.objects.filter(
        redemption_center=redemption_center
    ).values('farmer').distinct().count()
    
    context = {
        'redemption_center': redemption_center,
        'total_allocations': total_allocations,
        'total_disbursements': total_disbursements,
        'total_farmers_served': total_farmers_served,
    }
    return render(request, 'redemption_centers/profile.html', context)

