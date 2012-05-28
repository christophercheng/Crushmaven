import urllib, json, urlparse
from django.conf import settings
from django.contrib.auth.models import User
#from django.core.urlresolvers import reverse CHC - reverse gives me problems

from crush.models import UserProfile

class FacebookBackend:

    # Reads in Fb code and asks Fb if it's valid and what user it points to
    def authenticate(self, token=None, request=None):

        args = {
            'client_id': settings.FACEBOOK_APP_ID,
            'redirect_uri': request.build_absolute_uri('/facebook/authentication_callback'),
            'client_secret': settings.FACEBOOK_APP_SECRET,
            'code': token,
        }
        
        # Get a legit access token
        target = urllib.urlopen('https://graph.facebook.com/oauth/access_token?'
                            + urllib.urlencode(args)).read()
        # CHC target is a URL string with the access token embedded as a query string key/value pair
        # CHC use urlparse library to parse the query string
        response = urlparse.parse_qs(target) 
      
        # CHC the response is a dictionary, so process the dictionary with a key lookup
        if (response.__contains__('access_token')): 
            access_token = response['access_token'][-1]
        # CHC they -1 index removes the start and end braces from the string, not sure why this works
        else:
            return None# no user so just stop the authentication process
        # Read the user's profile information
        facebook_profile = urllib.urlopen(
                'https://graph.facebook.com/me?access_token=%s' % access_token)
        facebook_profile = json.load(facebook_profile)
        
        # find existing site user with this id or create a new user 
        # called function is in a custom UserProfile manager because it is also used during login/authentication
        return UserProfile.objects.find_or_create_user(fb_id=facebook_profile['id'], fb_access_token=access_token, fb_profile=facebook_profile, is_this_for_me=True)

    def get_user(self, user_id):
        """ Just returns the user of a given ID. """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    supports_object_permissions = False
    supports_anonymous_user = True
