from django.contrib import admin
from django.utils.html import format_html
from .models import GroupType, Group, Vendor, Farmer, State, LGA, Incentive, Disbursement


@admin.register(GroupType)
class GroupTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description_preview', 'groups_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {'fields': ('name', 'description')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def description_preview(self, obj):
        if obj.description:
            preview = obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
            return format_html('<span title="{}">{}</span>', obj.description, preview)
        return '-'
    description_preview.short_description = 'Description'

    def groups_count(self, obj):
        count = obj.groups.count()
        if count > 0:
            return format_html(
                '<a href="/admin/farmers/group/?group_type__id__exact={}">{}</a>', obj.id, count
            )
        return 0
    groups_count.short_description = 'Groups Count'


@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = [
        'farmer_id', 'picture_thumbnail', 'get_full_name',
        'phone', 'state', 'group_name', 'vendor', 'farmer_status_badge', 'date_registered'
    ]
    list_filter = ['farmer_status', 'gender', 'state', 'LGA', 'group_type', 'group_name', 'vendor', 'date_registered']
    search_fields = [
        'farmer_id', 'firstname', 'surname', 'middlename', 'phone', 'NIN', 'BVN',
        'ward', 'crop', 'group_leader_name', 'group_name__group_name',
        'vendor__vendor_firstname', 'vendor__vendor_surname'
    ]
    readonly_fields = ['farmer_id', 'date_registered', 'created_at', 'updated_at', 'picture_preview']
    autocomplete_fields = ['group_type', 'group_name', 'vendor']
    list_per_page = 25
    date_hierarchy = 'date_registered'

    fieldsets = (
        ('Farmer ID & Picture', {'fields': ('farmer_id', 'picture', 'picture_preview')}),
        ('Personal Information', {'fields': ('firstname', 'middlename', 'surname', 'date_of_birth', 'gender')}),
        ('Identification', {'fields': ('NIN', 'BVN')}),
        ('Contact Information', {'fields': ('phone', 'address')}),
        ('Location Information', {'fields': ('state', 'LGA', 'ward', 'farm_location')}),
        ('Group Information', {'fields': ('group_type', 'group_name', 'group_leader_name', 'group_leader_phone')}),
        ('Farming Information', {'fields': ('crop',)}),
        ('Registration Information', {'fields': ('vendor', 'date_registered', 'farmer_status')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'surname'

    def picture_thumbnail(self, obj):
        if obj.picture:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius:50%;object-fit:cover;" />', obj.picture.url
            )
        return format_html('<span style="color:#999;">No Image</span>')
    picture_thumbnail.short_description = 'Picture'

    def picture_preview(self, obj):
        if obj.picture:
            return format_html(
                '<img src="{}" width="200" height="200" style="border-radius:8px;object-fit:cover;border:2px solid #ddd;" />', obj.picture.url
            )
        return format_html('<span style="color:#999;">No picture uploaded</span>')
    picture_preview.short_description = 'Picture Preview'

    def farmer_status_badge(self, obj):
        color = 'success' if obj.farmer_status == 'active' else 'secondary'
        text = 'Active' if obj.farmer_status == 'active' else 'Inactive'
        return format_html('<span class="badge bg-{}">{}</span>', color, text)
    farmer_status_badge.short_description = 'Status'
    farmer_status_badge.admin_order_field = 'farmer_status'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('group_type', 'group_name', 'vendor')

    actions = ['make_active', 'make_inactive']

    def make_active(self, request, queryset):
        updated = queryset.update(farmer_status='active')
        self.message_user(request, f'{updated} farmer(s) marked as active.')
    make_active.short_description = 'Mark selected farmers as active'

    def make_inactive(self, request, queryset):
        updated = queryset.update(farmer_status='inactive')
        self.message_user(request, f'{updated} farmer(s) marked as inactive.')
    make_inactive.short_description = 'Mark selected farmers as inactive'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['group_name', 'group_type', 'group_leader', 'description_preview', 'is_active', 'created_at']
    list_filter = ['group_type', 'is_active', 'created_at']
    search_fields = ['group_name', 'description', 'group_type__name', 'group_leader__firstname', 'group_leader__surname']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['group_type', 'group_leader']

    fieldsets = (
        ('Group Information', {'fields': ('group_name', 'group_type', 'group_leader', 'description', 'is_active')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def description_preview(self, obj):
        if obj.description:
            preview = obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
            return format_html('<span title="{}">{}</span>', obj.description, preview)
        return '-'
    description_preview.short_description = 'Description'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('group_type')


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = [
        'vendor_registration_no', 'get_full_name', 'vendor_company_name',
        'vendor_email_address', 'vendor_phone', 'vendor_status_badge', 'date_registered'
    ]
    list_filter = ['vendor_status', 'date_registered']
    search_fields = [
        'vendor_firstname', 'vendor_surname', 'vendor_middlename',
        'vendor_company_name', 'vendor_email_address', 'vendor_phone', 'vendor_registration_no'
    ]
    readonly_fields = ['vendor_id', 'vendor_registration_no', 'date_registered']
    list_per_page = 25

    fieldsets = (
        ('Vendor Information', {'fields': (
            'vendor_id', 'vendor_registration_no', 'vendor_firstname', 'vendor_middlename',
            'vendor_surname', 'vendor_company_name', 'vendor_address',
            'vendor_email_address', 'vendor_phone', 'vendor_status'
        )}),
        ('Timestamps', {'fields': ('date_registered',), 'classes': ('collapse',)}),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'vendor_surname'

    def vendor_status_badge(self, obj):
        color = 'success' if obj.vendor_status == 'active' else 'secondary'
        text = 'Active' if obj.vendor_status == 'active' else 'Inactive'
        return format_html('<span class="badge bg-{}">{}</span>', color, text)
    vendor_status_badge.short_description = 'Status'
    vendor_status_badge.admin_order_field = 'vendor_status'


@admin.register(Incentive)
class IncentiveAdmin(admin.ModelAdmin):
    list_display = ['incentive_id', 'incentive_name', 'quantity', 'date_created', 'created_at']
    list_filter = ['date_created', 'created_at']
    search_fields = ['incentive_id', 'incentive_name', 'description']
    readonly_fields = ['incentive_id', 'created_at', 'updated_at']
    list_per_page = 25
    date_hierarchy = 'date_created'

    fieldsets = (
        ('Incentive Information', {'fields': ('incentive_id', 'incentive_name', 'quantity', 'description', 'date_created')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(Disbursement)
class DisbursementAdmin(admin.ModelAdmin):
    list_display = [
        'disbursement_id', 'farmer', 'incentive', 'quantity', 'disbursed_by', 'disbursement_date'
    ]
    list_filter = ['incentive', 'disbursement_date', 'created_at']
    search_fields = [
        'disbursement_id', 'farmer__firstname', 'farmer__surname',
        'farmer__NIN', 'incentive__incentive_name'
    ]
    readonly_fields = ['disbursement_id', 'disbursement_date', 'created_at', 'updated_at']
    autocomplete_fields = ['farmer', 'incentive']
    list_per_page = 25
    date_hierarchy = 'disbursement_date'

    fieldsets = (
        ('Disbursement Information', {'fields': (
            'disbursement_id', 'incentive', 'farmer', 'quantity', 'disbursed_by', 'disbursement_date', 'notes'
        )}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return list(self.readonly_fields) + ['incentive', 'farmer', 'quantity', 'disbursed_by', 'notes']
        return self.readonly_fields
