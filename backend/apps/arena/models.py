from django.db import models

# Create your models here.


class WebhookPayload(models.Model):

    received_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField()


class Luta(models.Model):

    id = models.CharField(max_length=50, primary_key=True)  # UUID + id_evento
    id_categoria_arena = models.CharField(max_length=150, null=True, blank=True)
    id_evento = models.IntegerField()
    id_atleta1 = models.IntegerField()
    id_atleta2 = models.IntegerField()
    flag_finalizado = models.IntegerField()
    round = models.CharField(max_length=150)
    id_atleta_ganhador = models.IntegerField(null=True, blank=True)
    sportAlternateName = models.CharField(max_length=150)
    weightCategoryName = models.CharField(max_length=150)
    audienceName = models.CharField(max_length=150)
    id_classe_peso = models.IntegerField(null=True, blank=True)

    atleta1_flag_injured = models.IntegerField(null=True, blank=True)
    atleta1_flag_seeded = models.IntegerField(null=True, blank=True)
    atleta1_draw_rank = models.CharField(max_length=10, null=True, blank=True)
    atleta1_RobinRank = models.CharField(max_length=10, null=True, blank=True)

    atleta2_flag_injured = models.IntegerField(null=True, blank=True)
    atleta2_flag_seeded = models.IntegerField(null=True, blank=True)
    atleta2_draw_rank = models.CharField(max_length=10, null=True, blank=True)
    atleta2_RobinRank = models.CharField(max_length=10, null=True, blank=True)

    resultado = models.CharField(max_length=30, null=True, blank=True)
    tipo_vitoria = models.CharField(max_length=10, null=True, blank=True)

    atleta1_ranking_point = models.IntegerField(null=True, blank=True)
    atleta2_ranking_point = models.IntegerField(null=True, blank=True)

    numero = models.IntegerField(null=True, blank=True)
    tapete = models.CharField(max_length=10)

    data_inicio = models.DateTimeField(null=True, blank=True)
    data_fim = models.DateTimeField(null=True, blank=True)

    is_temporary = models.BooleanField(default=False)


class EventosSge(models.Model):
    id = models.AutoField(primary_key=True)
    id_sge = models.IntegerField(unique=True)  # ID externo do SGE
    local = models.CharField(max_length=50, null=True, blank=True)
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    id_tipo = models.IntegerField()
    descricao = models.CharField(max_length=150, null=True, blank=True)
    escopo = models.CharField(max_length=50, null=True, blank=True)
    audienceName = models.CharField(max_length=50, null=True, blank=True)
    ano = models.IntegerField(null=True, blank=True)


class CredentialsArena(models.Model):
    id = models.AutoField(primary_key=True)
    client_id = models.CharField(max_length=150, null=True, blank=True)
    client_secret = models.CharField(max_length=150, null=True, blank=True)
    api_key = models.CharField(max_length=150, null=True, blank=True)
    nome_maquina = models.CharField(max_length=150, null=True, blank=True)


class EventosArena(models.Model):
    id = models.AutoField(primary_key=True)
    id_arena = models.CharField(max_length=100, unique=True)  # ID externo do Arena
    nome_evento = models.CharField(max_length=100)
    isTeamEvent = models.BooleanField()
    isBeachWrestlingTournament = models.BooleanField()
    audienceName = models.CharField(max_length=50, null=True, blank=True)

    # Relacionamento: uma credencial pode ter vários eventos
    credencial = models.ForeignKey(
        CredentialsArena, on_delete=models.CASCADE, related_name="eventos"
    )

    # Relacionamento N:N com eventos SGE
    eventos_sge = models.ManyToManyField(EventosSge, related_name="eventos_arena")




