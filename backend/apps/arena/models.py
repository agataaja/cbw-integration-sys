from django.db import models

# Create your models here.


class ArenaWebhookPayload(models.Model):

    received_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField()
    

class ArenaClient(models.Model):

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    host = models.CharField(max_length=255, null=True, blank=True)
    api_key = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    grant_type = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ArenaSportEvent(models.Model):

    id = models.AutoField(primary_key=True)
    arena_client = models.ForeignKey(ArenaClient, on_delete=models.CASCADE, related_name='events')
    event_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class ArenaSession(models.Model):

    id = models.AutoField(primary_key=True)
    arena_sport_event = models.ForeignKey(ArenaSportEvent, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class ArenaMat(models.Model):

    id = models.AutoField(primary_key=True)
    arena_session = models.ForeignKey(ArenaSession, on_delete=models.CASCADE, related_name='mats')
    mat_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class ArenaSportEventWeightCategory(models.Model):

    id = models.AutoField(primary_key=True)
    arena_sport_event = models.ForeignKey(ArenaSportEvent, on_delete=models.CASCADE, related_name='weight_categories')
    category_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class ArenaFight(models.Model):

    id = models.AutoField(primary_key=True)
    arena_sport_event_weight_category = models.ForeignKey(ArenaSportEventWeightCategory, on_delete=models.CASCADE, related_name='fights')
    fight_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class ArenaFighter(models.Model):

    id = models.AutoField(primary_key=True)
    fight = models.ForeignKey(ArenaFight, on_delete=models.CASCADE, related_name='fighters')
    fighter_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class ArenaAthlete(models.Model):

    id = models.AutoField(primary_key=True)
    fighter = models.ForeignKey(ArenaFighter, on_delete=models.CASCADE, related_name='athletes')
    athlete_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class ArenaPerson(models.Model):

    id = models.AutoField(primary_key=True)
    athlete = models.ForeignKey(ArenaAthlete, on_delete=models.CASCADE, related_name='persons')
    person_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class ArenaWebhook(models.Model):

    id = models.AutoField(primary_key=True)
    arena_client = models.ForeignKey(ArenaClient, on_delete=models.CASCADE, related_name='webhooks')
    webhook_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name