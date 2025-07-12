"""
Admin configuration for the *incidents* app.

Provides a more user-friendly Django-admin interface by exposing the most
important incident-management models with sensible list displays, filters and
search capabilities.
"""

from django.contrib import admin

from .models import (
    Role,
    UserRole,
    IncidentStatus,
    IncidentPriority,
    IncidentCategory,
    Incident,
    IncidentComment,
    IncidentHistory,
    WorkflowTemplate,
    WorkflowStep,
)

# ---------------------------------------------------------------------------
# Inline definitions
# ---------------------------------------------------------------------------


class IncidentCommentInline(admin.TabularInline):
    model = IncidentComment
    extra = 0
    fields = ("user", "comment", "is_private", "created_at")
    readonly_fields = ("created_at",)
    show_change_link = True


class IncidentHistoryInline(admin.TabularInline):
    model = IncidentHistory
    extra = 0
    fields = ("user", "field_name", "old_value", "new_value", "change_type", "changed_at")
    readonly_fields = ("user", "field_name", "old_value", "new_value", "change_type", "changed_at")
    can_delete = False


class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 0
    fields = ("order", "name", "status", "estimated_time", "is_mandatory")
    readonly_fields = ("order",)


# ---------------------------------------------------------------------------
# Model admin customisations
# ---------------------------------------------------------------------------


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "can_view_incidents",
        "can_create_incidents",
        "can_update_incidents",
        "can_assign_incidents",
        "can_close_incidents",
        "can_manage_roles",
    )
    search_fields = ("name", "description")
    list_filter = (
        "can_view_incidents",
        "can_create_incidents",
        "can_update_incidents",
        "can_assign_incidents",
        "can_close_incidents",
        "can_manage_roles",
    )
    ordering = ("name",)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "is_active", "assigned_at")
    search_fields = ("user__username", "role__name")
    list_filter = ("is_active", "role__name")
    raw_id_fields = ("user", "role")
    ordering = ("user__username", "role__name")


@admin.register(IncidentStatus)
class IncidentStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "is_default", "is_closed", "order")
    search_fields = ("name", "description")
    list_filter = ("is_default", "is_closed")
    ordering = ("order", "name")


@admin.register(IncidentPriority)
class IncidentPriorityAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "response_time", "resolution_time")
    search_fields = ("name", "description")
    list_filter = ("level",)
    ordering = ("-level", "name")


@admin.register(IncidentCategory)
class IncidentCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    search_fields = ("name", "description")
    list_filter = ("parent",)
    raw_id_fields = ("parent",)
    ordering = ("name",)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "priority", "asset", "reported_by", "assigned_to", "reported_at", "due_date")
    list_filter = ("status", "priority", "category", "reported_by", "assigned_to")
    search_fields = ("title", "description", "resolution", "asset__asset_name")
    date_hierarchy = "reported_at"
    raw_id_fields = ("asset", "reported_by", "assigned_to", "category")
    inlines = [IncidentCommentInline, IncidentHistoryInline]
    ordering = ("-reported_at",)


@admin.register(IncidentComment)
class IncidentCommentAdmin(admin.ModelAdmin):
    list_display = ("incident", "user", "is_private", "created_at")
    list_filter = ("is_private",)
    search_fields = ("incident__title", "user__username", "comment")
    raw_id_fields = ("incident", "user")
    ordering = ("-created_at",)


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ("name", "description")
    raw_id_fields = ("category",)
    inlines = [WorkflowStepInline]
    ordering = ("name",)

# ---------------------------------------------------------------------------
# Unregistered models kept out of admin to reduce noise
# (IncidentHistory is visible via inline only)
# ---------------------------------------------------------------------------

