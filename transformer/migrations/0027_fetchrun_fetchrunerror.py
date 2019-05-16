# Generated by Django 2.0.13 on 2019-05-09 17:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('transformer', '0026_auto_20190430_2200'),
    ]

    operations = [
        migrations.CreateModel(
            name='FetchRun',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[(0, 'Started'), (1, 'Finished'), (2, 'Errored')], max_length=100)),
                ('source', models.CharField(choices=[(0, 'Aurora'), (1, 'Archivematica'), (2, 'Fedora'), (3, 'ArchivesSpace'), (4, 'Pisces'), (5, 'Cartographer'), (6, 'Trees'), (7, 'Wikidata'), (8, 'Wikipedia')], max_length=100)),
                ('object_type', models.CharField(blank=True, choices=[('agents', 'Agents'), ('collections', 'Collections'), ('objects', 'Objects'), ('terms', 'Terms')], max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='FetchRunError',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('message', models.CharField(max_length=255)),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='transformer.FetchRun')),
            ],
        ),
    ]
