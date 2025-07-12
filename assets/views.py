from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.base import TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q
from django.utils import timezone

import pandas as pd
import io
import logging

from .models import Asset, AssetCategory, AssetFeature, AssetLocation, AssetNetworkAddress
from .forms import (
    AssetForm, AssetCategoryForm, AssetFeatureForm, AssetLocationForm, 
    AssetNetworkAddressForm, ExcelImportForm
)

# Configure logger
logger = logging.getLogger(__name__)


# Dashboard View
class AssetDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard view showing asset statistics and summary information
    """
    template_name = 'assets/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get counts of assets by category
        category_counts = AssetCategory.objects.filter(
            is_active=1
        ).annotate(
            asset_count=Count('assets', filter=Q(assets__is_active=1))
        ).values('category_name', 'asset_count').order_by('-asset_count')
        
        # Get counts of assets by type
        type_counts = Asset.objects.filter(
            is_active=1
        ).values('asset_type').annotate(
            count=Count('asset_id')
        ).order_by('-count')
        
        # Get recent assets
        recent_assets = Asset.objects.filter(
            is_active=1
        ).order_by('-valid_from')[:10]
        
        # Get assets with no features
        assets_no_features = Asset.objects.filter(
            is_active=1, 
            feature__isnull=True
        ).count()
        
        # Get assets with no location
        assets_no_location = Asset.objects.filter(
            is_active=1, 
            location__isnull=True
        ).count()
        
        # Get total asset count
        total_assets = Asset.objects.filter(is_active=1).count()
        
        context.update({
            'total_assets': total_assets,
            'category_counts': category_counts,
            'type_counts': type_counts,
            'recent_assets': recent_assets,
            'assets_no_features': assets_no_features,
            'assets_no_location': assets_no_location,
        })
        
        return context


# Asset Category Views
class AssetCategoryListView(LoginRequiredMixin, ListView):
    """
    View to list all asset categories
    """
    model = AssetCategory
    template_name = 'assets/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active status if specified
        active_filter = self.request.GET.get('active')
        if active_filter == '1':
            queryset = queryset.filter(is_active=1)
        elif active_filter == '0':
            queryset = queryset.filter(is_active=0)
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(category_name__icontains=search_term) | 
                Q(category_type__icontains=search_term)
            )
        
        return queryset.order_by('-is_active', 'category_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        context['active_filter'] = self.request.GET.get('active', '')
        return context


class AssetCategoryDetailView(LoginRequiredMixin, DetailView):
    """
    View to show details of a specific asset category
    """
    model = AssetCategory
    template_name = 'assets/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get assets in this category
        context['assets'] = Asset.objects.filter(
            category=self.object,
            is_active=1
        ).order_by('asset_name')
        return context


class AssetCategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View to create a new asset category
    """
    model = AssetCategory
    form_class = AssetCategoryForm
    template_name = 'assets/category_form.html'
    success_url = reverse_lazy('asset_category_list')

    def test_func(self):
        # Only staff users can create categories
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Asset category created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating asset category. Please check the form.')
        return super().form_invalid(form)


class AssetCategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View to update an existing asset category
    """
    model = AssetCategory
    form_class = AssetCategoryForm
    template_name = 'assets/category_form.html'
    context_object_name = 'category'

    def test_func(self):
        # Only staff users can update categories
        return self.request.user.is_staff

    def get_success_url(self):
        return reverse_lazy('asset_category_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Asset category updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating asset category. Please check the form.')
        return super().form_invalid(form)


class AssetCategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View to delete an asset category
    """
    model = AssetCategory
    template_name = 'assets/category_confirm_delete.html'
    success_url = reverse_lazy('asset_category_list')
    context_object_name = 'category'

    def test_func(self):
        # Only staff users can delete categories
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        
        # Check if there are assets using this category
        if Asset.objects.filter(category=category).exists():
            messages.error(request, 'Cannot delete category. There are assets assigned to it.')
            return redirect('asset_category_detail', pk=category.pk)
        
        messages.success(request, f'Asset category "{category.category_name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Asset Feature Views
class AssetFeatureListView(LoginRequiredMixin, ListView):
    """
    View to list all asset features
    """
    model = AssetFeature
    template_name = 'assets/feature_list.html'
    context_object_name = 'features'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active status if specified
        active_filter = self.request.GET.get('active')
        if active_filter == '1':
            queryset = queryset.filter(is_active=1)
        elif active_filter == '0':
            queryset = queryset.filter(is_active=0)
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(feature_name__icontains=search_term) | 
                Q(feature_type__icontains=search_term) |
                Q(feature_desc__icontains=search_term)
            )
        
        # Filter by feature type if provided
        feature_type = self.request.GET.get('type', '')
        if feature_type:
            queryset = queryset.filter(feature_type=feature_type)
        
        return queryset.order_by('-is_active', 'feature_type', 'feature_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        context['active_filter'] = self.request.GET.get('active', '')
        context['feature_type'] = self.request.GET.get('type', '')
        
        # Get unique feature types for filtering
        context['feature_types'] = AssetFeature.objects.values_list(
            'feature_type', flat=True
        ).distinct().order_by('feature_type')
        
        return context


class AssetFeatureDetailView(LoginRequiredMixin, DetailView):
    """
    View to show details of a specific asset feature
    """
    model = AssetFeature
    template_name = 'assets/feature_detail.html'
    context_object_name = 'feature'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get assets with this feature
        context['assets'] = Asset.objects.filter(
            feature=self.object,
            is_active=1
        ).order_by('asset_name')
        return context


class AssetFeatureCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View to create a new asset feature
    """
    model = AssetFeature
    form_class = AssetFeatureForm
    template_name = 'assets/feature_form.html'
    success_url = reverse_lazy('asset_feature_list')

    def test_func(self):
        # Only staff users can create features
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Asset feature created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating asset feature. Please check the form.')
        return super().form_invalid(form)


class AssetFeatureUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View to update an existing asset feature
    """
    model = AssetFeature
    form_class = AssetFeatureForm
    template_name = 'assets/feature_form.html'
    context_object_name = 'feature'

    def test_func(self):
        # Only staff users can update features
        return self.request.user.is_staff

    def get_success_url(self):
        return reverse_lazy('asset_feature_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Asset feature updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating asset feature. Please check the form.')
        return super().form_invalid(form)


class AssetFeatureDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View to delete an asset feature
    """
    model = AssetFeature
    template_name = 'assets/feature_confirm_delete.html'
    success_url = reverse_lazy('asset_feature_list')
    context_object_name = 'feature'

    def test_func(self):
        # Only staff users can delete features
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        feature = self.get_object()
        
        # Check if there are assets using this feature
        if Asset.objects.filter(feature=feature).exists():
            messages.error(request, 'Cannot delete feature. There are assets assigned to it.')
            return redirect('asset_feature_detail', pk=feature.pk)
        
        messages.success(request, f'Asset feature "{feature.feature_name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Asset Location Views
class AssetLocationListView(LoginRequiredMixin, ListView):
    """
    View to list all asset locations
    """
    model = AssetLocation
    template_name = 'assets/location_list.html'
    context_object_name = 'locations'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active status if specified
        active_filter = self.request.GET.get('active')
        if active_filter == '1':
            queryset = queryset.filter(is_active=1)
        elif active_filter == '0':
            queryset = queryset.filter(is_active=0)
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(address_value__icontains=search_term) | 
                Q(city__icontains=search_term) |
                Q(state__icontains=search_term) |
                Q(country__icontains=search_term)
            )
        
        # Filter by address type if provided
        address_type = self.request.GET.get('type', '')
        if address_type:
            queryset = queryset.filter(address_type=address_type)
        
        return queryset.order_by('-is_active', 'address_type', 'address_value')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        context['active_filter'] = self.request.GET.get('active', '')
        context['address_type'] = self.request.GET.get('type', '')
        
        # Get unique address types for filtering
        context['address_types'] = AssetLocation.objects.values_list(
            'address_type', flat=True
        ).distinct().order_by('address_type')
        
        return context


class AssetLocationDetailView(LoginRequiredMixin, DetailView):
    """
    View to show details of a specific asset location
    """
    model = AssetLocation
    template_name = 'assets/location_detail.html'
    context_object_name = 'location'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get assets at this location
        context['assets'] = Asset.objects.filter(
            location=self.object,
            is_active=1
        ).order_by('asset_name')
        return context


class AssetLocationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View to create a new asset location
    """
    model = AssetLocation
    form_class = AssetLocationForm
    template_name = 'assets/location_form.html'
    success_url = reverse_lazy('asset_location_list')

    def test_func(self):
        # Only staff users can create locations
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Asset location created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating asset location. Please check the form.')
        return super().form_invalid(form)


class AssetLocationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View to update an existing asset location
    """
    model = AssetLocation
    form_class = AssetLocationForm
    template_name = 'assets/location_form.html'
    context_object_name = 'location'

    def test_func(self):
        # Only staff users can update locations
        return self.request.user.is_staff

    def get_success_url(self):
        return reverse_lazy('asset_location_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Asset location updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating asset location. Please check the form.')
        return super().form_invalid(form)


class AssetLocationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View to delete an asset location
    """
    model = AssetLocation
    template_name = 'assets/location_confirm_delete.html'
    success_url = reverse_lazy('asset_location_list')
    context_object_name = 'location'

    def test_func(self):
        # Only staff users can delete locations
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        location = self.get_object()
        
        # Check if there are assets using this location
        if Asset.objects.filter(location=location).exists():
            messages.error(request, 'Cannot delete location. There are assets assigned to it.')
            return redirect('asset_location_detail', pk=location.pk)
        
        messages.success(request, f'Asset location deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Asset Views
class AssetListView(LoginRequiredMixin, ListView):
    """
    View to list all assets
    """
    model = Asset
    template_name = 'assets/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active status if specified
        active_filter = self.request.GET.get('active')
        if active_filter == '1':
            queryset = queryset.filter(is_active=1)
        elif active_filter == '0':
            queryset = queryset.filter(is_active=0)
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(asset_name__icontains=search_term) | 
                Q(asset_make__icontains=search_term) |
                Q(asset_type__icontains=search_term) |
                Q(asset_purpose__icontains=search_term)
            )
        
        # Filter by category if provided
        category_id = self.request.GET.get('category', '')
        if category_id and category_id.isdigit():
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by asset type if provided
        asset_type = self.request.GET.get('type', '')
        if asset_type:
            queryset = queryset.filter(asset_type=asset_type)
        
        return queryset.select_related('category', 'feature', 'location').order_by('-is_active', 'asset_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        context['active_filter'] = self.request.GET.get('active', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['type_filter'] = self.request.GET.get('type', '')
        
        # Get categories for filtering
        context['categories'] = AssetCategory.objects.filter(is_active=1).order_by('category_name')
        
        # Get unique asset types for filtering
        context['asset_types'] = Asset.objects.values_list(
            'asset_type', flat=True
        ).distinct().order_by('asset_type')
        
        return context


class AssetDetailView(LoginRequiredMixin, DetailView):
    """
    View to show details of a specific asset
    """
    model = Asset
    template_name = 'assets/asset_detail.html'
    context_object_name = 'asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get network addresses for this asset
        context['network_addresses'] = AssetNetworkAddress.objects.filter(
            asset=self.object,
            is_active=1
        ).order_by('address_type')
        
        # Get child assets
        context['child_assets'] = Asset.objects.filter(
            parent_asset=self.object,
            is_active=1
        ).order_by('asset_name')
        
        # Get incidents related to this asset (if incidents app is installed)
        if 'incidents' in self.request.META.get('INSTALLED_APPS', []):
            from incidents.models import Incident
            context['incidents'] = Incident.objects.filter(
                asset=self.object
            ).order_by('-reported_at')
        
        return context


class AssetCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View to create a new asset
    """
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('asset_list')

    def test_func(self):
        # Only staff users can create assets
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Asset created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating asset. Please check the form.')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('asset_detail', kwargs={'pk': self.object.pk})


class AssetUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View to update an existing asset
    """
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    context_object_name = 'asset'

    def test_func(self):
        # Only staff users can update assets
        return self.request.user.is_staff

    def get_success_url(self):
        return reverse_lazy('asset_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Asset updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating asset. Please check the form.')
        return super().form_invalid(form)


class AssetDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View to delete an asset
    """
    model = Asset
    template_name = 'assets/asset_confirm_delete.html'
    success_url = reverse_lazy('asset_list')
    context_object_name = 'asset'

    def test_func(self):
        # Only staff users can delete assets
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        asset = self.get_object()
        
        # Check if there are child assets
        if Asset.objects.filter(parent_asset=asset).exists():
            messages.error(request, 'Cannot delete asset. There are child assets assigned to it.')
            return redirect('asset_detail', pk=asset.pk)
        
        # Check if there are incidents related to this asset (if incidents app is installed)
        if 'incidents' in request.META.get('INSTALLED_APPS', []):
            from incidents.models import Incident
            if Incident.objects.filter(asset=asset).exists():
                messages.error(request, 'Cannot delete asset. There are incidents related to it.')
                return redirect('asset_detail', pk=asset.pk)
        
        messages.success(request, f'Asset "{asset.asset_name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Asset Network Address Views
class AssetNetworkAddressListView(LoginRequiredMixin, ListView):
    """
    View to list all network addresses
    """
    model = AssetNetworkAddress
    template_name = 'assets/network_address_list.html'
    context_object_name = 'addresses'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active status if specified
        active_filter = self.request.GET.get('active')
        if active_filter == '1':
            queryset = queryset.filter(is_active=1)
        elif active_filter == '0':
            queryset = queryset.filter(is_active=0)
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(address_value__icontains=search_term) | 
                Q(asset__asset_name__icontains=search_term)
            )
        
        # Filter by address type if provided
        address_type = self.request.GET.get('type', '')
        if address_type:
            queryset = queryset.filter(address_type=address_type)
        
        # Filter by asset if provided
        asset_id = self.request.GET.get('asset', '')
        if asset_id and asset_id.isdigit():
            queryset = queryset.filter(asset_id=asset_id)
        
        return queryset.select_related('asset').order_by('-is_active', 'address_type', 'address_value')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        context['active_filter'] = self.request.GET.get('active', '')
        context['type_filter'] = self.request.GET.get('type', '')
        context['asset_filter'] = self.request.GET.get('asset', '')
        
        # Get address types for filtering
        context['address_types'] = [
            ('IP_ADDRESS', 'IP Address'),
            ('MAC_ID', 'MAC ID')
        ]
        
        return context


class AssetNetworkAddressCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View to create a new network address
    """
    model = AssetNetworkAddress
    form_class = AssetNetworkAddressForm
    template_name = 'assets/network_address_form.html'

    def test_func(self):
        # Only staff users can create network addresses
        return self.request.user.is_staff

    def get_initial(self):
        initial = super().get_initial()
        # Pre-select asset if provided in URL
        asset_id = self.request.GET.get('asset', '')
        if asset_id and asset_id.isdigit():
            initial['asset'] = asset_id
        return initial

    def get_success_url(self):
        # Redirect back to the asset detail page if we came from there
        asset_id = self.request.GET.get('asset', '')
        if asset_id and asset_id.isdigit():
            return reverse_lazy('asset_detail', kwargs={'pk': asset_id})
        return reverse_lazy('asset_network_address_list')

    def form_valid(self, form):
        messages.success(self.request, 'Network address created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating network address. Please check the form.')
        return super().form_invalid(form)


class AssetNetworkAddressUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View to update an existing network address
    """
    model = AssetNetworkAddress
    form_class = AssetNetworkAddressForm
    template_name = 'assets/network_address_form.html'
    context_object_name = 'address'

    def test_func(self):
        # Only staff users can update network addresses
        return self.request.user.is_staff

    def get_success_url(self):
        # Redirect back to the asset detail page
        return reverse_lazy('asset_detail', kwargs={'pk': self.object.asset.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Network address updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating network address. Please check the form.')
        return super().form_invalid(form)


class AssetNetworkAddressDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View to delete a network address
    """
    model = AssetNetworkAddress
    template_name = 'assets/network_address_confirm_delete.html'
    context_object_name = 'address'

    def test_func(self):
        # Only staff users can delete network addresses
        return self.request.user.is_staff

    def get_success_url(self):
        # Redirect back to the asset detail page
        return reverse_lazy('asset_detail', kwargs={'pk': self.object.asset.pk})

    def delete(self, request, *args, **kwargs):
        address = self.get_object()
        messages.success(request, f'Network address "{address.address_value}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Excel Import View
class ExcelImportView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    View to import asset data from Excel files
    """
    template_name = 'assets/excel_import.html'

    def test_func(self):
        # Only staff users can import data
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ExcelImportForm()
        return context

    def post(self, request, *args, **kwargs):
        form = ExcelImportForm(request.POST, request.FILES)
        
        if not form.is_valid():
            messages.error(request, 'Error with the form submission. Please check the form.')
            return render(request, self.template_name, {'form': form})
        
        excel_file = request.FILES['excel_file']
        sheet_name = form.cleaned_data.get('sheet_name') or 0  # Use first sheet if not specified
        category = form.cleaned_data.get('category')
        
        try:
            # Read the Excel file
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Process the data
            result = self.process_excel_data(df, category)
            
            if result['success']:
                messages.success(request, f"Import successful! {result['created']} assets created, {result['updated']} assets updated.")
            else:
                messages.error(request, f"Import failed: {result['error']}")
                
            return render(request, self.template_name, {'form': form, 'result': result})
            
        except Exception as e:
            logger.error(f"Excel import error: {str(e)}")
            messages.error(request, f"Error processing Excel file: {str(e)}")
            return render(request, self.template_name, {'form': form})

    @transaction.atomic
    def process_excel_data(self, df, category):
        """
        Process the Excel data and create/update assets
        
        Args:
            df: Pandas DataFrame containing the asset data
            category: AssetCategory instance for the imported assets
            
        Returns:
            dict: Result of the import operation
        """
        result = {
            'success': False,
            'created': 0,
            'updated': 0,
            'errors': [],
            'error': None
        }
        
        try:
            # Normalize column names (convert to lowercase and replace spaces with underscores)
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            # Map expected columns to their possible names in the Excel file
            column_mappings = {
                'computer_name': ['computer_name', 'name', 'asset_name', 'hostname'],
                'server_make': ['server_make', 'make', 'asset_make', 'manufacturer'],
                'type': ['type', 'asset_type', 'server_type'],
                'ram': ['ram', 'memory'],
                'processor': ['processor', 'cpu'],
                'harddisk': ['harddisk', 'hdd', 'storage', 'disk'],
                'ip_address': ['ip_address', 'ip', 'ipaddress', 'ip_addr'],
                'mac_id': ['mac_id', 'mac', 'macid', 'mac_address']
            }
            
            # Find actual column names in the DataFrame
            actual_columns = {}
            for key, possible_names in column_mappings.items():
                for name in possible_names:
                    if name in df.columns:
                        actual_columns[key] = name
                        break
            
            # Check if required columns are present
            required_columns = ['computer_name']
            missing_columns = [col for col in required_columns if col not in actual_columns]
            if missing_columns:
                result['error'] = f"Missing required columns: {', '.join(missing_columns)}"
                return result
            
            # Process each row in the DataFrame
            for _, row in df.iterrows():
                try:
                    # Get asset name (required)
                    asset_name = row[actual_columns.get('computer_name')]
                    if pd.isna(asset_name) or not asset_name:
                        continue  # Skip rows with no asset name
                    
                    # Check if asset already exists
                    asset = Asset.objects.filter(asset_name=asset_name).first()
                    
                    if asset:
                        # Update existing asset
                        is_updated = False
                        
                        # Update category if different
                        if asset.category != category:
                            asset.category = category
                            is_updated = True
                        
                        # Update asset make if provided
                        if 'server_make' in actual_columns and not pd.isna(row[actual_columns['server_make']]):
                            asset_make = row[actual_columns['server_make']]
                            if asset.asset_make != asset_make:
                                asset.asset_make = asset_make
                                is_updated = True
                        
                        # Update asset type if provided
                        if 'type' in actual_columns and not pd.isna(row[actual_columns['type']]):
                            asset_type = row[actual_columns['type']]
                            if asset.asset_type != asset_type:
                                asset.asset_type = asset_type
                                is_updated = True
                        
                        if is_updated:
                            asset.save()
                            result['updated'] += 1
                    else:
                        # Create new asset
                        asset_data = {
                            'asset_name': asset_name,
                            'category': category,
                            'is_active': 1,
                            'valid_from': timezone.now()
                        }
                        
                        # Add asset make if provided
                        if 'server_make' in actual_columns and not pd.isna(row[actual_columns['server_make']]):
                            asset_data['asset_make'] = row[actual_columns['server_make']]
                        
                        # Add asset type if provided
                        if 'type' in actual_columns and not pd.isna(row[actual_columns['type']]):
                            asset_data['asset_type'] = row[actual_columns['type']]
                        
                        asset = Asset.objects.create(**asset_data)
                        result['created'] += 1
                    
                    # Process hardware features (RAM, PROCESSOR, HARDDISK)
                    self.process_hardware_features(asset, row, actual_columns)
                    
                    # Process network addresses (IP_ADDRESS, MAC_ID)
                    self.process_network_addresses(asset, row, actual_columns)
                    
                except Exception as e:
                    logger.error(f"Error processing row for asset {asset_name}: {str(e)}")
                    result['errors'].append(f"Error processing {asset_name}: {str(e)}")
            
            result['success'] = True
            return result
            
        except Exception as e:
            logger.error(f"Excel processing error: {str(e)}")
            result['error'] = str(e)
            return result

    def process_hardware_features(self, asset, row, actual_columns):
        """
        Process hardware features (RAM, PROCESSOR, HARDDISK) from Excel row
        """
        features_to_process = [
            ('ram', 'RAM'),
            ('processor', 'PROCESSOR'),
            ('harddisk', 'HARDDISK')
        ]
        
        for col_key, feature_type in features_to_process:
            if col_key in actual_columns and not pd.isna(row[actual_columns[col_key]]):
                feature_value = str(row[actual_columns[col_key]])
                
                # Skip empty values
                if not feature_value.strip():
                    continue
                
                # Check if feature already exists
                feature = AssetFeature.objects.filter(
                    feature_type=feature_type,
                    feature_name=feature_value
                ).first()
                
                if not feature:
                    # Create new feature
                    feature = AssetFeature.objects.create(
                        feature_type=feature_type,
                        feature_name=feature_value,
                        feature_desc=f"{feature_type}: {feature_value}",
                        is_active=1,
                        valid_from=timezone.now()
                    )
                
                # Update asset with this feature
                asset.feature = feature
                asset.save()

    def process_network_addresses(self, asset, row, actual_columns):
        """
        Process network addresses (IP_ADDRESS, MAC_ID) from Excel row
        """
        addresses_to_process = [
            ('ip_address', 'IP_ADDRESS'),
            ('mac_id', 'MAC_ID')
        ]
        
        for col_key, address_type in addresses_to_process:
            if col_key in actual_columns and not pd.isna(row[actual_columns[col_key]]):
                address_value = str(row[actual_columns[col_key]])
                
                # Skip empty values
                if not address_value.strip():
                    continue
                
                # Check if address already exists for this asset
                network_address = AssetNetworkAddress.objects.filter(
                    asset=asset,
                    address_type=address_type,
                    address_value=address_value
                ).first()
                
                if not network_address:
                    # Create new network address
                    AssetNetworkAddress.objects.create(
                        asset=asset,
                        address_type=address_type,
                        address_value=address_value,
                        is_active=1,
                        valid_from=timezone.now()
                    )


# API Views for AJAX requests
def asset_search_api(request):
    """
    API endpoint to search for assets
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    search_term = request.GET.get('term', '')
    if not search_term or len(search_term) < 2:
        return JsonResponse({'results': []})
    
    assets = Asset.objects.filter(
        is_active=1,
        asset_name__icontains=search_term
    ).values('asset_id', 'asset_name', 'asset_type', 'asset_make')[:10]
    
    results = [{'id': a['asset_id'], 'text': f"{a['asset_name']} ({a['asset_type'] or 'Unknown'})"} for a in assets]
    
    return JsonResponse({'results': results})


def asset_category_api(request):
    """
    API endpoint to get asset categories
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    categories = AssetCategory.objects.filter(
        is_active=1
    ).values('category_id', 'category_name')
    
    results = [{'id': c['category_id'], 'name': c['category_name']} for c in categories]
    
    return JsonResponse({'results': results})
