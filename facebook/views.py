import urllib

from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth import authenticate
from crush.utils_email import send_mail_user_logged_in
import thread

#First step of process, redirects user to Facebook, which redirects back to authentication_callback.
def login(request,next_page="",next_page_param=""):
    # if user tries to access a page when not logged in, we'll get a next Get parameter.  add it as a parameter to the fb redirect URI so we can redirect later
    if next_page != "":
        next_page = "/" + next_page + "/"
    if next_page_param != "":
        next_page += next_page_param + "/"
    redirect_uri = request.build_absolute_uri('/facebook/authentication_callback' + next_page)
    redirect_uri=redirect_uri.replace('https','http')
    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'scope': settings.FACEBOOK_SCOPE,
        'redirect_uri': redirect_uri,
        }
    # call facebook with the above settings; expect to receive http response with the access code as a GET parameter
    return HttpResponseRedirect('https://www.facebook.com/dialog/oauth?'
                                                   + urllib.urlencode(args))
    
    
#Second step of the login process. It reads in a code from Facebook, then redirects back to the home page.
def authentication_callback(request,next_page="",next_page_param=""):
    if next_page!="":
        next_page = "/" + next_page + "/"
    if next_page_param != "":
        next_page += next_page_param + "/"
    code = request.GET.get('code')
    # call the django authentication middleware function
    user = authenticate(token=code, request=request,next_page=next_page)
    if user!=None:
        auth_login(request, user)
        thread.start_new_thread(send_mail_user_logged_in,(user,str(request.META)))
    #RETURN back to home directory
    if next_page =="":
        return HttpResponseRedirect('/home/?signin=true')
    else:
        return HttpResponseRedirect(next_page + "?signin=true")