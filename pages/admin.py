from django.contrib import admin

from .models import ContactMessage, Subscriber


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "topic", "is_processed", "created_at"]
    list_filter = ["topic", "is_processed"]
    list_editable = ["is_processed"]
    search_fields = ["name", "phone", "message"]


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "created_at"]
    search_fields = ["email"]
