# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.urlresolvers import reverse, resolve


from mimetypes import guess_type


from models import Post, UserProfile, Comment
from forms import RegitrationForm, PasswordResetForm, AnonymousUserForm, UserProfileForm, UserForm, ProfilePageForm, PostForm, CommentForm
import datetime



def index(request):
    return redirect(reverse('globalstream'))


@transaction.atomic
def register(request):
    if request.user.is_authenticated:
        return redirect(reverse('globalstream'))
    # create an unbound form initially
    context={'form': RegitrationForm()}

    # If it is a get request, directly return an unbound registration form
    if request.method == 'GET':
        return render(request, 'grumblr/registration.html', context)

    # Create a bound form using inputs from POST request
    form = RegitrationForm(request.POST)
    context['form'] = form

    # If the form parameters are invalid, return the error form and do not register
    if not form.is_valid():
        return render(request, 'grumblr/registration.html', context)

    # If the parameters are valid, create and save a new user and save the form
    new_user = form.save(commit=False)
    # Before the email address is verified, set the user as an inactive account
    new_user.is_active = False
    new_user.save()

    # initialize new profile for new user
    user_profile = UserProfile.objects.create(user = new_user)
    # Email message content (generate a token in the activation link)
    token = default_token_generator.make_token(new_user)
    uid = urlsafe_base64_encode(force_bytes(new_user.pk))

    # send email
    mail_subject = 'Grumblr Sign Up Confirmation'
    mail_message = render_to_string('grumblr/activation/email_activation.html',{'user':new_user,'domain':get_current_site(request).domain,'uid':uid,'token':token})
    from_email = settings.EMAIL_HOST_USER
    to_list = [form.cleaned_data.get('email')] #email address like xxx@andrew.cmu
    send_mail(mail_subject, mail_message, from_email, to_list, fail_silently=True)

    return render(request, 'grumblr/activation/email_activate_done.html',{'id': new_user.id})

@transaction.atomic
def resend_activate_email(request, id):
    if request.user.is_authenticated:
        return HttpResponse("You've already activate your account.")
    user = get_object_or_404(User, id=id)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.id))
    mail_message = render_to_string('grumblr/activation/email_activation.html',
                                    {'user': user, 'domain': get_current_site(request).domain, 'uid': uid,
                                     'token': token})
    mail_subject = 'Grumblr Sign Up Confirmation'
    from_email = settings.EMAIL_HOST_USER
    to_list = [user.email]
    send_mail(mail_subject, mail_message, from_email, to_list, fail_silently=True)

    return render(request, 'grumblr/activation/email_activate_done.html',{'id':user.id})


@transaction.atomic
def activate(request, uidb64, token):
    context = {'validlink':False}
    try:
        # decode the uid in the url
        uid = force_text(urlsafe_base64_decode(uidb64))
        new_user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        new_user = None

    if not new_user or not default_token_generator.check_token(new_user, token):
        return render(request, 'grumblr/activation/email_activate_confirm.html', context)
    # if there is no exception and the token is the same as we calculated, the new user activated its account
    context['validlink'] = True
    new_user.is_active = True
    new_user.save()

    # For newly registrated users, auto login
    #new_user = authenticate(username=new_user['username'], password=new_user['password'])
    login(request, new_user)
    return render(request, 'grumblr/activation/email_activate_confirm.html', context)


@login_required
def post(request):
    if request.method == "POST":
        return HttpResponseRedirect('/grumblr/global-stream')
    context = {}
    # get the userprofile object of current user
    user_profile = get_object_or_404(UserProfile, user=request.user)
    # mutable = request.GET._mutable
    # request.GET._mutable = True
    # request.GET['date'] = datetime.datetime.now()
    # request.GET['user_profile'] = user_profile
    # request.GET._mutable = mutable
    new_post = Post.objects.create(user_profile=user_profile, date=datetime.datetime.now())
    post_form = PostForm(request.GET, instance=new_post)
    context['post_form'] = post_form

    if not post_form.is_valid():
        messages.error(request, 'Failed to update a post...')
        return HttpResponseRedirect('/grumblr/global-stream')
    post = post_form.save()
    print(Post.objects.all())
    print("post!!")
    messages.success(request, 'You have successfully update a post!')
    return HttpResponseRedirect('/grumblr/global-stream')


@login_required
def profile(request, user_id):

    errors=[]
    post_list = []
    comment_list = []
    following = False
    try:
        search_user = User.objects.get(id=user_id)
    except ObjectDoesNotExist:
        errors.append('The user does not exist.')
        return render(request, 'grumblr/profile.html', {"current_user": request.user, "errors": errors})
    # process user profile
    user_profile = get_object_or_404(UserProfile, user__id=user_id)
    current_profile = get_object_or_404(UserProfile, user=request.user)
    profile_form = ProfilePageForm(instance=user_profile)
    # process user info
    user_form=UserForm(instance=search_user)
    comment_form = CommentForm()

    # process follow relationship
    if user_id != request.user.id and user_profile in current_profile.following.all():
        following = True
    # if the user exists, filter posts he/she posted
    post_list = Post.objects.filter(user_profile__user__id=user_id).order_by("-date")
    if not post_list:
        errors.append("This user does not post any content.")

    for post in post_list:
        post.count = Comment.objects.filter(post=post).count()
        # get comments by each post
        comment_list = Comment.objects.filter(post=post).order_by("time")
        setattr(post, 'comment_list', comment_list)

    # get the latest post with max id
    max_id = 0
    if Post.objects.count() > 0:
        max_id = Post.objects.all().order_by("-id")[0].id

    return render(request, 'grumblr/profile.html', {"object_list":post_list, "search_user":search_user, "current_user":request.user, "errors":errors,'profile_form':profile_form,'user_profile':user_profile, 'following':following, 'user_form':user_form, 'comment_list':comment_list,"max_id":max_id, 'comment_form':comment_form})

@login_required
def globalstream(request):

    errors=[]
    # get all the posts in the global stream by reverse-chronological order
    post_list = Post.objects.all().order_by("-date")
    # create a bound form for updating a post
    post_form = PostForm()
    # create comment forms for each post
    comment_form = CommentForm()

    if not post_list:
        errors.append("There are not any posts in Grumblr.")

    for post in post_list:
        post.count = Comment.objects.filter(post=post).count()
        # get comments by each post
        comment_list = Comment.objects.filter(post=post).order_by("time")
        setattr(post, 'comment_list', comment_list)

    # get the latest post with max id
    max_id=0;
    if Post.objects.all():
        max_id = Post.objects.all().order_by("-id")[0].id

    return render(request, 'grumblr/globalstream.html',  {"object_list":post_list, "current_user":request.user, "errors":errors, "post_form":post_form, "max_id":max_id, "comment_form":comment_form})



@transaction.atomic
def reset_password(request):
    user = request.user

    context = {'user':user}
    # url=resolve(request.path_info).url_name

    if request.method == 'GET' and not user.is_authenticated:
        context['form'] = AnonymousUserForm()
        return render(request, 'grumblr/password_reset/password_reset.html', context)
    if request.method == 'GET' and user.is_authenticated and not user.email:
        return render(request, 'grumblr/password_reset/password_reset.html', context)
    if request.method == 'POST' and not user.is_authenticated:
        form = AnonymousUserForm(request.POST)
        context['form'] = form
        # Validates the form.
        if not form.is_valid():
            return render(request, 'grumblr/password_reset/password_reset.html', context)
        else:
            user = User.objects.get(username = form.cleaned_data['username'])
            context['user'] = user

    # Email message content (generate a token in the password reset link)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # if url == 'reset_password':
    mail_message = render_to_string('grumblr/password_reset/password_reset_email.html',
                                        {'user': user, 'domain': get_current_site(request).domain, 'uid': uid,
                                         'token': token})
    # else:
    #     mail_message = render_to_string('grumblr/password_reset/password_find_email.html',
    #                                     {'user': user, 'domain': get_current_site(request).domain, 'uid': uid,
    #                                      'token': token})
    mail_subject = 'Reset your password in Grumblr'
    from_email = settings.EMAIL_HOST_USER
    to_list = [user.email]
    send_mail(mail_subject, mail_message, from_email, to_list, fail_silently=True)


    return render(request, 'grumblr/password_reset/password_reset.html', context)

@transaction.atomic
def reset_password_form(request, uidb64, token):
    context = {'validlink': False}
    try:
        # decode the uid in the url
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and default_token_generator.check_token(user, token):
        context['validlink'] = True
    if request.method == 'GET':
        if context['validlink'] == False:
            return render(request, 'grumblr/password_reset/password_reset_form.html', context)
        # if there is no exception and the token is the same as we calculated, render password reset form
        context['form'] = PasswordResetForm()
        # context['form'] = PasswordResetForm(initial={'username':user.username})
        return render(request, 'grumblr/password_reset/password_reset_form.html', context)
    # if user post their new passwords

    form = PasswordResetForm(request.POST)
    # form.fields["username"].initial = user.username
    context['form'] = form

    # Validates the form.
    if not form.is_valid():
        return render(request, 'grumblr/password_reset/password_reset_form.html', context)
    # reset password
    user.set_password(form.cleaned_data['new_password'])
    # set the user to be active
    user.is_active = True
    # save it
    user.save()
    return render(request, 'grumblr/password_reset/password_reset_complete.html')




@login_required
@transaction.atomic
def edit_profile(request):
    context={}
    user = request.user
    context['current_user'] = user
    if(request.method == 'GET'):
        # get the model object from User model, and generate a bound ModelForm
        user_form = UserForm(instance=user)
        # get the model object from UserProfile model
        user_profile = get_object_or_404(UserProfile, user=user)
        # generate a bound ModelForm
        profile_form=UserProfileForm(instance=user_profile)
        # return two forms as the response
        context['user_form'] = user_form
        context['profile_form']=profile_form
        context['id'] = user_profile.id
        context['user_id'] = user.id
        return render(request, 'grumblr/profile_edit.html', context)
    # If user is trying to edit the profile
    # generate new form according to POST inputs
    user_form = UserForm(request.POST, instance = user)
    # get the profile object of the user
    new_profile = get_object_or_404(UserProfile, user=user)
    # update the fields according to POST inputs
    profile_form = UserProfileForm(request.POST,request.FILES, instance = new_profile)
    context['user_form'] = user_form
    context['profile_form'] = profile_form
    if user_form.is_valid() and profile_form.is_valid():
        user = user_form.save()
        profile = profile_form.save()
        context['id'] = profile.id
        context['user_id'] = user.id
        messages.success(request, 'Your profile has been saved.')

    return render(request, 'grumblr/profile_edit.html', context)

@login_required
def get_photo(request, id):
    # use the the item id as the picture id
    profile = get_object_or_404(UserProfile, id=id)
    if not profile.image:
        raise Http404
    content_type = guess_type(profile.image.name, strict=True)
    return HttpResponse(profile.image, content_type=content_type)

@login_required
def follow(request, follow_id):
    from_user_profile = get_object_or_404(UserProfile, user=request.user)
    to_user_profile = get_object_or_404(UserProfile, user__id=follow_id)
    from_user_profile.following.add(to_user_profile)
    from_user_profile.save()

    return HttpResponseRedirect(reverse('profile',args=(follow_id,)))

@login_required
def unfollow(request, unfollow_id):
    from_user_profile = get_object_or_404(UserProfile, user=request.user)
    to_user_profile = get_object_or_404(UserProfile, user__id=unfollow_id)
    from_user_profile.following.remove(to_user_profile)
    from_user_profile.save()
    return HttpResponseRedirect(reverse('profile',args=(unfollow_id,)))

@login_required
def following_page(request):
    current_user_profile = get_object_or_404(UserProfile, user=request.user)
    errors = []
    comment_list = []
    # query all posts that are posted by users in the current user's following list
    post_list = Post.objects.filter(user_profile__in = current_user_profile.following.all()).order_by("-date")
    # create comment forms for each post
    comment_form = CommentForm()
    if not post_list:
        errors.append("There are not any posts in the following list.")

    for post in post_list:
        post.count = Comment.objects.filter(post=post).count()
        # get comments by each post
        comment_list = Comment.objects.filter(post=post).order_by("time")
        setattr(post, 'comment_list', comment_list)

    # get the latest post with max id
    max_id = 0
    if Post.objects.count() > 0:
        max_id = Post.objects.all().order_by("-id")[0].id

    return render(request, 'grumblr/following_stream.html',
                  {"object_list": post_list, "current_user": request.user, "errors": errors, 'comment_list':comment_list, "max_id":max_id,'comment_form':comment_form})

@login_required
def get_global_posts(request):
    errors=[]
    posts = []
    # get all the posts in the global stream by reverse-chronological order
    post_list = Post.objects.all().order_by("-date")
    if not post_list:
        errors.append("There are not any posts in the following list.")
    context = {'posts':post_list, 'errors':errors}
    return render(request, 'grumblr/posts.json', context, content_type='application/json')
    # posts_json = serializers.serialize('json', posts)
    # return HttpResponse(posts_json, content_type='application/json')

@login_required
def comment(request, id):
    print("enter!!!")
    context = {}
    print(Post.objects.all())
    print("comment!!")
    post = get_object_or_404(Post, id=id)
    if(not post):

        context['error'] = 'The post does not exist.'
        return render(request, 'grumblr/comments.json', context, content_type='application/json')

    new_comment = Comment.objects.create(author_user_profile=get_object_or_404(UserProfile, user=request.user), time=datetime.datetime.now(), post=post)
    comment_form = CommentForm(request.POST, instance=new_comment)
    if not comment_form.is_valid():
        context['error'] = 'The comment is invalid.'
        return render(request, 'grumblr/comments.json', context, content_type='application/json')
    new_comment = comment_form.save()
    context['comment'] = new_comment
    return render(request, 'grumblr/comment.html', context)

@login_required
def check_max_id(request, max_id):
    new_posts = Post.objects.filter(id__gt=max_id)

    for post in new_posts:
        post.comment_form = CommentForm()
        post.count = Comment.objects.filter(post=post).count()
        post.comment_list = Comment.objects.filter(post=post).order_by("time")
    context = {'posts': new_posts}
    
    return render(request, 'grumblr/new_post.html', context)

@login_required
def get_new_max_id(request):
    new_max_id = 0
    if Post.objects.count() > 0:
        new_max_id = Post.objects.all().order_by("-id")[0].id
    return render(request, 'grumblr/max_id.json', {"new_max_id": new_max_id}, content_type='application/json')

@login_required
def get_comment_count(request,id):
    count = Comment.objects.filter(post__id=id).count()
    return render(request, 'grumblr/count.json', {"count": count}, content_type='application/json')


# @transaction.atomic
# def find_password_form(request, uidb64, token):
#     context = {'validlink': False}
#     try:
#         # decode the uid in the url
#         uid = force_text(urlsafe_base64_decode(uidb64))
#         user = User.objects.get(pk=uid)
#     except(TypeError, ValueError, OverflowError, User.DoesNotExist):
#         user = None
#     if user and default_token_generator.check_token(user, token):
#         context['validlink'] = True
#     if request.method == 'GET':
#         if context['validlink'] == False:
#             return render(request, 'grumblr/password_reset/password_reset_form.html', context)
#         # if there is no exception and the token is the same as we calculated, render password reset form
#         context['form'] = PasswordFindForm()
#         return render(request, 'grumblr/password_reset/password_reset_form.html', context)
#     # if user post their new passwords
#
#     form = PasswordFindForm(request.POST)
#     context['form'] = form
#
#     # Validates the form.
#     if not form.is_valid():
#         return render(request, 'grumblr/password_reset/password_reset_form.html', context)
#     # reset password
#     user.set_password(form.cleaned_data['new_password'])
#     # save it
#     user.save()
#     return render(request, 'grumblr/password_reset/password_reset_complete.html')