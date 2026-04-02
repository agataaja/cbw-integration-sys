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
        db_table = 'id_classe_peso'
        unique_together = (('ano', 'escopo', 'estilo', 'categoria', 'id_classe_peso'),)
