# Generated by Django 5.1.7 on 2025-03-29 17:45

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSocialAuth',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(choices=[('google', 'Google')], default='google', max_length=20)),
                ('provider_user_id', models.CharField(max_length=255)),
                ('provider_email', models.EmailField(max_length=254)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_auths', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'user social auth',
                'verbose_name_plural': 'user social auths',
                'unique_together': {('provider', 'provider_user_id')},
            },
        ),
    ]
