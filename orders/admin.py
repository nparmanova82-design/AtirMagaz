from django.contrib import admin

from .models import Order, OrderItem, PromoCode


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["variant", "title", "volume_label", "price", "quantity"]
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["number", "full_name", "phone", "region", "total", "payment", "status", "created_at"]
    list_filter = ["status", "delivery", "payment", "region", "created_at"]
    list_editable = ["status"]
    search_fields = ["number", "full_name", "phone"]
    readonly_fields = ["number", "subtotal", "discount", "delivery_cost", "gift_wrap_cost", "total",
                       "promo_code", "created_at"]
    inlines = [OrderItemInline]
    fieldsets = [
        (None, {"fields": ["number", "status", "created_at"]}),
        ("Mijoz", {"fields": ["user", "full_name", "phone", "email"]}),
        ("Yetkazib berish", {"fields": ["delivery", "region", "address", "comment"]}),
        ("Sovg'a", {"fields": ["gift_wrap", "gift_note"]}),
        ("To'lov", {"fields": ["payment", "promo_code", "subtotal", "discount",
                               "delivery_cost", "gift_wrap_cost", "total"]}),
    ]


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "percent", "min_total", "is_active", "description"]
    list_editable = ["is_active"]
