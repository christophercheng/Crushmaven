'''
Created on Dec 24, 2012

@author: Chris Work
'''
#from django.forms import CharField
from django import forms
import urllib, json
from crush.models import FacebookUser, CrushRelationship
import random 

class SelectCrushIDForm(forms.Form):
    uid = forms.CharField(max_length=100,required=True)
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(SelectCrushIDForm, self).__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super(SelectCrushIDForm,self).clean()
        access_token = self.request.user.access_token
        print "clean called on SelectCrushIDForm with access_token: " + str(access_token)
        # call fb api to get user info and put it in the cleaned_data function
        fb_profile = urllib.urlopen('https://graph.facebook.com/' + (self.cleaned_data['uid']) + '/?access_token=%s' % access_token)
        fb_profile = json.load(fb_profile)
        print "resulant profile: " + str(fb_profile)
        
        try:
            crush_id = fb_profile['id'] #raises KeyError if no id key/value pair exists in the fb_profile dictionary
            try:
                self.request.user.crush_targets.get(username=fb_profile['id'])
                raise forms.ValidationError("You've already added this person as a crush.")
            except FacebookUser.DoesNotExist:
                # determine what their friend relationship is
                # - are they friends?
                friend_profile = urllib.urlopen('https://graph.facebook.com/' + self.request.user.username + '/friends/' + crush_id + '/?access_token=%s' % access_token)
                friend_profile = json.load(friend_profile)
                if len(friend_profile['data'])>0:
                    friend_type=0
                else:
                    friend_profile = urllib.urlopen('https://graph.facebook.com/' + self.request.user.username + '/mutualfriends/' + crush_id + '/?access_token=%s' % access_token)
                    friend_profile = json.load(friend_profile)
                    if len(friend_profile['data'])>0:
                        friend_type=1
                    else:
                        friend_type=2
                # create the user
                crush_user=FacebookUser.objects.find_or_create_user(crush_id, self.request.user.access_token,False, fb_profile)
                # add the crush
                relationship=CrushRelationship.objects.create(source_person=self.request.user,target_person=crush_user,friendship_type=friend_type)
               
                if friend_type > 0: # if this is a friend of friend or stranger, then the lineup must be built now
                    #  cause the crush can't pull the admirer's friend list through the graph api
                    if relationship.initialize_lineup() == False:
                        relationship.delete()
                        raise forms.ValidationError("Sorry, we cannot add this user. For some odd reason we can not create a line-up for them.")
                        # delete the crush!
   
                return cleaned_data
        except KeyError:
            raise forms.ValidationError("Invalid facebook id")
       
        return
    