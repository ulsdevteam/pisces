# Generated by Django 2.0.13 on 2019-04-30 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transformer', '0024_auto_20190429_1719'),
    ]

    operations = [
        migrations.AlterField(
            model_name='identifier',
            name='source',
            field=models.CharField(choices=[(0, 'Aurora'), (1, 'Archivematica'), (2, 'Fedora'), (3, 'ArchivesSpace'), (4, 'Pisces'), (5, 'Cartographer'), (6, 'Wikidata'), (7, 'Wikipedia')], max_length=100),
        ),
        migrations.AlterField(
            model_name='sourcedata',
            name='source',
            field=models.CharField(choices=[(0, 'Aurora'), (1, 'Archivematica'), (2, 'Fedora'), (3, 'ArchivesSpace'), (4, 'Cartographer'), (5, 'Wikidata'), (6, 'Wikipedia')], max_length=100),
        ),
        migrations.AlterField(
            model_name='transformrun',
            name='source',
            field=models.CharField(choices=[(0, 'Aurora'), (1, 'Archivematica'), (2, 'Fedora'), (3, 'ArchivesSpace'), (4, 'Pisces'), (5, 'Cartographer'), (6, 'Trees'), (7, 'Wikidata'), (8, 'Wikipedia')], max_length=100),
        ),
    ]
