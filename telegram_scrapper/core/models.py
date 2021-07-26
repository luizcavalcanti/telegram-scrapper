from django.db import models


MEDIAS = ("audio", "document", "photo", "video")


class Message(models.Model):
    message_id = models.BigIntegerField("ID da mensagem", unique=True)
    group = models.CharField("Grupo", max_length=255)
    sender = models.CharField("remetente", max_length=255)
    sent_at = models.DateTimeField("enviado em")
    message = models.TextField("mensagem")
    video = models.JSONField("vídeo", default=dict)
    audio = models.JSONField("áudio", default=dict)
    document = models.JSONField("documento", default=dict)
    photo = models.JSONField("imagem", default=dict)
    forwarded = models.BooleanField("encaminhada", default=False)

    class Meta:
        verbose_name = "mensagem"
        verbose_name_plural = "mensagens"
        ordering = ["-sent_at"]
        indexes = [models.Index(fields=["sent_at"]), models.Index(fields=["group"])]


class MessageSummary(Message):
    class Meta:
        proxy = True
        verbose_name_plural = '(WIP) Sumário de Mensagens'
