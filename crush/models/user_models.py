from django.db import models
# use signal to create user profile automatically when user created
import datetime
from django.db import IntegrityError
from django.contrib.auth.models import (UserManager, AbstractUser)
from django.conf import settings
import crush.models.relationship_models
from utils import graph_api_fetch
from crush.models.miscellaneous_models import InviteEmail
import thread
from django.db.models import Q
from django.core.cache import cache


# a custom User Profile manager class to encapsulate common actions taken on a table level (not row-user level)
class FacebookUserManager(UserManager):

    # helper function used by find_or_create_user function to separate profile data extraction from facebook and insertion into the user profile object
    def update_user(self,facebook_user,fb_profile):
        new_fields=[]
        if ('is_active' in fb_profile and facebook_user.is_active!=fb_profile['is_active']):
            facebook_user.is_active = fb_profile['is_active']
            new_fields.append('is_active')
        if ('access_token' in fb_profile and facebook_user.access_token!=fb_profile['access_token']):
            facebook_user.access_token = fb_profile['access_token']
            new_fields.append('access_token')
        
        if ('first_name' in fb_profile and facebook_user.first_name!=fb_profile['first_name']):
            facebook_user.first_name = fb_profile['first_name']
            new_fields.append('first_name')
        
        if ('last_name' in fb_profile and facebook_user.last_name!=fb_profile['last_name']):
            facebook_user.last_name = fb_profile['last_name']
            new_fields.append('last_name')
        
        if (facebook_user.birthday_year==None and 'birthday' in fb_profile):
            date_pieces=fb_profile['birthday'].split('/')
            if len(date_pieces)>2: # i only care to store birthday if it has a year
                facebook_user.birthday_year= int(date_pieces[2])   
            new_fields.append('birthday_year')
        
        if ('email' in fb_profile and facebook_user.email!=fb_profile['email']):
            facebook_user.email=fb_profile['email']
            new_fields.append('email')
        
        if (facebook_user.gender== '' and 'gender' in fb_profile):
            if fb_profile['gender']==u'male':
                facebook_user.gender=u'M'
            elif fb_profile['gender']==u'female':
                facebook_user.gender=u'F'
            new_fields.append('gender')
        
        if ('relationship_status' in fb_profile):            
            rel_stat = fb_profile['relationship_status']
            if ((rel_stat == u'Married') | (rel_stat==u'In a relationship') | (rel_stat==u'Engaged') | (rel_stat==u'In a civil union') | (rel_stat==u'In a domestic partnership')):
                facebook_user.is_single=False
            else: 
                facebook_user.is_single=True
            new_fields.append('is_single')
                
        if(facebook_user.gender_pref == '' and 'interested_in' in fb_profile):
            if len(fb_profile['interested_in'])==1: 
                if fb_profile['interested_in'][0]==u'female':
                    facebook_user.gender_pref=u'F'
                else: 
                    facebook_user.gender_pref=u'M'
            elif len(fb_profile['interested_in']) > 1:
                facebook_user.gender_pref=u'B'
            new_fields.append('gender_pref')
        age_results =  graph_api_fetch(fb_profile['access_token'],facebook_user.username + "?fields=age_range",False, False)
        age_range_max=""
        is_underage=False
        if age_results and "age_range" in age_results and "max" in age_results["age_range"]:
            age_range_max = age_results["age_range"]["max"]
            if age_range_max == 17:
                is_underage = True
        if facebook_user.is_underage != is_underage:
            facebook_user.is_underage=is_underage
            new_fields.append('is_underage')       
        facebook_user.save(update_fields=new_fields)
                     
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
                if user.is_active==False:# if the user was previously created (on someone else's crush list, but they are logging for first time)
                    fb_profile['is_active']=True
                    # dont' run update_user as a thread the first time
                    thread.start_new_thread(self.update_user,(user,fb_profile)) 
                    thread.start_new_thread(self.handle_activated_user,(user,fb_profile))
                    #self.activate_inactive_user(user, fb_profile)
                else:
                    thread.start_new_thread(self.update_user,(user,fb_profile))
        # No existing user, create one (happens when someone adds a crush but that crush is not already a user
        except FacebookUser.DoesNotExist:
            
            if fb_profile == None:
                try:
                    fb_profile=graph_api_fetch(fb_access_token,str(fb_id),expect_data=False)
                except:
                    return None # bad error handling, couldn't fetch data for this user
            fb_id=fb_profile['id']
            fb_username = fb_profile.get('username', fb_id)# if no username then grab id
            user = None
            try:
                
                fb_profile['is_active'] = is_this_for_me
                if not is_this_for_me:
                    user = FacebookUser.objects.create_user(username=fb_id)
                    # finally update the cached list of inactive_users
                    all_inactive_user_list = cache.get(settings.INACTIVE_USER_CACHE_KEY,[])
                    all_inactive_user_list.append(user.username)
                    cache.set(settings.INACTIVE_USER_CACHE_KEY,all_inactive_user_list)
                else:
                    user = FacebookUser.objects.create_user(username=fb_id,access_token=fb_access_token)
            except Exception as e:
                print str(e)
            except IntegrityError:
                print fb_username + " unable to create a new user, probably cause it's already been created"
                return super(FacebookUserManager, self).get_query_set().get(username=fb_id)
            thread.start_new_thread(self.update_user,(user,fb_profile))     
        return user
    
    def handle_activated_user(self,user,fb_profile):
        # look for any admirers at this point so their relationships can get updated
        admirer_relationships = crush.models.relationship_models.CrushRelationship.objects.all_admirers(user)
        for relation in admirer_relationships:
            # for each admirer relationship, change their status to 2 (crush is member, not yet started line-up)
            relation.target_status = 2
            relation.updated_flag=True
            relation.date_target_signed_up = datetime.datetime.now()
            relation.save(update_fields=['target_status','date_target_signed_up','updated_flag'])
        InviteEmail.objects.delete_activated_user_emails(user)
        user.friends_that_invited_me.clear()
        # update the cache inactive user list
        all_inactive_user_list = cache.get(settings.INACTIVE_USER_CACHE_KEY,[])
        all_inactive_user_list.remove(user.username)
        cache.set(settings.INACTIVE_USER_CACHE_KEY,all_inactive_user_list)
        # get user's age range
       
        
# Custom User Profile Class allows custom User fields to be associated with unique django user instance
class FacebookUser(AbstractUser):
    
    class Meta: 
    # this allows the models to be broken into separate model files
        app_label = 'crush' 
        
    # ------- START OF REQUIRED FIELDS
    access_token = models.CharField(max_length=50)
    
    GENDER_CHOICES = (
                      (u'M', u'male'),
                      (u'F', u'female'),
                      )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES,null=False)
    
    GENDER_PREF_CHOICES = (
                           (u'M',u'male'),
                           (u'F',u'female'),
                           (u'B',u'both')
                           )
    gender_pref=models.CharField(max_length=1,choices=GENDER_PREF_CHOICES)

    is_single = models.BooleanField(default=True)
    is_underage = models.BooleanField(default=False)

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
    friends_with_admirers = models.ManyToManyField('self',symmetrical=False,related_name='friends_with_admirers_set',blank=True)
    # For inactive users - friends of theirs who have already sent them a fb invite (clear out this field during activation)
    friends_that_invited_me = models.ManyToManyField('self', symmetrical=False,related_name='friends_that_invited_me_set',blank=True)
    
    bNotify_crush_signed_up = models.BooleanField(default=True)
    bNotify_crush_signup_reminder = models.BooleanField(default=True)
    #bNotify_crush_started_lineup = models.BooleanField(default=True) # off by default cause reciprocal lineup crushes don't instantiate a lineup
    bNotify_crush_responded = models.BooleanField(default=True)
    bNotify_new_admirer = models.BooleanField(default=True)    
    bNotify_setup_lineup_completed= models.BooleanField(default=True)
    bNotify_setup_recommendee_responded= models.BooleanField(default=True)
    
    processed_activated_friends_admirers = models.DateTimeField(blank=True,null=True,default=None)
    #call this asynchronously after a user first logs in.
    def find_inactive_friends(self):
        global all_inactive_user_list
    # this is done whenever an active user is first created
        try:
            # this is a potentially expensive operation, so do it at most every 12 hours
            if  (self.processed_activated_friends_admirers):
                time_since_last_update = datetime.datetime.now() - self.processed_activated_friends_admirers 
                if time_since_last_update < datetime.timedelta(hours=settings.FRIENDS_WITH_ADMIRERS_SEARCH_DELAY):
                    print"don't re-process friends-with admirers - too soon: " + str(time_since_last_update.hours)
                    return

            print "attempting to load the json results"
            fql_query_results=graph_api_fetch(self.access_token,"me/friends")

        except Exception as e:
            print str(e)
            raise 

        all_inactive_user_list = None#cache.get(settings.INACTIVE_USER_CACHE_KEY)         
        if all_inactive_user_list==None:
            print "updating cache with new all_inactive_user_list"
            all_inactive_user_list = list(FacebookUser.objects.filter(Q(is_active=False),~Q(crush_crushrelationship_set_from_target=None)).values_list('username',flat=True))
            print str(all_inactive_user_list)
            cache.set(settings.INACTIVE_USER_CACHE_KEY,all_inactive_user_list)
            
        else:
            print "using cache's all_inactive_user_list " + str(all_inactive_user_list)
    
        # clear out past data
        self.friends_with_admirers.clear()
        # loop through all friends.  if any friend is in inactive user results, then add them to the friends_with_admirers list.
        all_crushes=self.crush_targets.all()
        for friend in fql_query_results:
            if friend['id'] in all_inactive_user_list:
                friend_user = FacebookUser.objects.get(username=str(friend['id']))
                if friend_user not in all_crushes and self not in friend_user.friends_that_invited_me.all(): 
                    self.friends_with_admirers.add(friend_user)

        # mark the function complete flag so that future users/pages won't reprocess the user
        self.processed_activated_friends_admirers = datetime.datetime.now()
        self.save(update_fields=['processed_activated_friends_admirers'])
        return
  
    # if user sends an fb invite to their inactive friend, them remove them from their list of inactive friends 
    # and add them to list of friend who invited them
    def update_friends_with_admirers(self,remove_username=None):  
        friend_user = self.friends_with_admirers.get(username=str(remove_username))
        friend_user.friends_that_invited_me.add(self)
        self.friends_with_admirers.remove(friend_user)
    
    
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
    
    def get_facebook_pic(self,size):
        
        src =  'http://graph.facebook.com/' + self.username + '/picture?width=' + str(size) + '&height=' + str(size)
        print src
        return src
    
    def get_name(self):
        return self.first_name + " " + self.last_name
    
    # called by lineup.html to determine what to do after jquery lineup slider closes
    def get_progressing_admirers(self):
        return crush.models.relationship_models.CrushRelationship.objects.progressing_admirers(self)
    # called by lineup.html to determine what to do after jquery lineup slider closes
    def get_progressing_setups_for_me(self):
        return self.crush_setuprelationship_set_from_target.filter(date_lineup_finished=None)
    def get_fb_gender(self):
        if self.gender==u'M':
            return 'male'
        else:
            return 'female'
    
    def get_gender_pronoun(self):
        if self.gender==u'M':
            return 'his'
        else:
            return 'her'
    
    def get_gender_pronoun_subject(self):
        if self.gender==u'M':
            return 'he'
        else:
            return 'she'
    
    #=========  Debug Self Reference Function =========
    def __unicode__(self):
        return self.first_name + ' ' + self.last_name + ' (' + self.username + ')'
     
# used for message-write: recipient auto lookup     
class NamesLookup(object):

    def get_query(self,q,request):
        """ return a query set.  you also have access to request.user if needed """
        return crush.models.relationship_models.CrushRelationship.objects.completed_crushes(request.user).filter(Q(target_status=4),Q(target_person__first_name__contains=q) | Q(target_person__last_name__icontains=q) )

    def format_result(self,relationship):
        user=relationship.target_person
        """ the search results display in the dropdown menu.  may contain html and multiple-lines. will remove any |  """
        return  u"%s %s (%s)" % (user.first_name, user.last_name, user.username)

    def format_item(self,relationship):
        user=relationship.target_person
        """ the display of a currently selected object in the area below the search box. html is OK """
        #return unicode(user)
        return '<img src="http://graph.facebook.com/' + user.username + '/picture?width=20&height=20">&nbsp;' +  u"%s %s" % (user.first_name, user.last_name)
    def get_objects(self,ids):
        """ given a list of ids, return the objects ordered as you would like them on the admin page.
            this is for displaying the currently selected items (in the case of a ManyToMany field)
        """
        return FacebookUser.objects.filter(pk__in=ids).order_by('first_name','last_name')