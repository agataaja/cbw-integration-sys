
from django.db import models


class GestaoAtletaDocumentos(models.Model):
    id = models.BigIntegerField(primary_key=True)
    id_atleta = models.BigIntegerField(blank=True, null=True)
    id_tipo = models.IntegerField(blank=True, null=True)
    numero = models.TextField(blank=True, null=True)
    orgao_emissor = models.TextField(blank=True, null=True)
    validade = models.TextField(blank=True, null=True)
    data_emissao = models.TextField(blank=True, null=True)
    data_update = models.BigIntegerField(blank=True, null=True)
    data_create = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gestao_atleta_documentos'


class GestaoAtletas(models.Model):
    id = models.BigIntegerField(primary_key=True)
    nome_completo = models.TextField(blank=True, null=True)
    sexo = models.CharField(max_length=1, blank=True, null=True)
    data_nascimento = models.IntegerField(blank=True, null=True)
    id_pais = models.IntegerField(blank=True, null=True)
    tipo_atleta = models.TextField(blank=True, null=True)
    data_create = models.BigIntegerField(blank=True, null=True)
    registro_confederacao = models.TextField(blank=True, null=True)
    cpf = models.TextField(blank=True, null=True)
    estabelecimento = models.ForeignKey('GestaoEstabelecimentos', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gestao_atletas'


class GestaoIdsAtletas(models.Model):
    id = models.BigIntegerField(primary_key=True)
    id_atleta = models.ForeignKey(GestaoAtletas, models.DO_NOTHING, db_column='id_atleta', blank=True, null=True)
    id_esporte = models.IntegerField(blank=True, null=True)
    id_tecnico = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gestao_ids_atletas'


class GestaoEstabelecimentos(models.Model):
    # This model comes from the SGE API base https://restcbw.bigmidia.com/gestao/api on path /estabelecimento/ and is based on the 'gestao_estabelecimentos' table in the database.

    id = models.IntegerField(primary_key=True)
    descricao = models.TextField(blank=True, null=True)
    nome_fantasia = models.TextField(blank=True, null=True)
    sigla = models.TextField(blank=True, null=True)
    sigla_evento = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    cnpj = models.TextField(blank=True, null=True)
    id_moip = models.TextField(blank=True, null=True)
    id_estabelecimento_tipo = models.IntegerField(blank=True, null=True)
    id_time = models.IntegerField(blank=True, null=True)
    flg_ativo = models.IntegerField(blank=True, null=True)
    nacionalidade = models.IntegerField(blank=True, null=True)
    registro = models.TextField(blank=True, null=True)
    uf = models.TextField(blank=True, null=True)
    dominio = models.TextField(blank=True, null=True)
    dominio_sge = models.TextField(blank=True, null=True)
    perfil_facebook = models.TextField(blank=True, null=True)
    perfil_instagram = models.TextField(blank=True, null=True)
    perfil_youtube = models.TextField(blank=True, null=True)
    perfil_tiktok = models.TextField(blank=True, null=True)
    perfil_twitter = models.TextField(blank=True, null=True)
    biografia = models.TextField(blank=True, null=True)
    url_logo = models.TextField(blank=True, null=True)
    url_logo2 = models.TextField(blank=True, null=True)
    url_logo3 = models.TextField(blank=True, null=True)
    urllogo = models.TextField(blank=True, null=True)
    json_data = models.JSONField(blank=True, null=True)
    fundacao = models.TextField(blank=True, null=True)
    data_alteracao = models.IntegerField(blank=True, null=True)
    created_at = models.IntegerField(blank=True, null=True)
    updated_at = models.IntegerField(blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)
    old_id = models.IntegerField(blank=True, null=True)
    urllogo_0 = models.TextField(db_column='urlLogo', blank=True, null=True)  # Field name made lowercase. Field renamed because of name conflict.

    class Meta:
        managed = False
        db_table = 'gestao_estabelecimentos'


class GestaoEventos(models.Model):
    # This model is based on the 'gestao_eventos' table in the database. That comes form SGE API base https://restcbw.bigmidia.com/gestao/api on path /evento/

    id = models.IntegerField(primary_key=True)
    id_esporte = models.IntegerField(blank=True, null=True)
    id_estabelecimento = models.IntegerField(blank=True, null=True)
    id_campeonato = models.TextField(blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    arte_evento = models.TextField(blank=True, null=True)
    cor = models.TextField(blank=True, null=True)
    idioma = models.TextField(blank=True, null=True)
    id_evento_pai = models.IntegerField(blank=True, null=True)
    id_tipo = models.IntegerField(blank=True, null=True)
    flag_anuidade_confed_pessoa = models.IntegerField(blank=True, null=True)
    flag_anuidade_fed_pessoa = models.IntegerField(blank=True, null=True)
    flag_individual = models.IntegerField(blank=True, null=True)
    local = models.TextField(blank=True, null=True)
    escopo = models.TextField(blank=True, null=True)
    texto = models.TextField(blank=True, null=True)
    data_inicio = models.TextField(blank=True, null=True)
    data_fim = models.TextField(blank=True, null=True)
    data_inicio_inscricao = models.TextField(blank=True, null=True)
    data_limit_inscricao = models.TextField(blank=True, null=True)
    data_limit_pagamento = models.TextField(blank=True, null=True)
    num_visitas = models.IntegerField(blank=True, null=True)
    id_pais = models.IntegerField(blank=True, null=True)
    id_municipio = models.IntegerField(blank=True, null=True)
    bairro = models.TextField(blank=True, null=True)
    cep = models.TextField(blank=True, null=True)
    complemento = models.TextField(blank=True, null=True)
    tipo_logradouro = models.TextField(blank=True, null=True)
    logradouro = models.TextField(blank=True, null=True)
    logradouro2 = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    numero = models.TextField(blank=True, null=True)
    flag_del = models.IntegerField(blank=True, null=True)
    flag_calendario = models.IntegerField(blank=True, null=True)
    created_at = models.IntegerField(blank=True, null=True)
    updated_at = models.IntegerField(blank=True, null=True)
    id_aeroporto_preferencial = models.IntegerField(blank=True, null=True)
    rodoviaria = models.TextField(blank=True, null=True)
    flag_oculto = models.IntegerField(blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gestao_eventos'


class InscricoesEventosSGE(models.Model):
    # This model is based on the 'inscricoes_eventos_cbw' table in the database. That comes form SGE API base https://restcbw.bigmidia.com/cbw/api on path /evento-atleta/

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
        db_table = 'sge_inscricoes_eventos_cbw'


class ResultadoSGE(models.Model):
    # This model is based on the 'resultados_arena' table in the database. That comes form SGE API base https://restcbw.bigmidia.com/cbw/api on path /resultado-rank-arena/
    # It is triggerd in db by edge functions that consumes the SGE API
    # Origin data comes from Arena API, mannually upsert by me so far

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
        db_table = 'sge_resultados_arena'


class LutaSGE(models.Model):
    # This model is based on the 'sge_luta' table in the database. That comes form SGE API base https://restcbw.bigmidia.com/cbw/api on path /evento-luta/ and is updated by edge functions that consumes the SGE API

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

    
class RankingSGE(models.Model):
    
    pk = models.CompositePrimaryKey('ano', 'grupo', 'id_classe_peso', 'colocacao', 'id_atleta')
    ano = models.IntegerField()
    grupo = models.TextField()
    id_classe_peso = models.IntegerField()
    colocacao = models.IntegerField()
    id_atleta = models.ForeignKey(GestaoAtletas, models.DO_NOTHING, db_column='id_atleta')
    nome_completo = models.TextField(blank=True, null=True)
    estilo = models.TextField(blank=True, null=True)
    categoria = models.TextField(blank=True, null=True)
    peso = models.TextField(blank=True, null=True)
    pontos = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    data_recorte = models.DateField(blank=True, null=True)
    payload = models.JSONField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    clube = models.TextField(blank=True, null=True)
    clube_url_logo = models.TextField(blank=True, null=True)
    fed_url_logo = models.TextField(blank=True, null=True)
    federacao = models.TextField(blank=True, null=True)
    federacao_uf = models.TextField(blank=True, null=True)
    id_federacao = models.ForeignKey(GestaoEstabelecimentos, models.DO_NOTHING, db_column='id_federacao', blank=True, null=True)
    id_clube = models.ForeignKey(GestaoEstabelecimentos, models.DO_NOTHING, db_column='id_clube', related_name='sgeranking_id_clube_set', blank=True, null=True)
    urlfotoatleta = models.TextField(db_column='urlFotoAtleta', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'sge_ranking'