from django.contrib import admin

from .models import (
    Asset,
    AssetCategory,
    AssetFeature,
    AssetLocation,
    AssetNetworkAddress,
)


# ---------------------------------------------------------------------------
# Inline definitions
# ---------------------------------------------------------------------------


class AssetNetworkAddressInline(admin.TabularInline):
    """
    Inline admin for quickly managing network addresses
    (IP / MAC) directly inside the Asset admin screen.
    """

    model = AssetNetworkAddress
    extra = 0
    fields = ("address_type", "address_value", "is_active")
    readonly_fields = ("valid_from", "valid_to")
    show_change_link = True


# ---------------------------------------------------------------------------
# Model-admin customisations
# ---------------------------------------------------------------------------


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ("category_name", "category_type", "is_active", "valid_from", "valid_to")
    list_filter = ("is_active", "category_type")
    search_fields = ("category_name", "category_type")
    ordering = ("-is_active", "category_name")


@admin.register(AssetFeature)
class AssetFeatureAdmin(admin.ModelAdmin):
    list_display = ("feature_type", "feature_name", "feature_desc", "is_active", "valid_from", "valid_to")
    list_filter = ("is_active", "feature_type")
    search_fields = ("feature_type", "feature_name", "feature_desc")
    ordering = ("feature_type", "feature_name")


@admin.register(AssetLocation)
class AssetLocationAdmin(admin.ModelAdmin):
    list_display = (
        "address_type",
        "address_value",
        "city",
        "state",
        "country",
        "is_active",
        "valid_from",
        "valid_to",
    )
    list_filter = ("is_active", "address_type", "country")
    search_fields = ("address_value", "city", "state", "country")
    ordering = ("address_type", "address_value")


@admin.register(AssetNetworkAddress)
class AssetNetworkAddressAdmin(admin.ModelAdmin):
    list_display = ("asset", "address_type", "address_value", "is_active", "valid_from", "valid_to")
    list_filter = ("is_active", "address_type")
    search_fields = ("address_value", "asset__asset_name")
    raw_id_fields = ("asset",)
    ordering = ("address_type", "address_value")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "asset_name",
        "category",
        "asset_make",
        "asset_type",
        "feature",
        "location",
        "is_active",
    )
    list_filter = ("is_active", "category", "asset_type")
    search_fields = ("asset_name", "asset_make", "asset_type", "asset_purpose")
    raw_id_fields = ("category", "feature", "location", "parent_asset")
    inlines = [AssetNetworkAddressInline]
    ordering = ("asset_name",)

