import urllib

from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth import authenticate

#First step of process, redirects user to Facebook, which redirects back to authentication_callback.
def login(request):
    args = {
        'client_id': settings.FACEBOOK_APP_ID,
        'scope': settings.FACEBOOK_SCOPE,
        'redirect_uri': request.build_absolute_uri('/facebook/authentication_callback'),
        }
 
    # call facebook with the above settings; expect to receive http response with the access code as a GET parameter
    return HttpResponseRedirect('https://www.facebook.com/dialog/oauth?'
                                                    + urllib.urlencode(args))
    
#Second step of the login process. It reads in a code from Facebook, then redirects back to the home page.
def authentication_callback(request):

    code = request.GET.get('code')
    # call the django authentication middleware function
    user = authenticate(token=code, request=request)
    if user!=None:
        auth_login(request, user)
    #RETURN back to home directory
    return HttpResponseRedirect('/')