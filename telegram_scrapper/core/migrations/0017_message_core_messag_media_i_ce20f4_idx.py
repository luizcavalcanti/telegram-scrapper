# Generated by Django 3.2.7 on 2022-10-08 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_message_media_id'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['media_id'], name='core_messag_media_i_ce20f4_idx'),
        ),
    ]
