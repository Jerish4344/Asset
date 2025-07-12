from django.db import models
from django.utils import timezone


class AssetCategory(models.Model):
    """
    Model representing categories of assets (e.g., Server, Computer, Premise, etc.)
    """
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100, null=True, blank=True)
    category_type = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.category_name} ({self.category_id})"

    class Meta:
        verbose_name_plural = "Asset Categories"


class AssetFeature(models.Model):
    """
    Model representing features of assets (e.g., RAM, PROCESSOR, HARDDISK, etc.)
    """
    feature_id = models.AutoField(primary_key=True)
    feature_type = models.CharField(max_length=100, null=True, blank=True)
    feature_name = models.CharField(max_length=100, null=True, blank=True)
    feature_desc = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.feature_type}: {self.feature_name}"

    class Meta:
        verbose_name_plural = "Asset Features"


class AssetLocation(models.Model):
    """
    Model representing locations of assets, including physical addresses and network addresses
    """
    location_id = models.AutoField(primary_key=True)
    address_type = models.CharField(max_length=100, null=True, blank=True)
    address_value = models.CharField(max_length=100, null=True, blank=True)
    address_value2 = models.CharField(max_length=100, null=True, blank=True)
    address_value3 = models.CharField(max_length=100, null=True, blank=True)
    street_name = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.address_type in ['IP_ADDRESS', 'MAC_ID']:
            return f"{self.address_type}: {self.address_value}"
        return f"{self.city}, {self.state}, {self.country}"

    class Meta:
        verbose_name_plural = "Asset Locations"


class Asset(models.Model):
    """
    Model representing assets (e.g., Servers, Computers, Premises, etc.)
    
    An asset can have features, a location, and can be part of a hierarchy
    (parent-child relationship with other assets).
    """
    asset_id = models.AutoField(primary_key=True)
    asset_name = models.CharField(max_length=100, null=True, blank=True, help_text="Computer name from Excel")
    # Changed from varchar to ForeignKey for proper relationship
    category = models.ForeignKey(AssetCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    asset_make = models.CharField(max_length=100, null=True, blank=True, help_text="Server make from Excel")
    purchase_id = models.IntegerField(null=True, blank=True)
    asset_type = models.CharField(max_length=100, null=True, blank=True, help_text="Type from Excel")
    # Changed from int to ForeignKey for proper relationship
    feature = models.ForeignKey(AssetFeature, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    usage_id = models.IntegerField(null=True, blank=True)
    # Self-referential relationship for parent-child hierarchy
    parent_asset = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_assets')
    # Changed from int to ForeignKey for proper relationship
    location = models.ForeignKey(AssetLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    asset_purpose = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.asset_name} ({self.asset_id})"

    class Meta:
        verbose_name_plural = "Assets"


class AssetNetworkAddress(models.Model):
    """
    Model representing network addresses for assets (IP_ADDRESS, MAC_ID)
    This is a convenience model to easily manage multiple network addresses per asset
    """
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='network_addresses')
    address_type = models.CharField(max_length=20, choices=[
        ('IP_ADDRESS', 'IP Address'),
        ('MAC_ID', 'MAC ID'),
    ])
    address_value = models.CharField(max_length=100)
    is_active = models.IntegerField(default=1)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.address_type}: {self.address_value} ({self.asset.asset_name})"

    class Meta:
        verbose_name_plural = "Asset Network Addresses"
        unique_together = ['asset', 'address_type', 'address_value']
