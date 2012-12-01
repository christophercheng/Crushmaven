import json
import urllib
from django.db import models
from django.contrib.auth.models import User

# This is the base class for User Profile
class FacebookProfile(models.Model):
    user = models.OneToOneField(User)
    # this will be populated by the facebook username first, then the facebook id if username is non-existant
    facebook_id = models.BigIntegerField(default=0) # why is this not a character field?
    access_token = models.CharField(max_length=50)
    facebook_username = models.CharField(max_length=60)
    def get_facebook_profile(self):
        fb_profile = urllib.urlopen(
                        'https://graph.facebook.com/me?access_token=%s'
                        % self.access_token)
        data = json.load(fb_profile)
        data.update({'picture': self.get_facebook_picture()})
        return data

    def get_facebook_picture(self):
        return u'http://graph.facebook.com/%s/picture?type=large' \
                                                            % self.user.username

    def save(self):
        print "FacebookProfile save() called"
        # updates user avatar
        super(FacebookProfile, self).save()
        self.user.save()
