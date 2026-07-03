from django.contrib import admin
from .models import Personal

@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'apellidos', 'dni', 'cargo', 'user')
    search_fields = ('dni', 'nombres', 'apellidos')