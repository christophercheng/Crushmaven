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
                    if self.initialize_lineup(relationship) == False:
                        raise forms.ValidationError("Sorry, we cannot add this user. For some odd reason we can not create a line-up for them.")
                return cleaned_data
        except KeyError:
            raise forms.ValidationError("Invalid facebook id")
       
        return
    
    def initialize_lineup(self, relationship):
        print "initializing relationship for crush: " + relationship.target_person.facebook_username
        me = self.request.user
        # get sex of crush
        my_gender= 'Male' if me.gender == 'M'  else 'Female'
        
        exclude_facebook_ids = "'" + str(relationship.source_person.username) + "'"
   
        fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (" + exclude_facebook_ids + ")) )) AND sex = '" + my_gender + "'  ORDER BY friend_count DESC LIMIT 9"
        print "fql query to send out: " + fql_query
    
        fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,me.access_token))
    
        try:
            print "json results: " + str(fql_query_results)
            data = json.load(fql_query_results)['data']
       
            if (len(data) == 0):
                if my_gender=='Male':
                    data = [{u'username':u'zuck', 'uid':u'zuck'}]
                else:
                    data = [{u'username':u'sheryl', 'uid':u'sheryl'}]
            print "data: " + str(data)
        except KeyError, ValueError:
            print "ValueError on Fql Query Fetch read!"
            return False
        # determine where the admirer should randomly fall into the lineup
        admirer_position=random.randint(0, len(data)) # normally len(data) should be 9
        print "admirer_position: " + str(admirer_position)
        index = 0
        rel_id = relationship.id
        for fql_user in data:
                # if the current lineup position is where the admirer should go, then insert the admirer
            if index==admirer_position:
                new_member_id = rel_id + (.1 * index)
                relationship.lineupmember_set.create(position=new_member_id,LineupUser=relationship.source_person)
                print "put crush in position: " + str(new_member_id) + " from index value: " + str(index)
                index = index + 1            
                # create a lineup member with the given username      
            new_member_id = rel_id + (.1 * index)
            lineup_user=FacebookUser.objects.find_or_create_user(fb_id=fql_user['uid'],fb_access_token=me.access_token,is_this_for_me=False)
            relationship.lineupmember_set.create(position=new_member_id, LineupUser=lineup_user)
            print "put friend in position: " + str(new_member_id) + " from index value: " + str(index)
            index = index + 1
        
        if len(data)==admirer_position:
            new_member_id = rel_id + (len(data) * .1)
            relationship.lineupmember_set.create(position=new_member_id,LineupUser=relationship.source_person)
            print "put crush in position: " + str(new_member_id)        
            
        relationship.number_unrated_lineup_members = relationship.lineupmember_set.count()
        print "number lineup members: " + str(relationship.lineupmember_set.count())
        relationship.is_lineup_initialized = True
        relationship.save(update_fields=['number_unrated_lineup_members','is_lineup_initialized'])

    #    print "Number of results: " + str((data['data']).__len__())
        
        return True
