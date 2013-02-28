from django.db import models
# use signal to create user profile automatically when user created
import urllib,urllib2, json
import datetime
from django.db import IntegrityError
from django.contrib.auth.models import (UserManager, AbstractUser)
from django.conf import settings
import crush.models.relationship_models
from utils import graph_api_fetch


# a custom User Profile manager class to encapsulate common actions taken on a table level (not row-user level)
class FacebookUserManager(UserManager):

    # helper function used by find_or_create_user function to separate profile data extraction from facebook and insertion into the user profile object
    def update_user(self,facebook_user,fb_profile):
        facebook_user.first_name = fb_profile['first_name']
        facebook_user.last_name = fb_profile['last_name']
        if (facebook_user.birthday_year==None and 'birthday' in fb_profile):
            date_pieces=fb_profile['birthday'].split('/')
            if len(date_pieces)>2: # i only care to store birthday if it has a year
                facebook_user.birthday_year= int(date_pieces[2])   
        if (facebook_user.email=='' and 'email' in fb_profile):
            facebook_user.email=fb_profile['email']
        if (facebook_user.gender=='' and 'gender' in fb_profile):
            if fb_profile['gender']==u'male':
                facebook_user.gender=u'M'
            elif fb_profile['gender']==u'female':
                facebook_user.gender=u'F'
        if ('relationship_status' in fb_profile):            
            rel_stat = fb_profile['relationship_status']
            if ((rel_stat == u'Married') | (rel_stat==u'In a relationship') | (rel_stat==u'Engaged') | (rel_stat==u'In a civil union') | (rel_stat==u'In a domestic partnership')):
                facebook_user.is_single=False
            else: facebook_user.is_single=True
        if(facebook_user.gender_pref == '' and 'interested_in' in fb_profile):
            if len(fb_profile['interested_in'])==1: 
                if fb_profile['interested_in'][0]==u'female':
                    facebook_user.gender_pref=u'F'
                else: 
                    facebook_user.gender_pref=u'M'
            elif len(fb_profile['interested_in']) > 1:
                facebook_user.gender_pref=u'B'
                
    # find_or_create_user called in two cases:
    # 1) after someone adds a crush from the friend selector dialog (is_this_for_me = false)
    # 2) when facebook authenticates a user (is_this_for_me = true

    def find_or_create_user(self, fb_id, fb_access_token,is_this_for_me,fb_profile=None):
        
        print "find_or_create_user called for id: " + str(fb_id)
        try:
        # Try and find existing user
            user = super(FacebookUserManager, self).get_query_set().get(username=fb_id)
            # existing user was found!
            if (is_this_for_me): 
                user.access_token=fb_access_token #if logging user in then update his/her token

                if user.is_active==False:# if the user was previously created (on someone else's crush list, but they are logging for first time)
                    user.is_active=True# then activate their account
                    # update their profile with facebook data; they're not always obtained indirectly
                    self.update_user(user,fb_profile)
                    # look for any admirers at this point so their relationships can get updated
                    admirer_relationships = crush.models.relationship_models.CrushRelationship.objects.all_admirers(user)
                    for relation in admirer_relationships:
                        # for each admirer relationship, change their status to 2 (crush is member, not yet started line-up)
                        relation.target_status = 2
                        relation.updated_flag=True
                        relation.date_target_signed_up = datetime.datetime.now()
                        relation.save(update_fields=['target_status','date_target_signed_up','updated_flag'])
                user.save(update_fields=['is_active','access_token','birthday_year','email','gender','is_single','gender_pref','first_name','last_name'])
        # No existing user, create one
        except FacebookUser.DoesNotExist:
            
            if fb_profile == None:
                try:
                    fb_profile=graph_api_fetch(fb_access_token,str(fb_id),expect_data=False)
                except:
                    return None # bad error handling, couldn't fetch data for this user
            fb_id=fb_profile['id']
            fb_username = fb_profile.get('username', fb_id)# if no username then grab id
            default_notification_settings=crush.models.miscellaneous_models.NotificationSettings.objects.create()
            try:
                print fb_username + ": creating username"
                user = FacebookUser.objects.create_user(username=fb_id,notification_settings=default_notification_settings)
                if is_this_for_me:
                    user.is_active=True
                    user.access_token=fb_access_token
                else:
                    user.is_active=False
                print fb_username + ": completed creation call"
            except IntegrityError:
                print fb_username + " unable to create a new user, probably cause it's already been created"
                return super(FacebookUserManager, self).get_query_set().get(username=fb_id)
            print fb_username + ": calling the update_user function"
            
            FacebookUser.objects.update_user(user,fb_profile)
                
            user.save(update_fields=['access_token','is_active','birthday_year','email','gender','is_single','gender_pref','first_name','last_name'])
   
        return user
    
# Custom User Profile Class allows custom User fields to be associated with unique django user instance
class FacebookUser(AbstractUser):
    
    class Meta: 
    # this allows the models to be broken into separate model files
        app_label = 'crush' 
        
    # ------- START OF REQUIRED FIELDS
    access_token = models.CharField(max_length=50)
    
    notification_settings=models.OneToOneField('NotificationSettings')
    
    # this will be populated by the facebook username first, then the facebook id if username is non-existant
    facebook_username = models.CharField(max_length=60) 
    
    GENDER_CHOICES = (
                      (u'M', u'male'),
                      (u'F', u'female'),
                      )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    GENDER_PREF_CHOICES = (
                           (u'M',u'male'),
                           (u'F',u'female'),
                           (u'B',u'both')
                           )
    gender_pref=models.CharField(max_length=1,choices=GENDER_PREF_CHOICES)

    is_single = models.BooleanField(default=True)

    # --------  END OF REQUIRED FIELDS
    
    # ----------  START OF OPTIONAL FIELDS

    
    birthday_year = models.IntegerField(null=True,blank=True,max_length=4,choices=[(y,y) for y in range(1920,datetime.datetime.now().year-6)])
    age_pref_min=models.IntegerField(null=True, blank=True,choices=[(y,y) for y in range(13,99)])
    age_pref_max=models.IntegerField(null=True,blank=True,choices=[(y,y) for y in range(13,99)])
    # by default give every user 1 credit ($1) so that they can acquaint themselves with the crush lineup process
    site_credits = models.IntegerField(default=settings.STARTING_CREDITS) 
    
    # each user has a set of user lists representing their 'just friends' and their crushes
    # here is an idiosyncrasy of this implementation:
        # to access a user's crushes, you need to go through the user's UserProfile object
        # to access a user's admirers, you need to go through the user's User object

    just_friends_targets = models.ManyToManyField('self', symmetrical=False, through='PlatonicRelationship',related_name='platonic_friend_set')
    crush_targets = models.ManyToManyField('self', symmetrical=False, through='CrushRelationship',related_name='admirer_set')

    # ----------- END  OF OPTIONAL FIELDS
    objects = FacebookUserManager()
    
    # for friends with admirers processing
    
    # many-to-many relationship with other friends with admirers
    friends_with_admirers = models.ManyToManyField('self',symmetrical=False,related_name='friends_with_admirers_set')
    
    def add_inactive_crushed_friend_by_id(self, friend_id):
        print "adding inactive crushed friend: " + friend_id
        # get user with friend id
        try:
            user = FacebookUser.objects.get(username=friend_id)
            self.friends_with_admirers.add(user)
        except FacebookUser.DoesNotExist:
            return False
        return

    processed_activated_friends_admirers = models.DateTimeField(null=True,default=None)
    #call this asynchronously after a user first logs in.
    def find_inactive_friends_of_activated_user(self):
    # this is done whenever an active user is first created

        # this is a potentially expensive operation, so do it at most every 12 hours
        if  (self.processed_activated_friends_admirers):
            time_since_last_update = datetime.datetime.now() - self.processed_activated_friends_admirers 
            if time_since_last_update.seconds < settings.FRIENDS_WITH_ADMIRERS_SEARCH_DELAY:
                print"don't re-process friends-with admirers - too soon: " + str(time_since_last_update.seconds)
                return
        
        # get all inactive users into a queryset result but filter out users who are also crushes of user
        all_inactive_crush_relationships = crush.models.relationship_models.CrushRelationship.objects.filter(target_status__lt=2).exclude(source_person=self)
        print "list of all inactive crush relationships: " + str(all_inactive_crush_relationships)
        # build list of all inactive users
        all_inactive_user_list=[]
        for crush_rel in all_inactive_crush_relationships:
            all_inactive_user_list.append(int(crush_rel.target_person.username))
        print "list of all site inactive users: " + str(all_inactive_user_list)        

        fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1=me())"
        try:
            print "attempting to load the json results"
            fql_query_results=graph_api_fetch(self.access_token,"me/friends")
            #full_query_string=fql_query_results = 'https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,self.access_token)
            #fql_query_results=urllib.urlopen(full_query_string)
            #fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,self.access_token))
            #fql_query_results = json.load(fql_query_results)['data']
        except:
            raise 
    
        # clear out past data
        self.friends_with_admirers_set.clear()
        # loop through all friends.  if any friend is in inactive user results, then add them to the friends_with_admirers list.
        for friend in fql_query_results:
            if friend['id'] in all_inactive_user_list:
                self.add_inactive_crushed_friend_by_id(str(friend['id']))
        # mark the function complete flag so that future users/pages won't reprocess the user
        self.processed_activated_friends_admirers = datetime.datetime.now()
        self.save(update_fields=['processed_activated_friends_admirers'])
        return
    
    #processed_inactivated_friends_admirers = models.BooleanField(default=False)
    def find_active_friends_of_inactivated_crush(self):
                
        # initialize a batch json argument for use in graph api batch request
            # batch format: https://graph.facebook.com/?access_token=31235234123&batch=[{"METHOD":"GET","relative_url","me/friends?limit=50"},{-second request}]
        #fb_batch_url="https://graph.facebook.com/?access_token=" + self.access_token + "&batch=["
        #request = "{'METHOD':'GET','RELATIVE_URL':me/friends?uid=";
        # loop through all inactive users.  within each loop, build up the batch request json
        #index=0;
        #for inactive_user in inactive_users:
            
        # break up batch into multiple batch requests if there are more than 50 requests per call
        
        # go through the results and for each result item, add user to the friends_with_admirers list.
       
        #self.processed_inactivated_friends_admirers=True
        return
    
    def get_facebook_profile(self):
        try:
            data=graph_api_fetch(self.access_token,'me',expect_data=False)
        except:
            return None
        data.update({'picture': self.get_facebook_picture()})
        return data

    def get_facebook_picture(self):
        return u'http://graph.facebook.com/%s/picture?type=large' % self.username
    
    # called by lineup.html to determine what to do after jquery lineup slider closes
    def get_progressing_admirers(self):
        print "here"
        return crush.models.relationship_models.CrushRelationship.objects.progressing_admirers(self)
    
    def get_fb_gender(self):
        if self.gender==u'M':
            return 'male'
        else:
            return 'female'
    
    #=========  Debug Self Reference Function =========
    def __unicode__(self):
        return '(id:' + str(self.username) +') ' + self.facebook_username