# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-21 01:06
from __future__ import unicode_literals

from django.db import migrations
import wagtail.wagtailcore.blocks
import wagtail.wagtailcore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_simplepage_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='simplepage',
            name='extra_body',
            field=wagtail.wagtailcore.fields.StreamField([(b'paragraph', wagtail.wagtailcore.blocks.RichTextBlock(icon='pilcrow')), (b'html', wagtail.wagtailcore.blocks.RawHTMLBlock(icon='code', label='Raw HTML'))], blank=True, default=''),
        ),
    ]
