# Generated by Django 3.2.7 on 2022-02-23 09:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20220212_1734'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='messages_count',
            field=models.IntegerField(null=True, verbose_name='mensagens'),
        ),
        migrations.AlterField(
            model_name='report',
            name='id',
            field=models.CharField(max_length=255, primary_key=True, serialize=False, verbose_name='grupo'),
        ),
    ]
