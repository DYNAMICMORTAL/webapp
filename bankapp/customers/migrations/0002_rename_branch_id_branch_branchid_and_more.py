# Generated by Django 5.1.6 on 2025-03-06 19:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='branch',
            old_name='branch_id',
            new_name='BranchID',
        ),
        migrations.RenameField(
            model_name='branch',
            old_name='branch_name',
            new_name='BranchName',
        ),
        migrations.RemoveField(
            model_name='branch',
            name='ifsc_code',
        ),
        migrations.AddField(
            model_name='branch',
            name='City',
            field=models.CharField(default='Unknown', max_length=100),
        ),
        migrations.AddField(
            model_name='branch',
            name='State',
            field=models.CharField(default='Unknown', max_length=100),
        ),
        migrations.AddField(
            model_name='branch',
            name='IFSC_Code',
            field=models.CharField(default='TEMP0000000', max_length=20, unique=True),
        ),
    ]
