from django import forms
from django.core.exceptions import ValidationError
from .models import Asset, AssetCategory, AssetFeature, AssetLocation, AssetNetworkAddress


class AssetCategoryForm(forms.ModelForm):
    """
    Form for creating and editing asset categories
    """
    # The model stores ``is_active`` as an ``IntegerField`` (1 / 0) but in the
    # UI we want to present it as a boolean checkbox.  We therefore replace the
    # auto-generated form field with a ``BooleanField`` and transparently
    # convert the value back to an integer during cleaning.
    class Meta:
        model = AssetCategory
        fields = ['category_name', 'category_type', 'is_active', 'valid_from', 'valid_to']
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local', 'required': False}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Replace the IntegerField with a BooleanField presented as a checkbox.
        self.fields['is_active'] = forms.BooleanField(
            label='Active',
            required=False,
        )

        # Initial value: use instance value when editing, otherwise default True.
        if self.instance and self.instance.pk:
            self.initial['is_active'] = bool(self.instance.is_active)
        else:
            self.initial.setdefault('is_active', True)

    def clean_category_name(self):
        name = self.cleaned_data.get('category_name')
        if name and len(name.strip()) == 0:
            raise ValidationError("Category name cannot be empty.")
        return name

    def clean_is_active(self):
        """
        Convert the checkbox boolean into the integer value expected by
        the model (1 for True / checked, 0 for False / unchecked).
        """
        return 1 if self.cleaned_data.get('is_active') else 0


class AssetFeatureForm(forms.ModelForm):
    """
    Form for creating and editing asset features
    """
    class Meta:
        model = AssetFeature
        fields = ['feature_type', 'feature_name', 'feature_desc', 'is_active', 'valid_from', 'valid_to']
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local', 'required': False}),
            'feature_desc': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_feature_name(self):
        name = self.cleaned_data.get('feature_name')
        if name and len(name.strip()) == 0:
            raise ValidationError("Feature name cannot be empty.")
        return name

    # ------------------------------------------------------------------ #
    # Handle IntegerField is_active as boolean checkbox                  #
    # ------------------------------------------------------------------ #

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'] = forms.BooleanField(label='Active', required=False)
        if self.instance and self.instance.pk:
            self.initial['is_active'] = bool(self.instance.is_active)
        else:
            self.initial.setdefault('is_active', True)

    def clean_is_active(self):
        return 1 if self.cleaned_data.get('is_active') else 0


class AssetLocationForm(forms.ModelForm):
    """
    Form for creating and editing asset locations
    """
    class Meta:
        model = AssetLocation
        fields = [
            'address_type', 'address_value', 'address_value2', 'address_value3',
            'street_name', 'city', 'state', 'country', 'is_active', 'valid_from', 'valid_to'
        ]
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local', 'required': False}),
        }

    def clean_address_value(self):
        address_type = self.cleaned_data.get('address_type')
        address_value = self.cleaned_data.get('address_value')
        
        if address_type == 'IP_ADDRESS':
            # Basic IP address validation
            parts = address_value.split('.')
            if len(parts) != 4:
                raise ValidationError("Invalid IP address format. Use format: xxx.xxx.xxx.xxx")
            for part in parts:
                try:
                    num = int(part)
                    if num < 0 or num > 255:
                        raise ValidationError("IP address segments must be between 0 and 255.")
                except ValueError:
                    raise ValidationError("IP address must contain only numbers and dots.")
        
        elif address_type == 'MAC_ID':
            # Basic MAC address validation
            address_value = address_value.replace('-', ':').replace('.', ':')
            parts = address_value.split(':')
            if len(parts) != 6:
                raise ValidationError("Invalid MAC address format. Use format: XX:XX:XX:XX:XX:XX")
            for part in parts:
                if len(part) != 2 or not all(c in '0123456789ABCDEFabcdef' for c in part):
                    raise ValidationError("MAC address must contain only hexadecimal digits.")
        
        return address_value

    # ------------------------------------------------------------------ #
    # Handle IntegerField is_active as boolean checkbox                  #
    # ------------------------------------------------------------------ #

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'] = forms.BooleanField(label='Active', required=False)
        if self.instance and self.instance.pk:
            self.initial['is_active'] = bool(self.instance.is_active)
        else:
            self.initial.setdefault('is_active', True)

    def clean_is_active(self):
        return 1 if self.cleaned_data.get('is_active') else 0


class AssetNetworkAddressForm(forms.ModelForm):
    """
    Form for creating and editing asset network addresses
    """
    class Meta:
        model = AssetNetworkAddress
        fields = ['asset', 'address_type', 'address_value', 'is_active', 'valid_from', 'valid_to']
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local', 'required': False}),
        }

    def clean_address_value(self):
        address_type = self.cleaned_data.get('address_type')
        address_value = self.cleaned_data.get('address_value')
        
        if address_type == 'IP_ADDRESS':
            # Basic IP address validation
            parts = address_value.split('.')
            if len(parts) != 4:
                raise ValidationError("Invalid IP address format. Use format: xxx.xxx.xxx.xxx")
            for part in parts:
                try:
                    num = int(part)
                    if num < 0 or num > 255:
                        raise ValidationError("IP address segments must be between 0 and 255.")
                except ValueError:
                    raise ValidationError("IP address must contain only numbers and dots.")
        
        elif address_type == 'MAC_ID':
            # Basic MAC address validation
            address_value = address_value.replace('-', ':').replace('.', ':')
            parts = address_value.split(':')
            if len(parts) != 6:
                raise ValidationError("Invalid MAC address format. Use format: XX:XX:XX:XX:XX:XX")
            for part in parts:
                if len(part) != 2 or not all(c in '0123456789ABCDEFabcdef' for c in part):
                    raise ValidationError("MAC address must contain only hexadecimal digits.")
        
        return address_value

    # ------------------------------------------------------------------ #
    # Handle IntegerField is_active as boolean checkbox                  #
    # ------------------------------------------------------------------ #

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'] = forms.BooleanField(label='Active', required=False)
        if self.instance and self.instance.pk:
            self.initial['is_active'] = bool(self.instance.is_active)
        else:
            self.initial.setdefault('is_active', True)

    def clean_is_active(self):
        return 1 if self.cleaned_data.get('is_active') else 0


class AssetForm(forms.ModelForm):
    """
    Form for creating and editing assets
    """
    class Meta:
        model = Asset
        fields = [
            'asset_name', 'category', 'asset_make', 'purchase_id', 'asset_type',
            'feature', 'usage_id', 'parent_asset', 'location', 'asset_purpose',
            'is_active', 'valid_from', 'valid_to'
        ]
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local', 'required': False}),
            'asset_purpose': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter parent_asset to exclude the current asset (to prevent self-reference)
        if self.instance and self.instance.pk:
            self.fields['parent_asset'].queryset = Asset.objects.filter(
                is_active=1
            ).exclude(pk=self.instance.pk)
        else:
            self.fields['parent_asset'].queryset = Asset.objects.filter(is_active=1)

        # Replace IntegerField is_active with BooleanField
        self.fields['is_active'] = forms.BooleanField(label='Active', required=False)
        if self.instance and self.instance.pk:
            self.initial['is_active'] = bool(self.instance.is_active)
        else:
            self.initial.setdefault('is_active', True)

    def clean_is_active(self):
        return 1 if self.cleaned_data.get('is_active') else 0


class ExcelImportForm(forms.Form):
    """
    Form for importing asset data from Excel files
    """
    excel_file = forms.FileField(
        label='Select Excel File',
        help_text='Upload an Excel file containing asset data.'
    )
    sheet_name = forms.CharField(
        required=False,
        label='Sheet Name (Optional)',
        help_text='Leave blank to use the first sheet.'
    )
    category = forms.ModelChoiceField(
        queryset=AssetCategory.objects.filter(is_active=1),
        required=True,
        label='Asset Category',
        help_text='Select the category for the imported assets.'
    )
    
    def clean_excel_file(self):
        excel_file = self.cleaned_data.get('excel_file')
        if excel_file:
            if not excel_file.name.endswith(('.xls', '.xlsx')):
                raise ValidationError('File must be an Excel file (.xls or .xlsx)')
            
            # Check file size (limit to 10MB)
            if excel_file.size > 10 * 1024 * 1024:  # 10MB in bytes
                raise ValidationError('File size must be less than 10MB')
                
        return excel_file
