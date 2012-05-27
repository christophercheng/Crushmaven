import urllib, json, urlparse
from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError
#from django.core.urlresolvers import reverse CHC - reverse gives me problems

from crush.models import *

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
        fb_profile = urllib.urlopen(
                'https://graph.facebook.com/me?access_token=%s' % access_token)
        fb_profile = json.load(fb_profile)

        try:
        # Try and find existing user
            fb_user = UserProfile.objects.get(facebook_id=fb_profile['id'])
            user = fb_user.user
            # Update access_token
            fb_user.access_token = access_token
            fb_user.save()
        # No existing user, create one
        except UserProfile.DoesNotExist:

            username = fb_profile.get('username', fb_profile['id'])# if no username then grab id
            print username

            try:
                user = User.objects.create_user(username=username)
            except IntegrityError:
                return #if there is already a user then get out of here - something catastrophic is happening!
            user.first_name = fb_profile['first_name']
            user.last_name = fb_profile['last_name']
            user.save()

                # Create the FacebookProfile
            fb_user = UserProfile(user=user, facebook_id=fb_profile['id'], access_token=access_token)
            if ('gender' in fb_profile):
                if fb_profile['gender']==u'male':
                    fb_user.gender=u'M'
                elif fb_profile['gender']==u'female':
                        fb_user.gender=u'F'
            if('interested_in' in fb_profile):
                if len(fb_profile['interested_in'])==1: 
                    if fb_profile['interested_in'][0]==u'female':
                        fb_user.gender_pref=u'F'
                    else: 
                        fb_user.gender_pref=u'M'
                elif len(fb_profile['interested_in']) > 1:
                    fb_user.gender_pref=u'B'   
            
            # Create all of the user's lists
            fb_user.my_crush_list=MyCrushList.objects.create()
            fb_user.my_secret_admirer_list=MySecretAdmirerList.objects.create()
            fb_user.my_open_admirer_list=MyOpenAdmirerList.objects.create()
            fb_user.my_not_interested_list=MyNotInterestedList.objects.create()
            fb_user.my_maybe_list=MyMaybeList.objects.create()
            fb_user.my_featured_maybe_list=MyFeaturedMaybeList.objects.create()
            
            fb_user.save()
        return user

    def get_user(self, user_id):
        """ Just returns the user of a given ID. """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    supports_object_permissions = False
    supports_anonymous_user = True
