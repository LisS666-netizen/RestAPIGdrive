# Generated by Django 3.0.6 on 2020-10-01 06:53

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('GetLink', '0010_auto_20201001_0645'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fileobject',
            old_name='stotedFileId',
            new_name='storedFileId',
        ),
    ]
