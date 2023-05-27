# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from mdeditor.fields import MDTextField
from django.core.exceptions import ValidationError

# Create your models here.

class Tag(models.Model):
    tag_name = models.CharField('标签名称', max_length=30)

    def __str__(self):
        return self.tag_name


class Article(models.Model):
    title = models.CharField(max_length=200)  # 博客标题
    category = models.ForeignKey('Category', verbose_name='文章类型', on_delete=models.CASCADE)
    #category = MDTextField()
    date_time = models.DateField(auto_now_add=True)  # 博客日期
    #content = models.TextField(blank=True, null=True)  # 文章正文
    content = MDTextField()
    digest = models.TextField(blank=True, null=True)  # 文章摘要
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='作者', on_delete=models.CASCADE)
    view = models.BigIntegerField(default=0)  # 阅读数
    comment = models.BigIntegerField(default=0)  # 评论数
    picture = models.CharField(max_length=200)  # 标题图片地址
    tag = models.ManyToManyField(Tag)  # 标签

    def __str__(self):
        return self.title

    def sourceUrl(self):
        source_url = settings.HOST + '/blog/detail/{id}'.format(id=self.pk)
        return source_url  # 给网易云跟帖使用

    def viewed(self):
        """
        增加阅读数
        :return:
        """
        self.view += 1
        self.save(update_fields=['view'])

    def commenced(self):
        """
        增加评论数
        :return:
        """
        self.comment += 1
        self.save(update_fields=['comment'])

    class Meta:  # 按时间降序
        ordering = ['-date_time']


class Category(models.Model):
    name = models.CharField('文章类型', max_length=30)
    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_mod_time = models.DateTimeField('修改时间', auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "文章类型"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Comment(models.Model):
    title = models.CharField("标题", max_length=100)
    source_id = models.CharField('文章id或source名称', max_length=25)
    create_time = models.DateTimeField('评论时间', auto_now=True)
    user_name = models.CharField('评论用户', max_length=25)
    url = models.CharField('链接', max_length=100)
    comment = models.CharField('评论内容', max_length=500)


class Country(models.Model):
    name = models.CharField(max_length=30)


class City(models.Model):
    name = models.CharField(max_length=30)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    population = models.PositiveIntegerField()


class Visitor(models.Model):
    ts = models.CharField(max_length=30)
    type = models.CharField(max_length=30)
    user = models.CharField(max_length=30)
    ip = models.CharField(max_length=30)
    country_code = models.CharField(max_length=30)
    province = models.CharField(max_length=30)
    city = models.CharField(max_length=30)
    level = models.CharField(max_length=30)
    info = models.CharField(max_length=100)



from django import forms


class MY_CHOICES(models.Model):
    choice = models.CharField(max_length=154, unique=True)


def blocked_content_validator(value):
    blocked_words = ['https', 'http', 'investment', 'target', 'increase']  # Add the blocked words or content here
    for word in blocked_words:
        if word.lower() in value.lower():
            raise ValidationError(f"The message contains blocked content: {word}")


class Contact(models.Model):
    GUEST_NUM_CHOICES = (
        ("1", "1"),
        ("2", "2"),
        ("3", "3"),
        ("4", "4"),
        ("5", "5"),
        ("6", "6")

    )
    EVENT_TYPE_CHOICES = (
        ("1", "party/feest"),
        ("2", "ceremony/ceremonie"),
        ("3", "ceremony and party/ ceremonie en feest"),
        ("4", "Can't join/ Kan niet meedoen"),

    )
    name = models.CharField(max_length=255)
    email = models.EmailField(default='youremail@gmail.com')
    phone = models.CharField(max_length=255)
    event_type = models.CharField(max_length=255,
                                  choices=EVENT_TYPE_CHOICES,
                                  #name='event type (for ceremony max=30 persons))',
                                  db_column='event_type',
                                  default='party'
                                  )

    message = models.TextField(default='Hey Lisanne and Fei i will join....', validators=[blocked_content_validator])
    #print(message) # <django.db.models.fields.TextField>

    guest_num = models.CharField(max_length=255,
                                 choices=GUEST_NUM_CHOICES,
                                 default='1',
                                 db_column='guest_num'
                                 #name='guest_num<Aantal Gasten>(include kids)')
                                 )
    created_at = models.DateTimeField(auto_now_add=True)

    """
    def __str__(self):
        return  'email: ' + self.email + ' name: ' + self.name + ' phone: ' + self.phone + ' event_type:' + self.event_type + ' message: ' + self.message + ' guest_num: ' + self.guest_num
    """


