# Generated by Django 3.2.7 on 2022-11-05 11:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20221019_0808'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='about',
            field=models.CharField(max_length=1024, null=True, verbose_name='Sobre'),
        ),
        migrations.AddField(
            model_name='group',
            name='group_type',
            field=models.CharField(max_length=30, null=True, verbose_name='Tipo do grupo'),
        ),
        migrations.AddField(
            model_name='group',
            name='title',
            field=models.CharField(max_length=2048, null=True, verbose_name='Título do grupo'),
        ),
    ]
