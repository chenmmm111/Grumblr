# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import forms
from django.contrib.auth.models import User
from models import UserProfile, Comment, Post
from django.shortcuts import get_object_or_404
class RegitrationForm(forms.ModelForm):

    password_confirm=forms.CharField(widget=forms.PasswordInput())


    class Meta:
        model=User
        fields=('username','first_name','last_name','email','password',)
        widgets={'password':forms.PasswordInput()}

    # if we don't override save() method, the password will be saved as plain_text, thus there will be Anonymous user without _mata exception.
    # To solve this problem, override the save() function to use set_password(plain_text).
    def save(self, commit=True):
        user = super(RegitrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email):
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if(password and password_confirm and password != password_confirm):
            raise forms.ValidationError("Passwords does not match.")
        return password_confirm

class PasswordResetForm(forms.Form):
    #username = forms.CharField(widget = forms.TextInput(attrs={'readonly':'readonly'}))
    # old_password = forms.CharField(widget=forms.PasswordInput())
    new_password = forms.CharField(widget=forms.PasswordInput())
    new_password_confirm = forms.CharField(widget=forms.PasswordInput())

    # def clean_old_password(self):
    #     old_password = self.cleaned_data.get('old_password')
    #     username = self.cleaned_data.get('username')
    #     user = get_object_or_404(User, username=username)
    #     if not user.check_password(old_password):
    #         raise forms.ValidationError("Old password does not match.")
    #     return old_password

    def clean_new_password_confirm(self):
        password = self.cleaned_data.get('new_password')
        password_confirm = self.cleaned_data.get('new_password_confirm')
        if (password and password_confirm and password != password_confirm):
            raise forms.ValidationError("New passwords do not match.")
        return password_confirm


# class PasswordFindForm(PasswordResetForm):
#     def __init__(self, *args, **kwargs):
#         super(PasswordFindForm, self).__init__(*args, **kwargs)
#         self.fields.pop('username')
#         self.fields.pop('old_password')


class AnonymousUserForm(forms.Form):
    username = forms.CharField()

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not User.objects.filter(username=username):
            raise forms.ValidationError("We don't have such a username in our database.")
        return username

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user','following')
        widgets = {'image' : forms.FileInput()}

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username','email','first_name', 'last_name',)
        widgets = {'username':forms.TextInput(attrs={'readonly':'readonly'}), 'email':forms.TextInput(attrs={'readonly':'readonly'})}

class ProfilePageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = {'user','following', 'image',}

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('body',)
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
        }
    def clean_body(self):
        body = self.cleaned_data.get('body')
        if (not body or len(body) == 0):
            raise forms.ValidationError("We didn't receive any content from your post.")
        if (len(body) > 42):
            raise forms.ValidationError("The maximum length of your post is 42. Your characters: " + str(len(body)));
        return body

    # def clean(self):
    #     cleaned_data = super(PostForm, self).clean()
    #     print(cleaned_data)
    #     body = cleaned_data.get('body')
    #     if(not body or len(body)==0):
    #         raise forms.ValidationError("We didn't receive any content from your post.")
    #     if(len(body)>42):
    #         raise forms.ValidationError("The maximum length of your post is 42. Your characters: " + str(len(body)));
    #     return cleaned_data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('comment',)
        widgets = {
            'comment' : forms.Textarea(attrs={'class': 'form-control', 'rows': '2'}),
        }
    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        if (not comment or len(comment) == 0):
            raise forms.ValidationError("We didn't receive any content from your comment.")
        if (len(comment) > 42):
            raise forms.ValidationError("The maximum length of your comment is 42. Your characters: " + str(len(comment)));
        return comment





