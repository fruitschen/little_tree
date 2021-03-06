# -*- coding: UTF-8 -*-
from __future__ import unicode_literals
from datetime import datetime
from PIL import Image as PILImage
from PIL import ExifTags

from django.db import models
from django.db.models.signals import post_save

from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailcore.fields import RichTextField, StreamField
from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel, StreamFieldPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailsearch import index
from wagtail.wagtailimages.models import Image as WagtailImage
from wagtail.wagtailcore.blocks import TextBlock, StructBlock, StreamBlock, FieldBlock, CharBlock, RichTextBlock, RawHTMLBlock

from modelcluster.fields import ParentalKey


# Stream Field


class CustomStreamBlock(StreamBlock):
    paragraph = RichTextBlock(icon="pilcrow")
    html = RawHTMLBlock(icon="code", label='Raw HTML')


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

    subpage_types = ['CategoryPage']
    parent_page_types = []

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

    subpage_types = ['GalleryPage', 'SimplePage']

    def get_template(self, request):
        if self.get_children().live().filter(gallerypage__isnull=False).exists():
            return 'home/category_page.html'
        else:
            return 'home/category_page_simple.html'

    @property
    def sub_pages(self):
        return self.get_children().live().order_by('-first_published_at')

    class Meta:
        verbose_name = u'分类页面'


CategoryPage.content_panels = [
    FieldPanel('title', classname="full title"),
    ImageChooserPanel('thumbnail'),
    FieldPanel('intro', classname="full"),
]


# Base Details Page


class BaseDetailsPage(Page):

    def get_prev(self):
        query = self.get_siblings().live().filter(first_published_at__lt=self.first_published_at)
        if query.exists():
            return query.order_by('-first_published_at')[0]

    def get_next(self):
        query = self.get_siblings().live().filter(first_published_at__gt=self.first_published_at)
        if query.exists():
            return query.order_by('first_published_at')[0]

    class Meta:
        abstract = True


# Simple Page


class SimplePage(BaseDetailsPage):
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)
    extra_body = StreamField(
        CustomStreamBlock,
        blank=True, default=''
    )

    thumbnail = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    timestamp = models.DateTimeField(
        verbose_name=u'时间',
        blank=True,
        null=True
    )

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    api_fields = ['intro', 'body', 'thumbnail', ]
    subpage_types = []

    def save(self, *args, **kwargs):
        result = super(SimplePage, self).save(*args, **kwargs)
        if self.first_published_at and self.timestamp and self.first_published_at > self.timestamp:
            self.first_published_at = self.timestamp
            self.save()

    class Meta:
        verbose_name = u'简单页面'


SimplePage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('timestamp'),
    ImageChooserPanel('thumbnail'),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    StreamFieldPanel('extra_body'),
]


# Gallery page


class GalleryPageGalleryImage(Orderable, GalleryImage):
    page = ParentalKey('GalleryPage', related_name='gallery_images')


class GalleryPage(BaseDetailsPage):
    intro = RichTextField(blank=True)
    timestamp = models.DateTimeField(
        verbose_name=u'时间',
        blank=True,
        null=True
    )

    search_fields = Page.search_fields + [
        index.SearchField('title'),
        index.SearchField('intro'),
    ]

    api_fields = ['intro', ]
    subpage_types = []

    @property
    def thumbnail(self):
        if self.id and self.gallery_images.all():
            return self.gallery_images.all()[0].image

    def save(self, *args, **kwargs):
        result = super(GalleryPage, self).save(*args, **kwargs)
        if not self.timestamp:
            thumbnail = self.thumbnail
            if thumbnail:
                filename = thumbnail.filename.lower()
                if 'img_' in filename:
                    time_str = filename.replace('img_', '').replace('.jpg', '')
                    time_str = time_str[:17]
                    timestmap = datetime.strptime(time_str, '%Y-%m-%d-%H%M%S')
                    self.timestamp = timestmap
                    self.save()

        if self.first_published_at and self.timestamp and self.first_published_at > self.timestamp:
            self.first_published_at = self.timestamp
            self.save()


    class Meta:
        verbose_name = u'图片页面'


GalleryPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('timestamp'),
    FieldPanel('intro', classname="full"),
    InlinePanel('gallery_images', label="Gallery images"),
]


for orientation in ExifTags.TAGS.keys():
    if ExifTags.TAGS[orientation] == 'Orientation': break


def resize_image(path):
    max_width = 1080
    img = PILImage.open(path)
    if hasattr(img, '_getexif'):
        # we need to rotate the image based on exif info.
        # https://stackoverflow.com/questions/4228530/pil-thumbnail-is-rotating-my-image
        exif = img._getexif()
        if not exif:
            return
        exif = dict(img._getexif().items())
        if exif[orientation] == 3:
            img = img.rotate(180, expand=True)
        elif exif[orientation] == 6:
            img = img.rotate(270, expand=True)
        elif exif[orientation] == 8:
            img = img.rotate(90, expand=True)
    original_width, original_height = img.size
    if original_width < max_width:  # no need to resize
        return
    width_percent = (max_width / float(original_width))
    new_height = int((float(original_height) * float(width_percent)))
    img = img.resize((max_width, new_height), PILImage.ANTIALIAS)
    img.save(path)


def image_post_save(sender, instance, **kwargs):
    image_path = instance.file.path
    resize_image(image_path)

post_save.connect(image_post_save, sender=WagtailImage)
