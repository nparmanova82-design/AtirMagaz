from django.contrib import admin
from django.utils.html import format_html

from .models import Brand, Note, Perfume, Review, Variant


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "founded", "is_niche", "perfume_count"]
    list_filter = ["is_niche", "country"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}

    @admin.display(description="Atirlar")
    def perfume_count(self, obj):
        return obj.perfumes.count()


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    fields = ["name", "rating", "text", "is_approved"]


@admin.register(Perfume)
class PerfumeAdmin(admin.ModelAdmin):
    list_display = ["swatch", "__str__", "gender", "concentration", "family",
                    "is_new", "is_bestseller", "is_active", "sold_count"]
    list_display_links = ["__str__"]
    list_editable = ["is_new", "is_bestseller", "is_active"]
    list_filter = ["gender", "concentration", "family", "brand", "is_new", "is_bestseller", "is_active"]
    search_fields = ["name", "brand__name", "perfumer"]
    prepopulated_fields = {"slug": ["name"]}
    autocomplete_fields = ["brand", "top_notes", "heart_notes", "base_notes"]
    inlines = [VariantInline, ReviewInline]
    fieldsets = [
        (None, {"fields": ["brand", "name", "slug", "description"]}),
        ("Tasnif", {"fields": [("gender", "concentration", "family"), ("year", "perfumer"),
                               ("season", "time_of_day"), ("longevity", "sillage")]}),
        ("Hid piramidasi", {"fields": ["top_notes", "heart_notes", "base_notes"]}),
        ("Ko'rinish", {"fields": ["image", ("color", "shape", "cap")]}),
        ("Vitrina", {"fields": [("is_new", "is_bestseller", "is_active"), "sold_count"]}),
    ]

    @admin.display(description="")
    def swatch(self, obj):
        return format_html(
            '<span style="display:inline-block;width:14px;height:14px;border-radius:50%;'
            'background:{};border:1px solid #0002"></span>', obj.color)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["perfume", "name", "rating", "is_approved", "created_at"]
    list_filter = ["is_approved", "rating"]
    list_editable = ["is_approved"]
    search_fields = ["name", "text", "perfume__name"]
