from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.IncidentDashboardView.as_view(), name='incident_dashboard'),
    
    # Role Management
    path('roles/', views.RoleListView.as_view(), name='role_list'),
    path('roles/create/', views.RoleCreateView.as_view(), name='role_create'),
    path('roles/<int:pk>/', views.RoleDetailView.as_view(), name='role_detail'),
    path('roles/<int:pk>/update/', views.RoleUpdateView.as_view(), name='role_update'),
    path('roles/<int:pk>/delete/', views.RoleDeleteView.as_view(), name='role_delete'),
    
    # User Role Management
    path('user-roles/', views.UserRoleListView.as_view(), name='user_role_list'),
    path('user-roles/create/', views.UserRoleCreateView.as_view(), name='user_role_create'),
    path('user-roles/<int:pk>/update/', views.UserRoleUpdateView.as_view(), name='user_role_update'),
    path('user-roles/<int:pk>/delete/', views.UserRoleDeleteView.as_view(), name='user_role_delete'),
    
    # Incident Status Management
    path('statuses/', views.IncidentStatusListView.as_view(), name='incident_status_list'),
    path('statuses/create/', views.IncidentStatusCreateView.as_view(), name='incident_status_create'),
    path('statuses/<int:pk>/update/', views.IncidentStatusUpdateView.as_view(), name='incident_status_update'),
    path('statuses/<int:pk>/delete/', views.IncidentStatusDeleteView.as_view(), name='incident_status_delete'),
    
    # Incident Priority Management
    path('priorities/', views.IncidentPriorityListView.as_view(), name='incident_priority_list'),
    path('priorities/create/', views.IncidentPriorityCreateView.as_view(), name='incident_priority_create'),
    path('priorities/<int:pk>/update/', views.IncidentPriorityUpdateView.as_view(), name='incident_priority_update'),
    path('priorities/<int:pk>/delete/', views.IncidentPriorityDeleteView.as_view(), name='incident_priority_delete'),
    
    # Incident Category Management
    path('categories/', views.IncidentCategoryListView.as_view(), name='incident_category_list'),
    path('categories/create/', views.IncidentCategoryCreateView.as_view(), name='incident_category_create'),
    path('categories/<int:pk>/', views.IncidentCategoryDetailView.as_view(), name='incident_category_detail'),
    path('categories/<int:pk>/update/', views.IncidentCategoryUpdateView.as_view(), name='incident_category_update'),
    path('categories/<int:pk>/delete/', views.IncidentCategoryDeleteView.as_view(), name='incident_category_delete'),
    
    # Incident Management
    path('incidents/', views.IncidentListView.as_view(), name='incident_list'),
    path('incidents/create/', views.IncidentCreateView.as_view(), name='incident_create'),
    path('incidents/<int:pk>/', views.IncidentDetailView.as_view(), name='incident_detail'),
    path('incidents/<int:pk>/update/', views.IncidentUpdateView.as_view(), name='incident_update'),
    path('incidents/<int:pk>/delete/', views.IncidentDeleteView.as_view(), name='incident_delete'),
    
    # Incident Comments
    path('incidents/<int:pk>/comments/add/', views.AddIncidentCommentView.as_view(), name='incident_add_comment'),
    path('incidents/<int:pk>/comments/<int:comment_pk>/delete/', views.DeleteIncidentCommentView.as_view(), name='incident_delete_comment'),
    
    # Workflow Management
    path('workflows/', views.WorkflowTemplateListView.as_view(), name='workflow_template_list'),
    path('workflows/create/', views.WorkflowTemplateCreateView.as_view(), name='workflow_template_create'),
    path('workflows/<int:pk>/', views.WorkflowTemplateDetailView.as_view(), name='workflow_template_detail'),
    path('workflows/<int:pk>/update/', views.WorkflowTemplateUpdateView.as_view(), name='workflow_template_update'),
    path('workflows/<int:pk>/delete/', views.WorkflowTemplateDeleteView.as_view(), name='workflow_template_delete'),
    
    # Workflow Steps
    path('workflows/<int:workflow_pk>/steps/create/', views.WorkflowStepCreateView.as_view(), name='workflow_step_create'),
    path('workflows/<int:workflow_pk>/steps/<int:step_pk>/update/', views.WorkflowStepUpdateView.as_view(), name='workflow_step_update'),
    path('workflows/<int:workflow_pk>/steps/<int:step_pk>/delete/', views.WorkflowStepDeleteView.as_view(), name='workflow_step_delete'),
    
    # Reporting
    path('reports/', views.IncidentReportView.as_view(), name='incident_report'),
    
    # API Endpoints
    path('api/statuses/', views.incident_status_api, name='api_incident_statuses'),
    path('api/priorities/', views.incident_priority_api, name='api_incident_priorities'),
    path('api/categories/', views.incident_category_api, name='api_incident_categories'),
    path('api/user-roles/', views.user_role_api, name='api_user_roles'),
]
