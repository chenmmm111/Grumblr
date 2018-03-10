# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(default = 0, blank=True)
    short_bio = models.CharField(max_length=420, default='', blank=True)
    image = models.ImageField(upload_to='profile_img', default = 'default-img.png', blank=True)
    following = models.ManyToManyField('self', related_name='follows', symmetrical=False)

    def __unicode__(self):
        return self.user.username

class Post(models.Model):
    # Built-in User model is the foreign key in Post model
    user_profile = models.ForeignKey(UserProfile)
    body = models.CharField(max_length=42)
    date = models.DateTimeField()

    def __unicode__(self):
        return self.body

class Comment(models.Model):
    author_user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=False)
    comment = models.CharField(max_length=42, blank=False)
    time = models.DateTimeField()

    def __unicode__(self):
        return self.comment
