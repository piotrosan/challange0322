from django.contrib import admin

from .models import Client, Subscriber, SubscriberSMS, User


class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('create_date', 'email', 'gdpr_consent')


class SubscriberSMSAdmin(admin.ModelAdmin):
    list_display = ('create_date', 'phone', 'gdpr_consent')


class UserAdmin(admin.ModelAdmin):
    list_display = ('create_date', 'phone', 'email', 'gdpr_consent')


class ClientAdmin(admin.ModelAdmin):
    list_display = ('create_date', 'phone', 'email')


admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(SubscriberSMS, SubscriberSMSAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Client, ClientAdmin)
