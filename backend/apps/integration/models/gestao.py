
from django.db import models


class GestaoAtletas(models.Model):
    id = models.BigIntegerField(primary_key=True)
    id_pais = models.IntegerField(blank=True, null=True)
    tipo_atleta = models.TextField(blank=True, null=True)
    nome_completo = models.TextField(blank=True, null=True)
    data_nascimento = models.IntegerField(blank=True, null=True)
    sexo = models.CharField(max_length=1, blank=True, null=True)
    foto = models.TextField(blank=True, null=True)
    foto_apresentacao = models.TextField(blank=True, null=True)
    patrocinador = models.TextField(blank=True, null=True)
    biografia = models.TextField(blank=True, null=True)
    perfil_facebook = models.TextField(blank=True, null=True)
    perfil_instagram = models.TextField(blank=True, null=True)
    perfil_twitter = models.TextField(blank=True, null=True)
    perfil_tiktok = models.TextField(blank=True, null=True)
    perfil_twitch = models.TextField(blank=True, null=True)
    perfil_booyah = models.TextField(blank=True, null=True)
    perfil_outras = models.TextField(blank=True, null=True)
    registro_confederacao = models.TextField(blank=True, null=True)
    patrocinio = models.TextField(blank=True, null=True)
    idade = models.IntegerField(blank=True, null=True)
    created_by = models.BigIntegerField(blank=True, null=True)
    updated_by = models.BigIntegerField(blank=True, null=True)
    created_at = models.BigIntegerField(blank=True, null=True)
    updated_at = models.BigIntegerField(blank=True, null=True)
    estabelecimento_id = models.BigIntegerField(blank=True, null=True)
    raw_payload = models.JSONField(blank=True, null=True)
    inserted_at = models.DateTimeField(blank=True, null=True)
    data_create = models.BigIntegerField(blank=True, null=True)
    foto_info = models.TextField(blank=True, null=True)
    urlfoto = models.TextField(db_column='urlFoto', blank=True, null=True)  # Field name made lowercase.
    urlfotoapresentacao = models.TextField(db_column='urlFotoApresentacao', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'gestao_atletas'


class GestaoEstabelecimentos(models.Model):
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

