# Generated by Django 3.2.7 on 2021-09-09 12:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_message_photo_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='audio_url',
            field=models.CharField(max_length=1024, null=True, verbose_name='URL do áudio'),
        ),
    ]
