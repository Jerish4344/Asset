from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import (
    Role, UserRole, IncidentStatus, IncidentPriority, IncidentCategory,
    Incident, IncidentComment, WorkflowTemplate, WorkflowStep
)
from assets.models import Asset


class RoleForm(forms.ModelForm):
    """
    Form for creating and editing user roles for incident management
    """
    class Meta:
        model = Role
        fields = [
            'name', 'description', 'can_view_incidents', 'can_create_incidents',
            'can_update_incidents', 'can_assign_incidents', 'can_close_incidents',
            'can_delete_incidents', 'can_manage_roles'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) == 0:
            raise ValidationError("Role name cannot be empty.")
        
        # Check if role name already exists (case-insensitive)
        existing = Role.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("A role with this name already exists.")
        
        return name


class UserRoleForm(forms.ModelForm):
    """
    Form for assigning roles to users
    """
    class Meta:
        model = UserRole
        fields = ['user', 'role', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order users alphabetically by username for better UX
        self.fields['user'].queryset = User.objects.all().order_by('username')
        # Order roles alphabetically by name for better UX
        self.fields['role'].queryset = Role.objects.all().order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        role = cleaned_data.get('role')
        
        # Check if this user-role combination already exists
        if user and role and not self.instance.pk:
            if UserRole.objects.filter(user=user, role=role).exists():
                raise ValidationError("This user already has this role assigned.")
        
        return cleaned_data


class IncidentStatusForm(forms.ModelForm):
    """
    Form for creating and editing incident statuses
    """
    class Meta:
        model = IncidentStatus
        fields = ['name', 'description', 'is_default', 'is_closed', 'order', 'color']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) == 0:
            raise ValidationError("Status name cannot be empty.")
        
        # Check if status name already exists (case-insensitive)
        existing = IncidentStatus.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("A status with this name already exists.")
        
        return name

    def clean(self):
        cleaned_data = super().clean()
        is_default = cleaned_data.get('is_default')
        
        # If this status is being set as default, ensure no other status is default
        if is_default and not self.instance.pk:
            if IncidentStatus.objects.filter(is_default=True).exists():
                self.add_error('is_default', "Another status is already set as default.")
        
        return cleaned_data


class IncidentPriorityForm(forms.ModelForm):
    """
    Form for creating and editing incident priorities
    """
    class Meta:
        model = IncidentPriority
        fields = ['name', 'description', 'level', 'response_time', 'resolution_time', 'color']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) == 0:
            raise ValidationError("Priority name cannot be empty.")
        
        # Check if priority name already exists (case-insensitive)
        existing = IncidentPriority.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("A priority with this name already exists.")
        
        return name

    def clean_level(self):
        level = self.cleaned_data.get('level')
        if level < 0:
            raise ValidationError("Priority level cannot be negative.")
        return level

    def clean_response_time(self):
        time = self.cleaned_data.get('response_time')
        if time < 0:
            raise ValidationError("Response time cannot be negative.")
        return time

    def clean_resolution_time(self):
        time = self.cleaned_data.get('resolution_time')
        if time < 0:
            raise ValidationError("Resolution time cannot be negative.")
        return time


class IncidentCategoryForm(forms.ModelForm):
    """
    Form for creating and editing incident categories
    """
    class Meta:
        model = IncidentCategory
        fields = ['name', 'description', 'parent']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter parent categories to exclude the current category (to prevent self-reference)
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = IncidentCategory.objects.exclude(
                pk=self.instance.pk
            ).order_by('name')
        else:
            self.fields['parent'].queryset = IncidentCategory.objects.all().order_by('name')

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) == 0:
            raise ValidationError("Category name cannot be empty.")
        
        # Check if category name already exists (case-insensitive)
        existing = IncidentCategory.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("A category with this name already exists.")
        
        return name

    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        
        # Check for circular reference in parent-child relationship
        if parent:
            current_parent = parent
            while current_parent:
                if self.instance and current_parent.pk == self.instance.pk:
                    self.add_error('parent', "Circular reference detected. A category cannot be its own ancestor.")
                    break
                current_parent = current_parent.parent
        
        return cleaned_data


class IncidentForm(forms.ModelForm):
    """
    Form for creating and editing incidents
    """
    class Meta:
        model = Incident
        fields = [
            'title', 'description', 'asset', 'category', 'status', 'priority',
            'assigned_to', 'due_date', 'resolution', 'is_public'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'resolution': forms.Textarea(attrs={'rows': 5}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the user from kwargs
        super().__init__(*args, **kwargs)
        
        # Filter active assets only
        self.fields['asset'].queryset = Asset.objects.filter(is_active=1).order_by('asset_name')
        
        # Order categories alphabetically
        self.fields['category'].queryset = IncidentCategory.objects.all().order_by('name')
        
        # Order statuses by their defined order
        self.fields['status'].queryset = IncidentStatus.objects.all().order_by('order', 'name')
        
        # Order priorities by level (highest first)
        self.fields['priority'].queryset = IncidentPriority.objects.all().order_by('-level')
        
        # Filter users who can be assigned (those with appropriate roles)
        assignable_users = User.objects.filter(
            user_roles__role__can_update_incidents=True,
            user_roles__is_active=True
        ).distinct().order_by('username')
        self.fields['assigned_to'].queryset = assignable_users
        
        # If this is a new incident, set the default status
        if not self.instance.pk:
            try:
                default_status = IncidentStatus.objects.get(is_default=True)
                self.fields['status'].initial = default_status
            except IncidentStatus.DoesNotExist:
                pass

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) == 0:
            raise ValidationError("Incident title cannot be empty.")
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description and len(description.strip()) == 0:
            raise ValidationError("Incident description cannot be empty.")
        return description


class IncidentCommentForm(forms.ModelForm):
    """
    Form for adding comments to incidents
    """
    class Meta:
        model = IncidentComment
        fields = ['comment', 'is_private']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add your comment here...'}),
        }

    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        if comment and len(comment.strip()) == 0:
            raise ValidationError("Comment cannot be empty.")
        return comment


class WorkflowTemplateForm(forms.ModelForm):
    """
    Form for creating and editing workflow templates
    """
    class Meta:
        model = WorkflowTemplate
        fields = ['name', 'description', 'category', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order categories alphabetically
        self.fields['category'].queryset = IncidentCategory.objects.all().order_by('name')

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) == 0:
            raise ValidationError("Workflow template name cannot be empty.")
        
        # Check if workflow name already exists (case-insensitive)
        existing = WorkflowTemplate.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("A workflow template with this name already exists.")
        
        return name


class WorkflowStepForm(forms.ModelForm):
    """
    Form for creating and editing workflow steps
    """
    class Meta:
        model = WorkflowStep
        fields = ['name', 'description', 'order', 'status', 'estimated_time', 'is_mandatory']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        workflow = kwargs.pop('workflow', None)  # Get the workflow from kwargs
        super().__init__(*args, **kwargs)
        
        # Set the workflow if provided
        if workflow:
            self.instance.workflow = workflow
        
        # Order statuses by their defined order
        self.fields['status'].queryset = IncidentStatus.objects.all().order_by('order', 'name')
        
        # If this is a new step, suggest the next order number
        if not self.instance.pk and workflow:
            next_order = WorkflowStep.objects.filter(workflow=workflow).count()
            self.fields['order'].initial = next_order

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) == 0:
            raise ValidationError("Step name cannot be empty.")
        return name

    def clean_estimated_time(self):
        time = self.cleaned_data.get('estimated_time')
        if time < 0:
            raise ValidationError("Estimated time cannot be negative.")
        return time

    def clean(self):
        cleaned_data = super().clean()
        order = cleaned_data.get('order')
        
        if order < 0:
            self.add_error('order', "Order cannot be negative.")
        
        # Check if this order already exists for this workflow
        if self.instance.workflow:
            existing = WorkflowStep.objects.filter(
                workflow=self.instance.workflow,
                order=order
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                self.add_error('order', "A step with this order already exists in this workflow.")
        
        return cleaned_data
