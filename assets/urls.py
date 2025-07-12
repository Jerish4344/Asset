from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.AssetDashboardView.as_view(), name='asset_dashboard'),
    
    # Asset Categories
    path('categories/', views.AssetCategoryListView.as_view(), name='asset_category_list'),
    path('categories/create/', views.AssetCategoryCreateView.as_view(), name='asset_category_create'),
    path('categories/<int:pk>/', views.AssetCategoryDetailView.as_view(), name='asset_category_detail'),
    path('categories/<int:pk>/update/', views.AssetCategoryUpdateView.as_view(), name='asset_category_update'),
    path('categories/<int:pk>/delete/', views.AssetCategoryDeleteView.as_view(), name='asset_category_delete'),
    
    # Asset Features
    path('features/', views.AssetFeatureListView.as_view(), name='asset_feature_list'),
    path('features/create/', views.AssetFeatureCreateView.as_view(), name='asset_feature_create'),
    path('features/<int:pk>/', views.AssetFeatureDetailView.as_view(), name='asset_feature_detail'),
    path('features/<int:pk>/update/', views.AssetFeatureUpdateView.as_view(), name='asset_feature_update'),
    path('features/<int:pk>/delete/', views.AssetFeatureDeleteView.as_view(), name='asset_feature_delete'),
    
    # Asset Locations
    path('locations/', views.AssetLocationListView.as_view(), name='asset_location_list'),
    path('locations/create/', views.AssetLocationCreateView.as_view(), name='asset_location_create'),
    path('locations/<int:pk>/', views.AssetLocationDetailView.as_view(), name='asset_location_detail'),
    path('locations/<int:pk>/update/', views.AssetLocationUpdateView.as_view(), name='asset_location_update'),
    path('locations/<int:pk>/delete/', views.AssetLocationDeleteView.as_view(), name='asset_location_delete'),
    
    # Assets
    path('assets/', views.AssetListView.as_view(), name='asset_list'),
    path('assets/create/', views.AssetCreateView.as_view(), name='asset_create'),
    path('assets/<int:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
    path('assets/<int:pk>/update/', views.AssetUpdateView.as_view(), name='asset_update'),
    path('assets/<int:pk>/delete/', views.AssetDeleteView.as_view(), name='asset_delete'),
    
    # Asset Network Addresses
    path('network-addresses/', views.AssetNetworkAddressListView.as_view(), name='asset_network_address_list'),
    path('network-addresses/create/', views.AssetNetworkAddressCreateView.as_view(), name='asset_network_address_create'),
    path('network-addresses/<int:pk>/update/', views.AssetNetworkAddressUpdateView.as_view(), name='asset_network_address_update'),
    path('network-addresses/<int:pk>/delete/', views.AssetNetworkAddressDeleteView.as_view(), name='asset_network_address_delete'),
    
    # Excel Import
    path('import/', views.ExcelImportView.as_view(), name='asset_excel_import'),
    
    # API Endpoints
    path('api/asset-search/', views.asset_search_api, name='api_asset_search'),
    path('api/asset-categories/', views.asset_category_api, name='api_asset_categories'),
]
