from django.contrib import admin
from .models import AgeGroupMapping, IdClassePeso


@admin.register(AgeGroupMapping)
class AgeGroupMappingAdmin(admin.ModelAdmin):
    list_display = ('canonical_name', 'primary_sge_variation', 'sort_order', 'created_at')
    list_editable = ('sort_order',)
    search_fields = ('canonical_name', 'arena_variations', 'sge_variations')
    ordering = ('sort_order', 'canonical_name')
    
    fieldsets = (
        (None, {
            'fields': ('canonical_name', 'arena_variations', 'sge_variations', 'sort_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(IdClassePeso)
class IdClassePesoAdmin(admin.ModelAdmin):
    list_display = ('id_classe_peso', 'estilo', 'categoria', 'peso', 'ano', 'escopo')
    list_filter = ('estilo', 'escopo', 'ano')
    search_fields = ('categoria', 'peso', 'estilo')
    ordering = ('ano', 'escopo', 'estilo', 'categoria')
