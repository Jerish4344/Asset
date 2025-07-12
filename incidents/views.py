from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.base import TemplateView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q, F, Sum, Avg, Min, Max
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied

import csv
import io
import json
import logging
from datetime import datetime, timedelta

from .models import (
    Role, UserRole, IncidentStatus, IncidentPriority, IncidentCategory,
    Incident, IncidentComment, IncidentHistory, WorkflowTemplate, WorkflowStep
)
from .forms import (
    RoleForm, UserRoleForm, IncidentStatusForm, IncidentPriorityForm, 
    IncidentCategoryForm, IncidentForm, IncidentCommentForm,
    WorkflowTemplateForm, WorkflowStepForm
)
from assets.models import Asset

# Configure logger
logger = logging.getLogger(__name__)


# Permission Mixins
class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Base mixin for checking role-based permissions
    """
    permission_name = None
    
    def test_func(self):
        # Admin users bypass all permission checks
        if self.request.user.is_superuser:
            return True
        
        # Check if user has the required role permission
        if self.permission_name:
            user_roles = UserRole.objects.filter(
                user=self.request.user,
                is_active=True,
                role__is_active=True
            )
            
            for user_role in user_roles:
                if getattr(user_role.role, self.permission_name, False):
                    return True
        
        return False


class CanViewIncidentsMixin(RoleRequiredMixin):
    """Mixin for checking if user can view incidents"""
    permission_name = 'can_view_incidents'


class CanCreateIncidentsMixin(RoleRequiredMixin):
    """Mixin for checking if user can create incidents"""
    permission_name = 'can_create_incidents'


class CanUpdateIncidentsMixin(RoleRequiredMixin):
    """Mixin for checking if user can update incidents"""
    permission_name = 'can_update_incidents'


class CanAssignIncidentsMixin(RoleRequiredMixin):
    """Mixin for checking if user can assign incidents"""
    permission_name = 'can_assign_incidents'


class CanCloseIncidentsMixin(RoleRequiredMixin):
    """Mixin for checking if user can close incidents"""
    permission_name = 'can_close_incidents'


class CanDeleteIncidentsMixin(RoleRequiredMixin):
    """Mixin for checking if user can delete incidents"""
    permission_name = 'can_delete_incidents'


class CanManageRolesMixin(RoleRequiredMixin):
    """Mixin for checking if user can manage roles"""
    permission_name = 'can_manage_roles'


# Dashboard View
class IncidentDashboardView(CanViewIncidentsMixin, TemplateView):
    """
    Dashboard view showing incident statistics and summary information
    """
    template_name = 'incidents/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get counts of incidents by status
        status_counts = IncidentStatus.objects.annotate(
            incident_count=Count('incidents')
        ).values('name', 'incident_count', 'color').order_by('order')
        
        # Get counts of incidents by priority
        priority_counts = IncidentPriority.objects.annotate(
            incident_count=Count('incidents')
        ).values('name', 'incident_count', 'color', 'level').order_by('-level')
        
        # Get counts of incidents by category
        category_counts = IncidentCategory.objects.annotate(
            incident_count=Count('incidents')
        ).values('name', 'incident_count').order_by('-incident_count')[:10]
        
        # Get recent incidents
        recent_incidents = Incident.objects.select_related(
            'status', 'priority', 'reported_by', 'assigned_to'
        ).order_by('-reported_at')[:10]
        
        # Get overdue incidents
        overdue_incidents = Incident.objects.filter(
            status__is_closed=False,
            due_date__lt=timezone.now()
        ).select_related(
            'status', 'priority', 'reported_by', 'assigned_to'
        ).order_by('due_date')[:10]
        
        # Get unassigned incidents
        unassigned_incidents = Incident.objects.filter(
            assigned_to__isnull=True,
            status__is_closed=False
        ).select_related(
            'status', 'priority', 'reported_by'
        ).order_by('-reported_at')[:10]
        
        # Get incidents assigned to current user
        my_incidents = Incident.objects.filter(
            assigned_to=self.request.user,
            status__is_closed=False
        ).select_related(
            'status', 'priority', 'reported_by'
        ).order_by('-reported_at')[:10]
        
        # Get incidents reported by current user
        reported_incidents = Incident.objects.filter(
            reported_by=self.request.user
        ).select_related(
            'status', 'priority', 'assigned_to'
        ).order_by('-reported_at')[:10]
        
        # Get incident resolution time statistics
        resolution_stats = Incident.objects.filter(
            resolved_at__isnull=False
        ).aggregate(
            avg_resolution_time=Avg(F('resolved_at') - F('reported_at')),
            min_resolution_time=Min(F('resolved_at') - F('reported_at')),
            max_resolution_time=Max(F('resolved_at') - F('reported_at'))
        )
        
        # Get total incident count
        total_incidents = Incident.objects.count()
        open_incidents = Incident.objects.filter(status__is_closed=False).count()
        closed_incidents = total_incidents - open_incidents
        
        # Get incident trend data (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_incidents = Incident.objects.filter(
            reported_at__gte=thirty_days_ago
        ).extra(
            select={'date': "DATE(reported_at)"}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Prepare trend data for chart
        trend_dates = []
        trend_counts = []
        for item in daily_incidents:
            trend_dates.append(item['date'].strftime('%Y-%m-%d'))
            trend_counts.append(item['count'])
        
        context.update({
            'total_incidents': total_incidents,
            'open_incidents': open_incidents,
            'closed_incidents': closed_incidents,
            'status_counts': status_counts,
            'priority_counts': priority_counts,
            'category_counts': category_counts,
            'recent_incidents': recent_incidents,
            'overdue_incidents': overdue_incidents,
            'unassigned_incidents': unassigned_incidents,
            'my_incidents': my_incidents,
            'reported_incidents': reported_incidents,
            'resolution_stats': resolution_stats,
            'trend_dates': json.dumps(trend_dates),
            'trend_counts': json.dumps(trend_counts),
        })
        
        return context


# Role Management Views
class RoleListView(CanManageRolesMixin, ListView):
    """
    View to list all roles
    """
    model = Role
    template_name = 'incidents/role_list.html'
    context_object_name = 'roles'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) | 
                Q(description__icontains=search_term)
            )
        
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        return context


class RoleDetailView(CanManageRolesMixin, DetailView):
    """
    View to show details of a specific role
    """
    model = Role
    template_name = 'incidents/role_detail.html'
    context_object_name = 'role'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get users with this role
        context['user_roles'] = UserRole.objects.filter(
            role=self.object
        ).select_related('user').order_by('user__username')
        
        return context


class RoleCreateView(CanManageRolesMixin, CreateView):
    """
    View to create a new role
    """
    model = Role
    form_class = RoleForm
    template_name = 'incidents/role_form.html'
    success_url = reverse_lazy('role_list')

    def form_valid(self, form):
        messages.success(self.request, 'Role created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating role. Please check the form.')
        return super().form_invalid(form)


class RoleUpdateView(CanManageRolesMixin, UpdateView):
    """
    View to update an existing role
    """
    model = Role
    form_class = RoleForm
    template_name = 'incidents/role_form.html'
    context_object_name = 'role'

    def get_success_url(self):
        return reverse_lazy('role_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Role updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating role. Please check the form.')
        return super().form_invalid(form)


class RoleDeleteView(CanManageRolesMixin, DeleteView):
    """
    View to delete a role
    """
    model = Role
    template_name = 'incidents/role_confirm_delete.html'
    success_url = reverse_lazy('role_list')
    context_object_name = 'role'

    def delete(self, request, *args, **kwargs):
        role = self.get_object()
        
        # Check if there are users assigned to this role
        if UserRole.objects.filter(role=role).exists():
            messages.error(request, 'Cannot delete role. There are users assigned to it.')
            return redirect('role_detail', pk=role.pk)
        
        messages.success(request, f'Role "{role.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# User Role Views
class UserRoleListView(CanManageRolesMixin, ListView):
    """
    View to list all user role assignments
    """
    model = UserRole
    template_name = 'incidents/user_role_list.html'
    context_object_name = 'user_roles'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active status if specified
        active_filter = self.request.GET.get('active')
        if active_filter == '1':
            queryset = queryset.filter(is_active=True)
        elif active_filter == '0':
            queryset = queryset.filter(is_active=False)
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(user__username__icontains=search_term) | 
                Q(user__first_name__icontains=search_term) |
                Q(user__last_name__icontains=search_term) |
                Q(user__email__icontains=search_term) |
                Q(role__name__icontains=search_term)
            )
        
        # Filter by role if provided
        role_id = self.request.GET.get('role', '')
        if role_id and role_id.isdigit():
            queryset = queryset.filter(role_id=role_id)
        
        # Filter by user if provided
        user_id = self.request.GET.get('user', '')
        if user_id and user_id.isdigit():
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.select_related('user', 'role').order_by('user__username', 'role__name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        context['active_filter'] = self.request.GET.get('active', '')
        context['role_filter'] = self.request.GET.get('role', '')
        context['user_filter'] = self.request.GET.get('user', '')
        
        # Get roles for filtering
        context['roles'] = Role.objects.all().order_by('name')
        
        return context


class UserRoleCreateView(CanManageRolesMixin, CreateView):
    """
    View to create a new user role assignment
    """
    model = UserRole
    form_class = UserRoleForm
    template_name = 'incidents/user_role_form.html'
    success_url = reverse_lazy('user_role_list')

    def get_initial(self):
        initial = super().get_initial()
        # Pre-select user if provided in URL
        user_id = self.request.GET.get('user', '')
        if user_id and user_id.isdigit():
            initial['user'] = user_id
        # Pre-select role if provided in URL
        role_id = self.request.GET.get('role', '')
        if role_id and role_id.isdigit():
            initial['role'] = role_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'User role assignment created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating user role assignment. Please check the form.')
        return super().form_invalid(form)


class UserRoleUpdateView(CanManageRolesMixin, UpdateView):
    """
    View to update an existing user role assignment
    """
    model = UserRole
    form_class = UserRoleForm
    template_name = 'incidents/user_role_form.html'
    context_object_name = 'user_role'
    success_url = reverse_lazy('user_role_list')

    def form_valid(self, form):
        messages.success(self.request, 'User role assignment updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating user role assignment. Please check the form.')
        return super().form_invalid(form)


class UserRoleDeleteView(CanManageRolesMixin, DeleteView):
    """
    View to delete a user role assignment
    """
    model = UserRole
    template_name = 'incidents/user_role_confirm_delete.html'
    success_url = reverse_lazy('user_role_list')
    context_object_name = 'user_role'

    def delete(self, request, *args, **kwargs):
        user_role = self.get_object()
        messages.success(request, f'Role "{user_role.role.name}" removed from user "{user_role.user.username}" successfully.')
        return super().delete(request, *args, **kwargs)


# Incident Status Views
class IncidentStatusListView(CanManageRolesMixin, ListView):
    """
    View to list all incident statuses
    """
    model = IncidentStatus
    template_name = 'incidents/status_list.html'
    context_object_name = 'statuses'

    def get_queryset(self):
        return super().get_queryset().order_by('order', 'name')


class IncidentStatusCreateView(CanManageRolesMixin, CreateView):
    """
    View to create a new incident status
    """
    model = IncidentStatus
    form_class = IncidentStatusForm
    template_name = 'incidents/status_form.html'
    success_url = reverse_lazy('incident_status_list')

    def form_valid(self, form):
        messages.success(self.request, 'Incident status created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating incident status. Please check the form.')
        return super().form_invalid(form)


class IncidentStatusUpdateView(CanManageRolesMixin, UpdateView):
    """
    View to update an existing incident status
    """
    model = IncidentStatus
    form_class = IncidentStatusForm
    template_name = 'incidents/status_form.html'
    context_object_name = 'status'
    success_url = reverse_lazy('incident_status_list')

    def form_valid(self, form):
        messages.success(self.request, 'Incident status updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating incident status. Please check the form.')
        return super().form_invalid(form)


class IncidentStatusDeleteView(CanManageRolesMixin, DeleteView):
    """
    View to delete an incident status
    """
    model = IncidentStatus
    template_name = 'incidents/status_confirm_delete.html'
    success_url = reverse_lazy('incident_status_list')
    context_object_name = 'status'

    def delete(self, request, *args, **kwargs):
        status = self.get_object()
        
        # Check if there are incidents using this status
        if Incident.objects.filter(status=status).exists():
            messages.error(request, 'Cannot delete status. There are incidents using it.')
            return redirect('incident_status_list')
        
        # Check if there are workflow steps using this status
        if WorkflowStep.objects.filter(status=status).exists():
            messages.error(request, 'Cannot delete status. There are workflow steps using it.')
            return redirect('incident_status_list')
        
        messages.success(request, f'Incident status "{status.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Incident Priority Views
class IncidentPriorityListView(CanManageRolesMixin, ListView):
    """
    View to list all incident priorities
    """
    model = IncidentPriority
    template_name = 'incidents/priority_list.html'
    context_object_name = 'priorities'

    def get_queryset(self):
        return super().get_queryset().order_by('-level')


class IncidentPriorityCreateView(CanManageRolesMixin, CreateView):
    """
    View to create a new incident priority
    """
    model = IncidentPriority
    form_class = IncidentPriorityForm
    template_name = 'incidents/priority_form.html'
    success_url = reverse_lazy('incident_priority_list')

    def form_valid(self, form):
        messages.success(self.request, 'Incident priority created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating incident priority. Please check the form.')
        return super().form_invalid(form)


class IncidentPriorityUpdateView(CanManageRolesMixin, UpdateView):
    """
    View to update an existing incident priority
    """
    model = IncidentPriority
    form_class = IncidentPriorityForm
    template_name = 'incidents/priority_form.html'
    context_object_name = 'priority'
    success_url = reverse_lazy('incident_priority_list')

    def form_valid(self, form):
        messages.success(self.request, 'Incident priority updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating incident priority. Please check the form.')
        return super().form_invalid(form)


class IncidentPriorityDeleteView(CanManageRolesMixin, DeleteView):
    """
    View to delete an incident priority
    """
    model = IncidentPriority
    template_name = 'incidents/priority_confirm_delete.html'
    success_url = reverse_lazy('incident_priority_list')
    context_object_name = 'priority'

    def delete(self, request, *args, **kwargs):
        priority = self.get_object()
        
        # Check if there are incidents using this priority
        if Incident.objects.filter(priority=priority).exists():
            messages.error(request, 'Cannot delete priority. There are incidents using it.')
            return redirect('incident_priority_list')
        
        messages.success(request, f'Incident priority "{priority.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Incident Category Views
class IncidentCategoryListView(CanManageRolesMixin, ListView):
    """
    View to list all incident categories
    """
    model = IncidentCategory
    template_name = 'incidents/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) | 
                Q(description__icontains=search_term)
            )
        
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        return context


class IncidentCategoryDetailView(CanManageRolesMixin, DetailView):
    """
    View to show details of a specific incident category
    """
    model = IncidentCategory
    template_name = 'incidents/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get incidents in this category
        context['incidents'] = Incident.objects.filter(
            category=self.object
        ).select_related('status', 'priority').order_by('-reported_at')[:10]
        
        # Get subcategories
        context['subcategories'] = IncidentCategory.objects.filter(
            parent=self.object
        ).order_by('name')
        
        # Get workflow templates for this category
        context['workflow_templates'] = WorkflowTemplate.objects.filter(
            category=self.object,
            is_active=True
        ).order_by('name')
        
        return context


class IncidentCategoryCreateView(CanManageRolesMixin, CreateView):
    """
    View to create a new incident category
    """
    model = IncidentCategory
    form_class = IncidentCategoryForm
    template_name = 'incidents/category_form.html'
    success_url = reverse_lazy('incident_category_list')

    def get_initial(self):
        initial = super().get_initial()
        # Pre-select parent category if provided in URL
        parent_id = self.request.GET.get('parent', '')
        if parent_id and parent_id.isdigit():
            initial['parent'] = parent_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Incident category created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating incident category. Please check the form.')
        return super().form_invalid(form)


class IncidentCategoryUpdateView(CanManageRolesMixin, UpdateView):
    """
    View to update an existing incident category
    """
    model = IncidentCategory
    form_class = IncidentCategoryForm
    template_name = 'incidents/category_form.html'
    context_object_name = 'category'

    def get_success_url(self):
        return reverse_lazy('incident_category_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Incident category updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating incident category. Please check the form.')
        return super().form_invalid(form)


class IncidentCategoryDeleteView(CanManageRolesMixin, DeleteView):
    """
    View to delete an incident category
    """
    model = IncidentCategory
    template_name = 'incidents/category_confirm_delete.html'
    success_url = reverse_lazy('incident_category_list')
    context_object_name = 'category'

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        
        # Check if there are incidents using this category
        if Incident.objects.filter(category=category).exists():
            messages.error(request, 'Cannot delete category. There are incidents assigned to it.')
            return redirect('incident_category_detail', pk=category.pk)
        
        # Check if there are subcategories
        if IncidentCategory.objects.filter(parent=category).exists():
            messages.error(request, 'Cannot delete category. There are subcategories assigned to it.')
            return redirect('incident_category_detail', pk=category.pk)
        
        # Check if there are workflow templates using this category
        if WorkflowTemplate.objects.filter(category=category).exists():
            messages.error(request, 'Cannot delete category. There are workflow templates assigned to it.')
            return redirect('incident_category_detail', pk=category.pk)
        
        messages.success(request, f'Incident category "{category.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Incident Views
class IncidentListView(CanViewIncidentsMixin, ListView):
    """
    View to list all incidents
    """
    model = Incident
    template_name = 'incidents/incident_list.html'
    context_object_name = 'incidents'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status if specified
        status_id = self.request.GET.get('status', '')
        if status_id and status_id.isdigit():
            queryset = queryset.filter(status_id=status_id)
        elif status_id == 'open':
            queryset = queryset.filter(status__is_closed=False)
        elif status_id == 'closed':
            queryset = queryset.filter(status__is_closed=True)
        
        # Filter by priority if specified
        priority_id = self.request.GET.get('priority', '')
        if priority_id and priority_id.isdigit():
            queryset = queryset.filter(priority_id=priority_id)
        
        # Filter by category if specified
        category_id = self.request.GET.get('category', '')
        if category_id and category_id.isdigit():
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by asset if specified
        asset_id = self.request.GET.get('asset', '')
        if asset_id and asset_id.isdigit():
            queryset = queryset.filter(asset_id=asset_id)
        
        # Filter by assigned user if specified
        assigned_id = self.request.GET.get('assigned', '')
        if assigned_id and assigned_id.isdigit():
            queryset = queryset.filter(assigned_to_id=assigned_id)
        elif assigned_id == 'me':
            queryset = queryset.filter(assigned_to=self.request.user)
        elif assigned_id == 'unassigned':
            queryset = queryset.filter(assigned_to__isnull=True)
        
        # Filter by reported user if specified
        reported_id = self.request.GET.get('reported', '')
        if reported_id and reported_id.isdigit():
            queryset = queryset.filter(reported_by_id=reported_id)
        elif reported_id == 'me':
            queryset = queryset.filter(reported_by=self.request.user)
        
        # Filter by due date if specified
        due_filter = self.request.GET.get('due', '')
        if due_filter == 'overdue':
            queryset = queryset.filter(
                status__is_closed=False,
                due_date__lt=timezone.now()
            )
        elif due_filter == 'today':
            today = timezone.now().date()
            queryset = queryset.filter(
                status__is_closed=False,
                due_date__date=today
            )
        elif due_filter == 'week':
            today = timezone.now().date()
            week_later = today + timedelta(days=7)
            queryset = queryset.filter(
                status__is_closed=False,
                due_date__date__gte=today,
                due_date__date__lte=week_later
            )
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term) | 
                Q(description__icontains=search_term) |
                Q(resolution__icontains=search_term)
            )
        
        # Default sort by reported date (newest first)
        sort = self.request.GET.get('sort', '-reported_at')
        if sort not in [
            'title', '-title', 'reported_at', '-reported_at', 
            'due_date', '-due_date', 'priority', '-priority'
        ]:
            sort = '-reported_at'
        
        if sort == 'priority':
            queryset = queryset.order_by('priority__level', '-reported_at')
        elif sort == '-priority':
            queryset = queryset.order_by('-priority__level', '-reported_at')
        else:
            queryset = queryset.order_by(sort)
        
        return queryset.select_related(
            'status', 'priority', 'category', 'asset',
            'reported_by', 'assigned_to'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['priority_filter'] = self.request.GET.get('priority', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['asset_filter'] = self.request.GET.get('asset', '')
        context['assigned_filter'] = self.request.GET.get('assigned', '')
        context['reported_filter'] = self.request.GET.get('reported', '')
        context['due_filter'] = self.request.GET.get('due', '')
        context['sort'] = self.request.GET.get('sort', '-reported_at')
        
        # Get filter options
        context['statuses'] = IncidentStatus.objects.all().order_by('order', 'name')
        context['priorities'] = IncidentPriority.objects.all().order_by('-level')
        context['categories'] = IncidentCategory.objects.all().order_by('name')
        
        # Check permissions for creating incidents
        context['can_create'] = self.request.user.is_superuser or UserRole.objects.filter(
            user=self.request.user,
            is_active=True,
            role__can_create_incidents=True
        ).exists()
        
        return context


class IncidentDetailView(CanViewIncidentsMixin, DetailView):
    """
    View to show details of a specific incident
    """
    model = Incident
    template_name = 'incidents/incident_detail.html'
    context_object_name = 'incident'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get comments for this incident
        if self.request.user.is_staff:
            # Staff can see all comments
            comments = IncidentComment.objects.filter(incident=self.object)
        else:
            # Non-staff can only see public comments
            comments = IncidentComment.objects.filter(
                incident=self.object,
                is_private=False
            )
        
        context['comments'] = comments.select_related('user').order_by('created_at')
        
        # Get history for this incident
        context['history'] = IncidentHistory.objects.filter(
            incident=self.object
        ).select_related('user').order_by('-changed_at')
        
        # Add comment form
        context['comment_form'] = IncidentCommentForm()
        
        # Check permissions
        context['can_update'] = self.request.user.is_superuser or UserRole.objects.filter(
            user=self.request.user,
            is_active=True,
            role__can_update_incidents=True
        ).exists()
        
        context['can_assign'] = self.request.user.is_superuser or UserRole.objects.filter(
            user=self.request.user,
            is_active=True,
            role__can_assign_incidents=True
        ).exists()
        
        context['can_close'] = self.request.user.is_superuser or UserRole.objects.filter(
            user=self.request.user,
            is_active=True,
            role__can_close_incidents=True
        ).exists()
        
        context['can_delete'] = self.request.user.is_superuser or UserRole.objects.filter(
            user=self.request.user,
            is_active=True,
            role__can_delete_incidents=True
        ).exists()
        
        return context


class IncidentCreateView(CanCreateIncidentsMixin, CreateView):
    """
    View to create a new incident
    """
    model = Incident
    form_class = IncidentForm
    template_name = 'incidents/incident_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        
        # Pre-select asset if provided in URL
        asset_id = self.request.GET.get('asset', '')
        if asset_id and asset_id.isdigit():
            initial['asset'] = asset_id
        
        # Pre-select category if provided in URL
        category_id = self.request.GET.get('category', '')
        if category_id and category_id.isdigit():
            initial['category'] = category_id
        
        return initial

    def form_valid(self, form):
        # Set the reported_by field to the current user
        form.instance.reported_by = self.request.user
        form.instance.reported_at = timezone.now()
        
        # If assigned_to is set, record the assignment time
        if form.instance.assigned_to:
            form.instance.assigned_at = timezone.now()
        
        with transaction.atomic():
            response = super().form_valid(form)
            
            # Create history entry for incident creation
            IncidentHistory.objects.create(
                incident=self.object,
                user=self.request.user,
                field_name='incident',
                new_value='Created incident',
                change_type='CREATE'
            )
            
            # If a category is selected and it has an associated workflow template,
            # apply the workflow template
            category = form.cleaned_data.get('category')
            if category:
                workflow_template = WorkflowTemplate.objects.filter(
                    category=category,
                    is_active=True
                ).first()
                
                if workflow_template:
                    # Create history entry for workflow application
                    IncidentHistory.objects.create(
                        incident=self.object,
                        user=self.request.user,
                        field_name='workflow',
                        new_value=f'Applied workflow template: {workflow_template.name}',
                        change_type='UPDATE'
                    )
        
        messages.success(self.request, 'Incident created successfully.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating incident. Please check the form.')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('incident_detail', kwargs={'pk': self.object.pk})


class IncidentUpdateView(CanUpdateIncidentsMixin, UpdateView):
    """
    View to update an existing incident
    """
    model = Incident
    form_class = IncidentForm
    template_name = 'incidents/incident_form.html'
    context_object_name = 'incident'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        old_instance = Incident.objects.get(pk=self.object.pk)
        
        # Check if assigned_to has changed
        if form.instance.assigned_to != old_instance.assigned_to:
            if form.instance.assigned_to:
                form.instance.assigned_at = timezone.now()
                
                # Create history entry for assignment
                IncidentHistory.objects.create(
                    incident=self.object,
                    user=self.request.user,
                    field_name='assigned_to',
                    old_value=str(old_instance.assigned_to) if old_instance.assigned_to else 'Unassigned',
                    new_value=str(form.instance.assigned_to),
                    change_type='ASSIGN'
                )
        
        # Check if status has changed
        if form.instance.status != old_instance.status:
            # Create history entry for status change
            IncidentHistory.objects.create(
                incident=self.object,
                user=self.request.user,
                field_name='status',
                old_value=old_instance.status.name,
                new_value=form.instance.status.name,
                change_type='STATUS'
            )
            
            # If new status is closed, record the closed time
            if form.instance.status.is_closed and not old_instance.status.is_closed:
                form.instance.closed_at = timezone.now()
            
            # If new status is not closed but old one was, clear the closed time
            elif not form.instance.status.is_closed and old_instance.status.is_closed:
                form.instance.closed_at = None
        
        # Check if priority has changed
        if form.instance.priority != old_instance.priority:
            # Create history entry for priority change
            IncidentHistory.objects.create(
                incident=self.object,
                user=self.request.user,
                field_name='priority',
                old_value=old_instance.priority.name,
                new_value=form.instance.priority.name,
                change_type='PRIORITY'
            )
        
        # Check if resolution has been added or changed
        if form.instance.resolution != old_instance.resolution:
            if form.instance.resolution and not old_instance.resolution:
                form.instance.resolved_at = timezone.now()
                
                # Create history entry for resolution
                IncidentHistory.objects.create(
                    incident=self.object,
                    user=self.request.user,
                    field_name='resolution',
                    old_value='No resolution',
                    new_value='Resolution added',
                    change_type='UPDATE'
                )
        
        # For other fields that have changed, create history entries
        for field in ['title', 'description', 'category', 'asset', 'due_date', 'is_public']:
            old_value = getattr(old_instance, field)
            new_value = getattr(form.instance, field)
            
            if old_value != new_value:
                IncidentHistory.objects.create(
                    incident=self.object,
                    user=self.request.user,
                    field_name=field,
                    old_value=str(old_value) if old_value else 'None',
                    new_value=str(new_value) if new_value else 'None',
                    change_type='UPDATE'
                )
        
        messages.success(self.request, 'Incident updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating incident. Please check the form.')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('incident_detail', kwargs={'pk': self.object.pk})


class IncidentDeleteView(CanDeleteIncidentsMixin, DeleteView):
    """
    View to delete an incident
    """
    model = Incident
    template_name = 'incidents/incident_confirm_delete.html'
    success_url = reverse_lazy('incident_list')
    context_object_name = 'incident'

    def delete(self, request, *args, **kwargs):
        incident = self.get_object()
        
        # Create history entry before deletion
        IncidentHistory.objects.create(
            incident=incident,
            user=request.user,
            field_name='incident',
            old_value=f'Incident: {incident.title}',
            new_value='Deleted',
            change_type='DELETE'
        )
        
        messages.success(request, f'Incident "{incident.title}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Incident Comment Views
class AddIncidentCommentView(CanViewIncidentsMixin, View):
    """
    View to add a comment to an incident
    """
    def post(self, request, pk):
        incident = get_object_or_404(Incident, pk=pk)
        form = IncidentCommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.incident = incident
            comment.user = request.user
            comment.save()
            
            # Create history entry for comment
            IncidentHistory.objects.create(
                incident=incident,
                user=request.user,
                field_name='comment',
                new_value=f'Added comment: {comment.comment[:50]}{"..." if len(comment.comment) > 50 else ""}',
                change_type='UPDATE'
            )
            
            messages.success(request, 'Comment added successfully.')
        else:
            messages.error(request, 'Error adding comment. Please check the form.')
        
        return redirect('incident_detail', pk=pk)


class DeleteIncidentCommentView(CanUpdateIncidentsMixin, View):
    """
    View to delete a comment from an incident
    """
    def post(self, request, pk, comment_pk):
        comment = get_object_or_404(IncidentComment, pk=comment_pk, incident__pk=pk)
        
        # Only allow the comment author or staff to delete comments
        if comment.user != request.user and not request.user.is_staff:
            messages.error(request, 'You do not have permission to delete this comment.')
            return redirect('incident_detail', pk=pk)
        
        incident = comment.incident
        comment_preview = comment.comment[:50] + ("..." if len(comment.comment) > 50 else "")
        
        # Create history entry for comment deletion
        IncidentHistory.objects.create(
            incident=incident,
            user=request.user,
            field_name='comment',
            old_value=f'Deleted comment: {comment_preview}',
            change_type='DELETE'
        )
        
        comment.delete()
        messages.success(request, 'Comment deleted successfully.')
        return redirect('incident_detail', pk=pk)


# Workflow Template Views
class WorkflowTemplateListView(CanManageRolesMixin, ListView):
    """
    View to list all workflow templates
    """
    model = WorkflowTemplate
    template_name = 'incidents/workflow_template_list.html'
    context_object_name = 'templates'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active status if specified
        active_filter = self.request.GET.get('active')
        if active_filter == '1':
            queryset = queryset.filter(is_active=True)
        elif active_filter == '0':
            queryset = queryset.filter(is_active=False)
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) | 
                Q(description__icontains=search_term)
            )
        
        # Filter by category if provided
        category_id = self.request.GET.get('category', '')
        if category_id and category_id.isdigit():
            queryset = queryset.filter(category_id=category_id)
        
        return queryset.select_related('category').order_by('-is_active', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        context['active_filter'] = self.request.GET.get('active', '')
        context['category_filter'] = self.request.GET.get('category', '')
        
        # Get categories for filtering
        context['categories'] = IncidentCategory.objects.all().order_by('name')
        
        return context


class WorkflowTemplateDetailView(CanManageRolesMixin, DetailView):
    """
    View to show details of a specific workflow template
    """
    model = WorkflowTemplate
    template_name = 'incidents/workflow_template_detail.html'
    context_object_name = 'template'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get steps for this workflow template
        context['steps'] = WorkflowStep.objects.filter(
            workflow=self.object
        ).select_related('status').order_by('order')
        
        return context


class WorkflowTemplateCreateView(CanManageRolesMixin, CreateView):
    """
    View to create a new workflow template
    """
    model = WorkflowTemplate
    form_class = WorkflowTemplateForm
    template_name = 'incidents/workflow_template_form.html'
    success_url = reverse_lazy('workflow_template_list')

    def get_initial(self):
        initial = super().get_initial()
        # Pre-select category if provided in URL
        category_id = self.request.GET.get('category', '')
        if category_id and category_id.isdigit():
            initial['category'] = category_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Workflow template created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating workflow template. Please check the form.')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('workflow_template_detail', kwargs={'pk': self.object.pk})


class WorkflowTemplateUpdateView(CanManageRolesMixin, UpdateView):
    """
    View to update an existing workflow template
    """
    model = WorkflowTemplate
    form_class = WorkflowTemplateForm
    template_name = 'incidents/workflow_template_form.html'
    context_object_name = 'template'

    def form_valid(self, form):
        messages.success(self.request, 'Workflow template updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating workflow template. Please check the form.')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('workflow_template_detail', kwargs={'pk': self.object.pk})


class WorkflowTemplateDeleteView(CanManageRolesMixin, DeleteView):
    """
    View to delete a workflow template
    """
    model = WorkflowTemplate
    template_name = 'incidents/workflow_template_confirm_delete.html'
    success_url = reverse_lazy('workflow_template_list')
    context_object_name = 'template'

    def delete(self, request, *args, **kwargs):
        template = self.get_object()
        
        # Check if there are steps for this template
        if WorkflowStep.objects.filter(workflow=template).exists():
            # Delete all steps first
            WorkflowStep.objects.filter(workflow=template).delete()
        
        messages.success(request, f'Workflow template "{template.name}" and all its steps deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Workflow Step Views
class WorkflowStepCreateView(CanManageRolesMixin, CreateView):
    """
    View to create a new workflow step
    """
    model = WorkflowStep
    form_class = WorkflowStepForm
    template_name = 'incidents/workflow_step_form.html'

    def dispatch(self, request, *args, **kwargs):
        # Get the workflow template
        self.workflow = get_object_or_404(WorkflowTemplate, pk=self.kwargs['workflow_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['workflow'] = self.workflow
        return kwargs

    def form_valid(self, form):
        form.instance.workflow = self.workflow
        messages.success(self.request, 'Workflow step created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating workflow step. Please check the form.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workflow'] = self.workflow
        return context

    def get_success_url(self):
        return reverse_lazy('workflow_template_detail', kwargs={'pk': self.workflow.pk})


class WorkflowStepUpdateView(CanManageRolesMixin, UpdateView):
    """
    View to update an existing workflow step
    """
    model = WorkflowStep
    form_class = WorkflowStepForm
    template_name = 'incidents/workflow_step_form.html'
    context_object_name = 'step'
    pk_url_kwarg = 'step_pk'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['workflow'] = self.object.workflow
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Workflow step updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating workflow step. Please check the form.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workflow'] = self.object.workflow
        return context

    def get_success_url(self):
        return reverse_lazy('workflow_template_detail', kwargs={'pk': self.object.workflow.pk})


class WorkflowStepDeleteView(CanManageRolesMixin, DeleteView):
    """
    View to delete a workflow step
    """
    model = WorkflowStep
    template_name = 'incidents/workflow_step_confirm_delete.html'
    context_object_name = 'step'
    pk_url_kwarg = 'step_pk'

    def get_success_url(self):
        return reverse_lazy('workflow_template_detail', kwargs={'pk': self.object.workflow.pk})

    def delete(self, request, *args, **kwargs):
        step = self.get_object()
        workflow = step.workflow
        
        messages.success(request, f'Workflow step "{step.name}" deleted successfully.')
        
        # Delete the step
        result = super().delete(request, *args, **kwargs)
        
        # Reorder remaining steps
        with transaction.atomic():
            for i, s in enumerate(WorkflowStep.objects.filter(workflow=workflow).order_by('order')):
                s.order = i
                s.save()
        
        return result


# Reporting Views
class IncidentReportView(CanViewIncidentsMixin, TemplateView):
    """
    View for generating incident reports
    """
    template_name = 'incidents/incident_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        status_id = self.request.GET.get('status')
        priority_id = self.request.GET.get('priority')
        category_id = self.request.GET.get('category')
        assigned_id = self.request.GET.get('assigned')
        
        # Base queryset
        queryset = Incident.objects.all()
        
        # Apply filters
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(reported_at__date__gte=start_date)
                context['start_date'] = start_date.strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(reported_at__date__lte=end_date)
                context['end_date'] = end_date.strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        if status_id and status_id.isdigit():
            queryset = queryset.filter(status_id=status_id)
            context['selected_status'] = int(status_id)
        elif status_id == 'open':
            queryset = queryset.filter(status__is_closed=False)
            context['selected_status'] = 'open'
        elif status_id == 'closed':
            queryset = queryset.filter(status__is_closed=True)
            context['selected_status'] = 'closed'
        
        if priority_id and priority_id.isdigit():
            queryset = queryset.filter(priority_id=priority_id)
            context['selected_priority'] = int(priority_id)
        
        if category_id and category_id.isdigit():
            queryset = queryset.filter(category_id=category_id)
            context['selected_category'] = int(category_id)
        
        if assigned_id and assigned_id.isdigit():
            queryset = queryset.filter(assigned_to_id=assigned_id)
            context['selected_assigned'] = int(assigned_id)
        elif assigned_id == 'unassigned':
            queryset = queryset.filter(assigned_to__isnull=True)
            context['selected_assigned'] = 'unassigned'
        
        # Get incidents based on filters
        incidents = queryset.select_related(
            'status', 'priority', 'category', 'reported_by', 'assigned_to'
        ).order_by('-reported_at')
        
        # Generate report statistics
        stats = {
            'total_incidents': incidents.count(),
            'open_incidents': incidents.filter(status__is_closed=False).count(),
            'closed_incidents': incidents.filter(status__is_closed=True).count(),
            'avg_resolution_time': None,
        }
        
        # Calculate average resolution time for closed incidents
        closed_incidents = incidents.filter(
            status__is_closed=True,
            resolved_at__isnull=False
        )
        if closed_incidents.exists():
            total_seconds = 0
            count = 0
            
            for incident in closed_incidents:
                if incident.resolved_at and incident.reported_at:
                    delta = incident.resolved_at - incident.reported_at
                    total_seconds += delta.total_seconds()
                    count += 1
            
            if count > 0:
                avg_seconds = total_seconds / count
                avg_hours = avg_seconds / 3600
                stats['avg_resolution_time'] = round(avg_hours, 1)
        
        # Status breakdown
        status_breakdown = {}
        for status in IncidentStatus.objects.all():
            count = incidents.filter(status=status).count()
            if count > 0:
                status_breakdown[status.name] = {
                    'count': count,
                    'percentage': round((count / stats['total_incidents']) * 100 if stats['total_incidents'] > 0 else 0, 1),
                    'color': status.color
                }
        
        # Priority breakdown
        priority_breakdown = {}
        for priority in IncidentPriority.objects.all():
            count = incidents.filter(priority=priority).count()
            if count > 0:
                priority_breakdown[priority.name] = {
                    'count': count,
                    'percentage': round((count / stats['total_incidents']) * 100 if stats['total_incidents'] > 0 else 0, 1),
                    'color': priority.color
                }
        
        # Category breakdown
        category_counts = incidents.values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Add report data to context
        context.update({
            'incidents': incidents[:100],  # Limit to 100 for performance
            'stats': stats,
            'status_breakdown': status_breakdown,
            'priority_breakdown': priority_breakdown,
            'category_counts': category_counts,
            'total_shown': min(100, incidents.count()),
            'has_more': incidents.count() > 100,
        })
        
        # Add filter options to context
        context['statuses'] = IncidentStatus.objects.all().order_by('order', 'name')
        context['priorities'] = IncidentPriority.objects.all().order_by('-level')
        context['categories'] = IncidentCategory.objects.all().order_by('name')
        context['assignees'] = User.objects.filter(
            assigned_incidents__isnull=False
        ).distinct().order_by('username')
        
        # Check if export is requested
        export_format = self.request.GET.get('export')
        if export_format == 'csv':
            return self.export_csv(incidents)
        
        return context
    
    def export_csv(self, incidents):
        """
        Export incidents to CSV
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="incident_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Title', 'Status', 'Priority', 'Category',
            'Reported By', 'Reported At', 'Assigned To',
            'Due Date', 'Resolved At', 'Closed At',
            'Resolution Time (hours)'
        ])
        
        for incident in incidents:
            # Calculate resolution time in hours
            resolution_time = ''
            if incident.resolved_at and incident.reported_at:
                delta = incident.resolved_at - incident.reported_at
                resolution_time = round(delta.total_seconds() / 3600, 1)
            
            writer.writerow([
                incident.id,
                incident.title,
                incident.status.name if incident.status else '',
                incident.priority.name if incident.priority else '',
                incident.category.name if incident.category else '',
                incident.reported_by.username if incident.reported_by else '',
                incident.reported_at.strftime('%Y-%m-%d %H:%M') if incident.reported_at else '',
                incident.assigned_to.username if incident.assigned_to else '',
                incident.due_date.strftime('%Y-%m-%d %H:%M') if incident.due_date else '',
                incident.resolved_at.strftime('%Y-%m-%d %H:%M') if incident.resolved_at else '',
                incident.closed_at.strftime('%Y-%m-%d %H:%M') if incident.closed_at else '',
                resolution_time
            ])
        
        return response


# API Views for AJAX requests
def incident_status_api(request):
    """
    API endpoint to get incident statuses
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    statuses = IncidentStatus.objects.all().values(
        'id', 'name', 'is_closed', 'color', 'order'
    ).order_by('order', 'name')
    
    return JsonResponse({'results': list(statuses)})


def incident_priority_api(request):
    """
    API endpoint to get incident priorities
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    priorities = IncidentPriority.objects.all().values(
        'id', 'name', 'level', 'color'
    ).order_by('-level')
    
    return JsonResponse({'results': list(priorities)})


def incident_category_api(request):
    """
    API endpoint to get incident categories
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    categories = IncidentCategory.objects.all().values(
        'id', 'name', 'parent_id'
    ).order_by('name')
    
    return JsonResponse({'results': list(categories)})


def user_role_api(request):
    """
    API endpoint to get user roles
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # Only staff or users with role management permission can access this
    if not request.user.is_staff and not UserRole.objects.filter(
        user=request.user,
        is_active=True,
        role__can_manage_roles=True
    ).exists():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    user_id = request.GET.get('user_id')
    if not user_id or not user_id.isdigit():
        return JsonResponse({'error': 'Invalid user ID'}, status=400)
    
    user_roles = UserRole.objects.filter(
        user_id=user_id,
        is_active=True
    ).select_related('role').values(
        'id', 'role__id', 'role__name'
    )
    
    return JsonResponse({'results': list(user_roles)})
