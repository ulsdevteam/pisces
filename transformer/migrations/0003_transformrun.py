# Generated by Django 2.0.13 on 2019-04-09 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transformer', '0002_auto_20190408_2005'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransformRun',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('end_time', models.DateTimeField()),
                ('status', models.CharField(choices=[(0, 'Running'), (1, 'Finished'), (2, 'Errored')], max_length=100)),
            ],
        ),
    ]
