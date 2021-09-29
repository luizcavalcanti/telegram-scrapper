from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models


MEDIAS = ("audio", "document", "photo", "video")


class Message(models.Model):
    message_id = models.BigIntegerField("ID da mensagem")
    group = models.CharField("Grupo", max_length=255)
    sender = models.CharField("remetente", max_length=255)
    sent_at = models.DateTimeField("enviado em")
    message = models.TextField("mensagem")
    video = models.JSONField("vídeo", default=dict)
    video_url = models.CharField("URL do vídeo", max_length=1024, null=True)
    audio = models.JSONField("áudio", default=dict)
    audio_url = models.CharField("URL do áudio", max_length=1024, null=True)
    document = models.JSONField("documento", default=dict)
    photo = models.JSONField("imagem", default=dict)
    photo_url = models.CharField("URL da imagem", max_length=1024, null=True)
    forwarded = models.BooleanField("encaminhada", default=False)
    search_vector = SearchVectorField(null=True)

    class Meta:
        verbose_name = "mensagem"
        verbose_name_plural = "mensagens"
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["sent_at"]),
            models.Index(fields=["group"]),
            GinIndex(fields=['search_vector']),
        ]
        unique_together = ["message_id", "group"]


class TelegramUser(models.Model):
    user_id = models.BigIntegerField("ID do usuário", unique=True, primary_key=True)
    username = models.CharField("Usuário", max_length=255, null=True)
    first_name = models.CharField("Nome", max_length=255, null=True)
    last_name = models.CharField("Sobrenome", max_length=255, null=True)
    phone = models.CharField("Telefone", max_length=255, null=True)
    photo = models.JSONField("Foto de perfil", default=dict, null=True)
    fake = models.BooleanField("Falso", default=False)
    deleted = models.BooleanField("Excluído", default=False)
    verified = models.BooleanField("Verificado", default=False)

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        indexes = [models.Index(fields=["user_id"]), models.Index(fields=["username"])]


class Group(models.Model):
    id = models.CharField("grupo", max_length=255, primary_key=True)
    active = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "grupo"
        verbose_name_plural = "grupos"
        ordering = ["id"]
