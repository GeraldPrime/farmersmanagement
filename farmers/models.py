from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import date
import random

# Create your models here.

class State(models.Model):
    """
    Model to store Nigerian states.
    """
    name = models.CharField(max_length=100, unique=True, help_text="Name of the state")
    code = models.CharField(max_length=3, unique=True, blank=True, null=True, help_text="State code (e.g., LAG, ABJ)")
    
    class Meta:
        verbose_name = "State"
        verbose_name_plural = "States"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class LGA(models.Model):
    """
    Model to store Local Government Areas (LGAs) for each state.
    """
    name = models.CharField(max_length=100, help_text="Name of the Local Government Area")
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='lgas', help_text="State this LGA belongs to")
    
    class Meta:
        verbose_name = "Local Government Area"
        verbose_name_plural = "Local Government Areas"
        ordering = ['state', 'name']
        unique_together = ['name', 'state']
    
    def __str__(self):
        return f"{self.name}, {self.state.name}"

class GroupType(models.Model):
    """
    Model to store different types of groups that can be created.
    Admin can create and manage group types.
    """
    name = models.CharField(max_length=100, unique=True, help_text="Name of the group type (e.g., 'Cooperative', 'Association', 'Union')")
    description = models.TextField(blank=True, help_text="Detailed description of what this group type represents")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Group Type"
        verbose_name_plural = "Group Types"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('admin:farmers_grouptype_change', args=[self.pk])


class Farmer(models.Model):
    """
    Model to store comprehensive farmer information.
    """
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    farmer_id = models.AutoField(primary_key=True, verbose_name="Farmer ID")
    firstname = models.CharField(max_length=100, help_text="First name of the farmer")
    surname = models.CharField(max_length=100, help_text="Surname of the farmer")
    middlename = models.CharField(max_length=100, blank=True, help_text="Middle name of the farmer")
    date_of_birth = models.DateField(blank=True, null=True, help_text="Date of birth of the farmer")
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        help_text="Gender of the farmer"
    )
    NIN = models.CharField(
        max_length=11,
        unique=True,
        help_text="National Identification Number (11 digits)"
    )
    BVN = models.CharField(
        max_length=11,
        unique=True,
        blank=True,
        null=True,
        help_text="Bank Verification Number (11 digits)"
    )
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(regex=r'^[\d\s\-\+\(\)]{7,20}$', message="Please enter a valid phone number (7-20 characters, digits, spaces, dashes, parentheses, or + allowed).")],
        help_text="Contact phone number"
    )
    address = models.TextField(blank=True, help_text="Residential address of the farmer")
    state = models.ForeignKey(
        State,
        on_delete=models.SET_NULL,
        related_name='farmers',
        blank=True,
        null=True,
        help_text="State of residence"
    )
    LGA = models.ForeignKey(
        LGA,
        on_delete=models.SET_NULL,
        related_name='farmers',
        blank=True,
        null=True,
        verbose_name="LGA",
        help_text="Local Government Area"
    )
    ward = models.CharField(max_length=100, blank=True, help_text="Ward")
    farm_location = models.TextField(blank=True, help_text="Location of the farm")
    group_type = models.ForeignKey(
        GroupType,
        on_delete=models.SET_NULL,
        related_name='farmers',
        blank=True,
        null=True,
        help_text="Type of group the farmer belongs to"
    )
    group_leader_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of the group leader"
    )
    group_leader_phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(regex=r'^[\d\s\-\+\(\)]{7,20}$', message="Please enter a valid phone number (7-20 characters, digits, spaces, dashes, parentheses, or + allowed).")],
        help_text="Phone number of the group leader"
    )
    group_name = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        related_name='members',
        blank=True,
        null=True,
        help_text="Name of the group the farmer belongs to"
    )
    crop = models.CharField(max_length=200, blank=True, help_text="Type of crop(s) the farmer grows")
    picture = models.ImageField(
        upload_to='farmers/',
        blank=True,
        null=True,
        help_text="Picture of the farmer"
    )
    date_registered = models.DateTimeField(auto_now_add=True, help_text="Date and time when farmer was registered")
    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.SET_NULL,
        related_name='registered_farmers',
        blank=True,
        null=True,
        help_text="Vendor who registered this farmer"
    )
    farmer_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current status of the farmer"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Farmer"
        verbose_name_plural = "Farmers"
        ordering = ['-date_registered']
        indexes = [
            models.Index(fields=['surname', 'firstname']),
            models.Index(fields=['farmer_status', 'date_registered']),
            models.Index(fields=['state', 'LGA']),
            models.Index(fields=['NIN']),
            models.Index(fields=['BVN']),
        ]

    def __str__(self):
        return f"{self.firstname} {self.surname} (ID: {self.farmer_id})"

    def get_full_name(self):
        """Return the full name of the farmer"""
        parts = [self.firstname]
        if self.middlename:
            parts.append(self.middlename)
        parts.append(self.surname)
        return ' '.join(parts)
    get_full_name.short_description = 'Full Name'

    def get_absolute_url(self):
        return reverse('admin:farmers_farmer_change', args=[self.pk])


class Group(models.Model):
    """
    Model to store farmer groups with their type and details.
    """
    group_name = models.CharField(max_length=200, help_text="Name of the farmer group")
    group_type = models.ForeignKey(
        GroupType,
        on_delete=models.PROTECT, # Protect the group type from being deleted if it is referenced by a group
        related_name='groups',
        help_text="Select the type of group"
    )
    group_leader = models.ForeignKey(
        'Farmer',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='led_groups',
        help_text="Select the group leader from available farmers (optional)"
    )
    description = models.TextField(blank=True, help_text="Detailed description of the group")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Whether this group is currently active")

    class Meta:
        verbose_name = "Group"
        verbose_name_plural = "Groups"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group_type', 'is_active']),
            models.Index(fields=['group_name']),
        ]

    def __str__(self):
        return f"{self.group_name} ({self.group_type.name})"

    def get_absolute_url(self):
        return reverse('admin:farmers_group_change', args=[self.pk])


class Vendor(models.Model):
    """
    Model to store vendors who register farmers at their locality.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    vendor_id = models.AutoField(primary_key=True, verbose_name="Vendor ID")
    vendor_firstname = models.CharField(max_length=100, help_text="First name of the vendor")
    vendor_surname = models.CharField(max_length=100, help_text="Surname of the vendor")
    vendor_middlename = models.CharField(max_length=100, blank=True, help_text="Middle name of the vendor")
    vendor_company_name = models.CharField(max_length=200, help_text="Company or organization name")
    vendor_address = models.TextField(help_text="Complete address of the vendor")
    vendor_email_address = models.EmailField(unique=True, help_text="Email address of the vendor")
    vendor_phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(regex=r'^[\d\s\-\+\(\)]{7,20}$', message="Please enter a valid phone number (7-20 characters, digits, spaces, dashes, parentheses, or + allowed).")],
        help_text="Contact phone number"
    )
    vendor_registration_no = models.CharField(
        max_length=6,
        unique=True,
        editable=False,
        help_text="6-digit registration number (automatically generated)"
    )
    vendor_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current status of the vendor"
    )
    date_registered = models.DateTimeField(auto_now_add=True, help_text="Date and time when vendor was registered")

    class Meta:
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"
        ordering = ['-date_registered']
        indexes = [
            models.Index(fields=['vendor_status', 'date_registered']),
            models.Index(fields=['vendor_email_address']),
            models.Index(fields=['vendor_registration_no']),
        ]

    def __str__(self):
        return f"{self.vendor_firstname} {self.vendor_surname} ({self.vendor_registration_no})"

    def get_full_name(self):
        """Return the full name of the vendor"""
        parts = [self.vendor_firstname]
        if self.vendor_middlename:
            parts.append(self.vendor_middlename)
        parts.append(self.vendor_surname)
        return ' '.join(parts)
    get_full_name.short_description = 'Full Name'

    def save(self, *args, **kwargs):
        """Generate a unique 6-digit registration number if not set"""
        if not self.vendor_registration_no:
            # Generate a unique 6-digit registration number
            while True:
                registration_no = str(random.randint(100000, 999999))
                if not Vendor.objects.filter(vendor_registration_no=registration_no).exists():
                    self.vendor_registration_no = registration_no
                    break
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('admin:farmers_vendor_change', args=[self.pk])


class RedemptionCenter(models.Model):
    """
    Model to store redemption center information.
    """
    redemption_center_id = models.AutoField(primary_key=True, verbose_name="Redemption Center ID")
    fullname = models.CharField(max_length=200, help_text="Full name of the redemption center")
    redemption_center_address = models.TextField(help_text="Complete address of the redemption center")
    phone_no = models.CharField(
        max_length=20,
        validators=[RegexValidator(regex=r'^[\d\s\-\+\(\)]{7,20}$', message="Please enter a valid phone number (7-20 characters, digits, spaces, dashes, parentheses, or + allowed).")],
        help_text="Contact phone number"
    )
    email = models.EmailField(unique=True, help_text="Email address of the redemption center")
    description = models.TextField(blank=True, help_text="Description of the redemption center (optional)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Redemption Center"
        verbose_name_plural = "Redemption Centers"
        ordering = ['fullname']
        indexes = [
            models.Index(fields=['fullname']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.fullname} (ID: {self.redemption_center_id})"

    def get_absolute_url(self):
        return reverse('admin:farmers_redemptioncenter_change', args=[self.pk])


class Incentive(models.Model):
    """
    Model to store incentives allocated to redemption centers for distribution to farmers.
    """
    incentive_id = models.AutoField(primary_key=True, verbose_name="Incentive ID")
    incentive_name = models.CharField(max_length=200, help_text="Name of the incentive")
    quantity = models.PositiveIntegerField(help_text="Quantity of the incentive")
    redemption_center = models.ForeignKey(
        'RedemptionCenter',
        on_delete=models.CASCADE,
        related_name='incentives',
        help_text="Redemption center where this incentive is allocated"
    )
    date_sent = models.DateField(
        default=date.today,
        help_text="Date when the incentive was sent to the redemption center"
    )
    description = models.TextField(blank=True, help_text="Description of the incentive (optional)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Incentive"
        verbose_name_plural = "Incentives"
        ordering = ['-date_sent', '-created_at']
        indexes = [
            models.Index(fields=['date_sent', 'redemption_center']),
            models.Index(fields=['incentive_name']),
        ]

    def __str__(self):
        return f"{self.incentive_name} - {self.quantity} units ({self.redemption_center.fullname})"

    def get_absolute_url(self):
        return reverse('admin:farmers_incentive_change', args=[self.pk])
