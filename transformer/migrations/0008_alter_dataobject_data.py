# Generated by Django 3.2.5 on 2021-07-02 00:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transformer', '0007_dataobject_online_pending'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataobject',
            name='data',
            field=models.JSONField(),
        ),
    ]
