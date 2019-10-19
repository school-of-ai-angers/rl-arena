from django.contrib import admin
from .models import Environment


class EnvironmentAdmin(admin.ModelAdmin):
    pass


admin.site.register(Environment, EnvironmentAdmin)
