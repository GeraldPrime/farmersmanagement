from django import forms
from django.db.models import Q
from .models import Farmer, Group, GroupType, Vendor, RedemptionCenter, State, LGA, Incentive


class FarmerForm(forms.ModelForm):
    """Form for creating and editing farmers"""
    
    class Meta:
        model = Farmer
        fields = [
            'firstname', 'middlename', 'surname', 'date_of_birth', 'gender',
            'NIN', 'BVN', 'phone', 'address', 'state', 'LGA', 'ward',
            'farm_location', 'group_type', 'group_name', 'group_leader_name',
            'group_leader_phone', 'crop', 'picture', 'vendor', 'farmer_status'
        ]
        widgets = {
            'firstname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'middlename': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter middle name (optional)'
            }),
            'surname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter surname'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'NIN': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '11-digit NIN',
                'maxlength': '11'
            }),
            'BVN': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '11-digit BVN (optional)',
                'maxlength': '11'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+234XXXXXXXXXX'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter residential address'
            }),
            'state': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_state'
            }),
            'LGA': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_LGA'
            }),
            'ward': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ward'
            }),
            'farm_location': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter farm location'
            }),
            'group_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'group_name': forms.Select(attrs={
                'class': 'form-select'
            }),
            'group_leader_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter group leader name (optional)'
            }),
            'group_leader_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter group leader phone (optional)'
            }),
            'crop': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter crop type(s)'
            }),
            'picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'vendor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'farmer_status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields optional where needed
        self.fields['group_type'].required = False
        self.fields['group_name'].required = False
        self.fields['vendor'].required = False
        # Picture is required for new farmers, optional when editing (if already has picture)
        if not self.instance or not self.instance.pk:
            self.fields['picture'].required = True
        elif self.instance and self.instance.pk and self.instance.picture:
            # If editing and already has a picture, it's optional
            self.fields['picture'].required = False
        else:
            # If editing but no picture, require it
            self.fields['picture'].required = True
        self.fields['state'].required = False
        self.fields['LGA'].required = False
        
        # Set querysets for State and LGA
        self.fields['state'].queryset = State.objects.all().order_by('name')
        self.fields['LGA'].queryset = LGA.objects.none()  # Start with empty queryset
        
        # If editing an existing farmer, set the LGA queryset based on the selected state
        if self.instance and self.instance.pk and self.instance.state:
            self.fields['LGA'].queryset = LGA.objects.filter(state=self.instance.state).order_by('name')
        # If form was submitted with errors, check POST data for state and populate LGA
        elif self.data and 'state' in self.data and self.data['state']:
            try:
                state_id = int(self.data['state'])
                self.fields['LGA'].queryset = LGA.objects.filter(state_id=state_id).order_by('name')
            except (ValueError, TypeError):
                pass


class GroupForm(forms.ModelForm):
    """Form for creating and editing groups"""
    
    class Meta:
        model = Group
        fields = ['group_name', 'group_type', 'group_leader', 'description', 'is_active']
        widgets = {
            'group_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter group name'
            }),
            'group_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'group_leader': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_group_leader'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter group description (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for group_type
        self.fields['group_type'].queryset = GroupType.objects.all().order_by('name')
        # Set queryset for group_leader - all farmers ordered by name
        self.fields['group_leader'].queryset = Farmer.objects.all().order_by('firstname', 'surname')
        # Make group_leader optional
        self.fields['group_leader'].required = False


class GroupTypeForm(forms.ModelForm):
    """Form for creating and editing group types"""
    
    class Meta:
        model = GroupType
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter group type name (e.g., Cooperative, Association)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter description of this group type (optional)'
            }),
        }


class VendorForm(forms.ModelForm):
    """Form for creating and editing vendors"""
    
    class Meta:
        model = Vendor
        fields = [
            'vendor_firstname', 'vendor_middlename', 'vendor_surname',
            'vendor_company_name', 'vendor_address', 'vendor_email_address',
            'vendor_phone', 'vendor_status'
        ]
        widgets = {
            'vendor_firstname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'vendor_middlename': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter middle name (optional)'
            }),
            'vendor_surname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter surname'
            }),
            'vendor_company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company or organization name'
            }),
            'vendor_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter complete address'
            }),
            'vendor_email_address': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'vendor_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+234XXXXXXXXXX'
            }),
            'vendor_status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


class RedemptionCenterForm(forms.ModelForm):
    """Form for creating and editing redemption centers"""
    
    class Meta:
        model = RedemptionCenter
        fields = ['fullname', 'redemption_center_address', 'phone_no', 'email', 'description', 'redemption_center_status']
        widgets = {
            'fullname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name of the redemption center'
            }),
            'redemption_center_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter complete address'
            }),
            'phone_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+234XXXXXXXXXX'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter description of the redemption center (optional)'
            }),
            'redemption_center_status': forms.Select(attrs={
                'class': 'form-select',
            }),
        }


class IncentiveForm(forms.ModelForm):
    """Form for creating and editing incentives"""
    
    class Meta:
        model = Incentive
        fields = ['incentive_name', 'quantity', 'redemption_center', 'date_sent', 'description']
        widgets = {
            'incentive_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter incentive name (e.g., Fertilizer, Seeds, Tools)'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter quantity',
                'min': '1'
            }),
            'redemption_center': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date_sent': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter description of the incentive (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset for redemption_center - only show active centers
        self.fields['redemption_center'].queryset = RedemptionCenter.objects.filter(
            redemption_center_status='active'
        ).order_by('fullname')
        
        # If editing an existing incentive with an inactive center, include it in queryset
        if self.instance and self.instance.pk and self.instance.redemption_center:
            if self.instance.redemption_center.redemption_center_status != 'active':
                self.fields['redemption_center'].queryset = RedemptionCenter.objects.filter(
                    Q(redemption_center_status='active') | Q(pk=self.instance.redemption_center.pk)
                ).order_by('fullname')
    
    def clean_redemption_center(self):
        """Validate that the redemption center is active"""
        redemption_center = self.cleaned_data.get('redemption_center')
        if redemption_center and redemption_center.redemption_center_status != 'active':
            raise forms.ValidationError(
                f'Cannot assign incentive to inactive redemption center "{redemption_center.fullname}". '
                'Please select an active redemption center.'
            )
        return redemption_center

