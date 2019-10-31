# Generated by Django 2.2.6 on 2019-10-27 02:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Platform_File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(max_length=100)),
                ('platform_file', models.FileField(upload_to='')),
                ('created', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity', models.CharField(max_length=100)),
                ('list_of_vars', models.TextField(blank=True, null=True)),
                ('AEM', models.FileField(upload_to='')),
                ('NONAEM', models.FileField(upload_to='')),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='regression.Platform_File')),
            ],
        ),
    ]
