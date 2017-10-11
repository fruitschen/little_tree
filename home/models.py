# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from django.db import models

from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailsearch import index

from modelcluster.fields import ParentalKey


# Gallery images


class GalleryImage(models.Model):
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    caption = models.CharField(max_length=255, blank=True)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
    ]

    api_fields = ['image', 'caption']

    class Meta:
        abstract = True


# Home Page


class HomePageGalleryImage(Orderable, GalleryImage):
    page = ParentalKey('HomePage', related_name='gallery_images')


class HomePage(Page):
    body = RichTextField(blank=True)
    search_fields = Page.search_fields + [
        index.SearchField('body'),
    ]

    api_fields = ['body', 'gallery_images', ]

    class Meta:
        verbose_name = u'主页'


HomePage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('body'),
    InlinePanel('gallery_images', label="Gallery images"),
]

HomePage.promote_panels = Page.promote_panels


# Category Page


class CategoryPage(Page):
    intro = RichTextField(blank=True)
    thumbnail = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    api_fields = ['intro', 'thumbnail']

    class Meta:
        verbose_name = u'分类页面'


CategoryPage.content_panels = [
    FieldPanel('title', classname="full title"),
    ImageChooserPanel('thumbnail'),
    FieldPanel('intro', classname="full"),
]


# Simple Page


class SimplePage(Page):
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    api_fields = ['intro', 'body', ]

    class Meta:
        verbose_name = u'简单页面'


SimplePage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
]


# Gallery page


class GalleryPageGalleryImage(Orderable, GalleryImage):
    page = ParentalKey('GalleryPage', related_name='gallery_images')


class GalleryPage(Page):
    intro = RichTextField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('title'),
        index.SearchField('intro'),
    ]

    api_fields = ['intro', ]

    class Meta:
        verbose_name = u'图片页面'


GalleryPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel('gallery_images', label="Gallery images"),
]

