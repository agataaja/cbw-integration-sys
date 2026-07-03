from django.db import models

# Create your models here.

class IdClassePeso(models.Model):
    id = models.BigAutoField(primary_key=True)
    ano = models.TextField()
    escopo = models.TextField()
    estilo = models.TextField()
    categoria = models.TextField()
    id_classe_peso = models.IntegerField()
    peso = models.TextField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sge_id_classe_peso'
        unique_together = (('ano', 'escopo', 'estilo', 'categoria', 'id_classe_peso'),)



class AgeGroupMapping(models.Model):
    """
    Normalized mapping between Arena and SGE age group naming variations.
    
    Example:
    - canonical_name: "u17"
    - arena_variations: ["U17", "u17", "Sub-17", "Under 17"]
    - sge_variations: ["Sub-17", "SUB 17", "SUB-17"]
    
    This allows flexible matching of Arena category names to SGE age groups.
    The first SGE variation is considered the primary one used when sending to SGE.
    """
    id = models.BigAutoField(primary_key=True)
    canonical_name = models.CharField(max_length=50, unique=True, help_text="Normalized age group name based on Arena identifier (e.g., 'u17', 'seniors')")
    arena_variations = models.JSONField(default=list, help_text="List of Arena age group name variations")
    sge_variations = models.JSONField(default=list, help_text="List of SGE age category variations (first is primary, e.g., ['Sub-17', 'SUB 17'])")
    sort_order = models.IntegerField(default=0, help_text="Display order (youngest to oldest)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'canonical_name']
        verbose_name = 'Age Group Mapping'
        verbose_name_plural = 'Age Group Mappings'
    
    def __str__(self):
        primary_sge = self.sge_variations[0] if self.sge_variations else 'N/A'
        return f"{self.canonical_name} → {primary_sge}"
    
    @property
    def primary_sge_variation(self) -> str:
        """Return the primary SGE variation (first in list)."""
        return self.sge_variations[0] if self.sge_variations else ""
    
    def matches_arena_name(self, arena_name: str) -> bool:
        """Check if given arena_name matches any variation (case-insensitive)."""
        if not arena_name:
            return False
        arena_upper = arena_name.upper().strip()
        return any(var.upper().strip() == arena_upper for var in self.arena_variations)
    
    def matches_sge_name(self, sge_name: str) -> bool:
        """Check if given sge_name matches any SGE variation (case-insensitive)."""
        if not sge_name:
            return False
        sge_upper = sge_name.upper().strip()
        return any(var.upper().strip() == sge_upper for var in self.sge_variations)


class SyncEstado(models.Model):
    nome = models.TextField(primary_key=True)
    pagina_atual = models.IntegerField()
    total_paginas = models.IntegerField(blank=True, null=True)
    status = models.TextField()
    updated_at = models.DateTimeField(blank=True, null=True)
    indice_peso_atual = models.IntegerField(blank=True, null=True)
    total_pesos = models.IntegerField(blank=True, null=True)
    ano_atual = models.IntegerField(blank=True, null=True)
    grupo_atual = models.TextField(blank=True, null=True)
    id_classe_peso_atual = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sync_estado'