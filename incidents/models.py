from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from assets.models import Asset


class Role(models.Model):
    """
    Model representing user roles for incident management.
    Roles define permissions and responsibilities in the incident management workflow.
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    can_view_incidents = models.BooleanField(default=True)
    can_create_incidents = models.BooleanField(default=False)
    can_update_incidents = models.BooleanField(default=False)
    can_assign_incidents = models.BooleanField(default=False)
    can_close_incidents = models.BooleanField(default=False)
    can_delete_incidents = models.BooleanField(default=False)
    can_manage_roles = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Roles"


class UserRole(models.Model):
    """
    Model representing the association between users and roles.
    A user can have multiple roles, and a role can be assigned to multiple users.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

    class Meta:
        unique_together = ['user', 'role']
        verbose_name_plural = "User Roles"


class IncidentStatus(models.Model):
    """
    Model representing the status of an incident.
    Examples: Open, In Progress, On Hold, Resolved, Closed
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False, help_text="Indicates if this status means the incident is closed")
    order = models.IntegerField(default=0, help_text="Order in which statuses should be displayed")
    color = models.CharField(max_length=20, default="#007bff", help_text="Color code for visual representation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Incident Statuses"
        ordering = ['order', 'name']


class IncidentPriority(models.Model):
    """
    Model representing the priority level of an incident.
    Examples: Low, Medium, High, Critical
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    level = models.IntegerField(default=0, help_text="Numeric level of priority (higher number = higher priority)")
    response_time = models.IntegerField(default=24, help_text="Target response time in hours")
    resolution_time = models.IntegerField(default=72, help_text="Target resolution time in hours")
    color = models.CharField(max_length=20, default="#28a745", help_text="Color code for visual representation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Incident Priorities"
        ordering = ['-level']


class IncidentCategory(models.Model):
    """
    Model representing categories of incidents.
    Examples: Hardware Failure, Software Issue, Network Problem, Security Incident
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='subcategories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Incident Categories"


class Incident(models.Model):
    """
    Model representing an incident or issue related to an asset.
    Tracks details about the incident, its status, priority, and assignment.
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, 
                             related_name='incidents')
    category = models.ForeignKey(IncidentCategory, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='incidents')
    status = models.ForeignKey(IncidentStatus, on_delete=models.PROTECT, related_name='incidents')
    priority = models.ForeignKey(IncidentPriority, on_delete=models.PROTECT, related_name='incidents')
    reported_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reported_incidents')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='assigned_incidents')
    reported_at = models.DateTimeField(default=timezone.now)
    assigned_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    resolution = models.TextField(null=True, blank=True)
    is_public = models.BooleanField(default=True, help_text="Whether this incident is visible to all users")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.status}"

    class Meta:
        ordering = ['-reported_at']


class IncidentComment(models.Model):
    """
    Model representing comments on incidents.
    Allows users to add notes, updates, and communication to an incident.
    """
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='incident_comments')
    comment = models.TextField()
    is_private = models.BooleanField(default=False, help_text="Whether this comment is only visible to staff")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment on {self.incident} by {self.user.username}"

    class Meta:
        ordering = ['created_at']


class IncidentHistory(models.Model):
    """
    Model representing the history of changes to an incident.
    Tracks who made changes, when they were made, and what was changed.
    """
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='incident_changes')
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    change_type = models.CharField(max_length=20, choices=[
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('ASSIGN', 'Assigned'),
        ('STATUS', 'Status Change'),
        ('PRIORITY', 'Priority Change'),
    ])
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Change to {self.incident} by {self.user.username} at {self.changed_at}"

    class Meta:
        verbose_name_plural = "Incident History"
        ordering = ['-changed_at']


class WorkflowTemplate(models.Model):
    """
    Model representing predefined workflows for incident resolution.
    Defines a sequence of steps to follow for specific types of incidents.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(IncidentCategory, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='workflow_templates')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class WorkflowStep(models.Model):
    """
    Model representing individual steps in a workflow template.
    Defines what actions should be taken at each stage of incident resolution.
    """
    workflow = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    order = models.IntegerField(default=0)
    status = models.ForeignKey(IncidentStatus, on_delete=models.SET_NULL, null=True, blank=True)
    estimated_time = models.IntegerField(default=24, help_text="Estimated time to complete this step in hours")
    is_mandatory = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.workflow.name} - Step {self.order}: {self.name}"

    class Meta:
        ordering = ['workflow', 'order']
        unique_together = ['workflow', 'order']
