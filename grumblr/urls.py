from django.conf.urls import url
from django.contrib.auth.views import (LoginView, LogoutView)
from django.urls import reverse_lazy
from .views import (index,globalstream,profile,register,post,activate,resend_activate_email,follow,unfollow,following_page,reset_password,edit_profile,get_photo,reset_password_form,get_global_posts,comment,check_max_id,get_new_max_id,get_comment_count)


urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^global-stream', globalstream,name='globalstream'),
    url(r'^user/(?P<user_id>\d+)$', profile, name='profile'),
    # route to the built-in authentication
    url(r'^login$', LoginView.as_view(redirect_authenticated_user=True,template_name='grumblr/login.html'), name='login'),
    url(r'^logout$', LogoutView.as_view(next_page=reverse_lazy('login')), name='logout'),
    url(r'^register$', register, name='register'),
    # route to post action when users click on post button in globalstream, it is get method, not adding $ at the end
    url(r'^post', post, name='post'),
    # token and uidb64 required to verify the identity of the user
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', activate, name='activate'),
    url(r'^activate/resend/(?P<id>\d+)$', resend_activate_email, name='resend_activate_email'),
    # process following
    url(r'^follow/(?P<follow_id>\d+)$', follow, name='follow'),
    url(r'^unfollow/(?P<unfollow_id>\d+)$',unfollow, name='unfollow'),
    url(r'^following/$', following_page, name='following_page'),
    # route to password reset views
    url(r'^reset_password/$', reset_password, name='reset_password'),
    url(r'^reset_password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', reset_password_form, name='reset_password_form'),
    # find password
    # url(r'^find_password/$', reset_password, name="find_password"),
    # url(r'^find_password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', find_password_form, name='find_password_form'),
    #route to edit profile
    url(r'^edit-profile/$', edit_profile, name='edit_profile'),
    url(r'^photo/(?P<id>\d+)$', get_photo, name='photo'),
    # get json objects in JS
    url(r'^comment/comment-form-(?P<id>[0-9]+)$', comment, name="comment"),
    url(r'^check_id/(?P<max_id>[0-9]+)$', check_max_id, name="check_max_id"),
    url(r'^get_max_id/$', get_new_max_id, name="get_new_max_id"),
    url(r'^get_comment_count/(?P<id>[0-9]+)$', get_comment_count, name="get_comment_count"),
]