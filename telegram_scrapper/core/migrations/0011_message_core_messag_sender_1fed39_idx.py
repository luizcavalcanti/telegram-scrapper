# Generated by Django 3.2.7 on 2022-02-12 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_group_users_count'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['sender'], name='core_messag_sender_1fed39_idx'),
        ),
    ]
