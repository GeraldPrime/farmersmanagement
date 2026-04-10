from django import forms
from .models import Farmer, Group, GroupType, Vendor, State, LGA, Incentive


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
        self.fields['group_type'].required = False
        self.fields['group_name'].required = False
        self.fields['vendor'].required = False
        if not self.instance or not self.instance.pk:
            self.fields['picture'].required = True
        elif self.instance and self.instance.pk and self.instance.picture:
            self.fields['picture'].required = False
        else:
            self.fields['picture'].required = True
        self.fields['state'].required = False
        self.fields['LGA'].required = False

        self.fields['state'].queryset = State.objects.all().order_by('name')
        self.fields['LGA'].queryset = LGA.objects.none()

        if self.instance and self.instance.pk and self.instance.state:
            self.fields['LGA'].queryset = LGA.objects.filter(state=self.instance.state).order_by('name')
        elif self.data and 'state' in self.data and self.data['state']:
            try:
                state_id = int(self.data['state'])
                self.fields['LGA'].queryset = LGA.objects.filter(state_id=state_id).order_by('name')
            except (ValueError, TypeError):
                pass


class VendorFarmerForm(forms.ModelForm):
    """Form for vendors creating farmers — excludes vendor and farmer_status fields"""

    class Meta:
        model = Farmer
        fields = [
            'firstname', 'middlename', 'surname', 'date_of_birth', 'gender',
            'NIN', 'BVN', 'phone', 'address', 'state', 'LGA', 'ward',
            'farm_location', 'group_type', 'group_name', 'group_leader_name',
            'group_leader_phone', 'crop', 'picture',
        ]
        widgets = {
            'firstname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'middlename': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter middle name (optional)'}),
            'surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter surname'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'NIN': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '11-digit NIN', 'maxlength': '11'}),
            'BVN': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '11-digit BVN (optional)', 'maxlength': '11'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+234XXXXXXXXXX'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter residential address'}),
            'state': forms.Select(attrs={'class': 'form-select', 'id': 'id_state'}),
            'LGA': forms.Select(attrs={'class': 'form-select', 'id': 'id_LGA'}),
            'ward': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ward'}),
            'farm_location': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter farm location'}),
            'group_type': forms.Select(attrs={'class': 'form-select'}),
            'group_name': forms.Select(attrs={'class': 'form-select'}),
            'group_leader_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter group leader name (optional)'}),
            'group_leader_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter group leader phone (optional)'}),
            'crop': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter crop type(s)'}),
            'picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group_type'].required = False
        self.fields['group_name'].required = False
        self.fields['state'].required = False
        self.fields['LGA'].required = False
        self.fields['picture'].required = False  # May be pre-filled from verification photo

        self.fields['state'].queryset = State.objects.all().order_by('name')
        self.fields['LGA'].queryset = LGA.objects.none()

        if self.instance and self.instance.pk and self.instance.state:
            self.fields['LGA'].queryset = LGA.objects.filter(state=self.instance.state).order_by('name')
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
        self.fields['group_type'].queryset = GroupType.objects.all().order_by('name')
        self.fields['group_leader'].queryset = Farmer.objects.all().order_by('firstname', 'surname')
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


class IncentiveForm(forms.ModelForm):
    """Form for creating and editing incentive batches"""

    class Meta:
        model = Incentive
        fields = ['incentive_name', 'quantity', 'date_created', 'description']
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
            'date_created': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter description of the incentive (optional)'
            }),
        }
