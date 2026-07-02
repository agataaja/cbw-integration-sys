from django.db import models
from apps.sge.models import GestaoEventos, GestaoAtletas, GestaoIdsAtletas, LutaSGE
from apps.arena.models import ArenaPerson, ArenaAthlete, ArenaFighter, ArenaSportEvent, ArenaFight, ArenaClient
from apps.normalization.models import AgeGroupMapping


class EventBridge(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    
    # Legacy string fields (kept for backward compatibility)
    age_group = models.CharField(max_length=255, null=True, blank=True, help_text="Legacy: Arena age group (use age_group_mappings instead)")
    sge_age_category = models.CharField(max_length=255, null=True, blank=True, help_text="Legacy: SGE age category (use age_group_mappings instead)")
    
    # Normalized age group mappings
    age_group_mappings = models.ManyToManyField(
        AgeGroupMapping,
        related_name='event_bridges',
        blank=True,
        help_text="Normalized age group mappings that this event bridge covers"
    )
    
    sge_event = models.ForeignKey(GestaoEventos, on_delete=models.CASCADE, related_name='evento_sge_origin')
    arena_event = models.ForeignKey(ArenaSportEvent, on_delete=models.CASCADE, related_name='evento_arena_origin')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            ('arena_event', 'age_group', 'sge_event', 'sge_age_category'),
        )
    
    def get_arena_age_variations(self) -> list[str]:
        """Get all Arena age group variations from linked mappings."""
        variations = []
        for mapping in self.age_group_mappings.all():
            variations.extend(mapping.arena_variations)
        return variations
    
    def get_sge_age_variations(self) -> list[str]:
        """Get all SGE age group variations from linked mappings."""
        variations = []
        for mapping in self.age_group_mappings.all():
            variations.extend(mapping.sge_variations)
        return variations
    
    def matches_arena_category(self, category_name: str) -> bool:
        """Check if a category name matches any of this bridge's age group mappings."""
        for mapping in self.age_group_mappings.all():
            if mapping.matches_arena_name(category_name):
                return True
        # Fallback to legacy string comparison
        if self.age_group and category_name:
            return self.age_group.upper().strip() == category_name.upper().strip()
        return False


class ClientBridge(models.Model):
    id = models.BigAutoField(primary_key=True)
    arena_client = models.ForeignKey(ArenaClient, on_delete=models.CASCADE, related_name='arena_client_origin')
    eventos_match = models.ManyToManyField(EventBridge, related_name='arena_client_eventos_match_origin', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AthleteBridge(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    sge_id_atleta = models.ForeignKey(GestaoAtletas, on_delete=models.CASCADE, related_name='atleta_sge_origin')
    sge_id = models.ForeignKey(GestaoIdsAtletas, on_delete=models.CASCADE, related_name='id_atleta_sge_origin')
    arena_custom_id = models.ForeignKey(ArenaPerson, on_delete=models.CASCADE, related_name='atleta_arena_origin', null=True, blank=True)
    arena_athlete = models.ManyToManyField(ArenaAthlete, related_name='atleta_arena_athlete_origin', blank=True)
    arena_fighter = models.ManyToManyField(ArenaFighter, related_name='atleta_arena_fighter_origin', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class FightBridge(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=255)
    sge_luta = models.ForeignKey(LutaSGE, on_delete=models.CASCADE, related_name='luta_sge_origin')
    arena_fight = models.ForeignKey(ArenaFight, on_delete=models.CASCADE, related_name='luta_arena_origin', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# Temporary aliases to avoid immediate breakage in any remaining legacy imports.
EventosMatch = EventBridge
ArenaClientsMatch = ClientBridge
AtletaMatch = AthleteBridge
LutaMatch = FightBridge