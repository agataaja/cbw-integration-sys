from django.db import models

class InscricoesEventosCbw(models.Model):
    id = models.BigAutoField(primary_key=True)
    id_evento = models.BigIntegerField(blank=True, null=True)
    id_atleta = models.BigIntegerField(blank=True, null=True)
    id_graduacao = models.BigIntegerField(blank=True, null=True)
    id_classe = models.BigIntegerField(blank=True, null=True)
    json_par_equipe = models.TextField(blank=True, null=True)  # This field type is a guess.
    id_classe_peso = models.BigIntegerField(blank=True, null=True)
    id_servico = models.BigIntegerField(blank=True, null=True)
    created_by = models.BigIntegerField(blank=True, null=True)
    updated_by = models.BigIntegerField(blank=True, null=True)
    id_estabelecimento = models.BigIntegerField(blank=True, null=True)
    id_selecao = models.BigIntegerField(blank=True, null=True)
    hist_trocas = models.TextField(blank=True, null=True)  # This field type is a guess.
    created_at = models.BigIntegerField(blank=True, null=True)
    updated_at = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'inscricoes_eventos_cbw'


class ResultadosArena(models.Model):
    id = models.IntegerField(primary_key=True)
    id_evento = models.IntegerField(blank=True, null=True)
    id_evento_arena = models.TextField(blank=True, null=True)
    sportalternatename = models.TextField(db_column='sportAlternateName', blank=True, null=True)  # Field name made lowercase.
    sportname = models.TextField(db_column='sportName', blank=True, null=True)  # Field name made lowercase.
    name = models.TextField(blank=True, null=True)
    sportid = models.TextField(db_column='sportId', blank=True, null=True)  # Field name made lowercase.
    audiencename = models.TextField(db_column='audienceName', blank=True, null=True)  # Field name made lowercase.
    countfighters = models.TextField(db_column='countFighters', blank=True, null=True)  # Field name made lowercase.
    countfights = models.TextField(db_column='countFights', blank=True, null=True)  # Field name made lowercase.
    weightcategoryfullname = models.TextField(db_column='weightCategoryFullName', blank=True, null=True)  # Field name made lowercase.
    customid = models.TextField(db_column='customId', blank=True, null=True)  # Field name made lowercase.
    fullname = models.TextField(db_column='fullName', blank=True, null=True)  # Field name made lowercase.
    rank = models.IntegerField(blank=True, null=True)
    id_estabelecimento = models.IntegerField(blank=True, null=True)
    id_classe_peso = models.IntegerField(blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)
    created_at = models.IntegerField(blank=True, null=True)
    updated_at = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'resultados_arena'
