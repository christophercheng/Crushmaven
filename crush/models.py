from django.db import models
from django.contrib.auth.models import User
# use signal to create user profile automatically when user created
from facebook.models import FacebookProfile
import urllib, json
import datetime
from django.db import IntegrityError
# list of all the peeps I have crushes on     
class CrushList(models.Model): 
    # each crush list could have many users, who could also be part of other crush lists
        # thus a many to many relationship between the crush list and the crushees
        # the special characteristics of each crush is described through the CrushRelationship class
    list_members = models.ManyToManyField(User, through='Relationship')
    #list_owner= models.OneToOneField(User, related_name='admirer') #the admirer

class MyMaybeList(CrushList):
    def __unicode__(self):
        return str(self.list_owner.username) + ' My Maybe List'

class MyFeaturedMaybeList(CrushList):
    
    queued_admirers = models.ManyToManyField(User)
    def __unicode__(self):
        return str(self.list_owner.username) + ' My Featured Maybe List'  

class MyCrushList(CrushList):
    def __unicode__(self):
        return str(self.list_owner.username) + ' My Crush List'  
    
class MySecretAdmirerList(CrushList):
    def __unicode__(self):
        return str(self.list_owner.username) + ' My Secret Admirer List'  
    
class MyOpenAdmirerList(CrushList):
    def __unicode__(self):
        return str(self.list_owner.username) + ' My Open Admirer List'  
    
class MyNotInterestedList(CrushList):
    def __unicode__(self):
        return str(self.list_owner.username) + ' My Not Interested List'  



# details about each unique crush 
class Relationship(models.Model):
    # crushee is the user who is being desired
    other_person = models.ForeignKey(User,unique=True)
    
    crush_list = models.ForeignKey(CrushList)

    # a crush relationship can be in only one of the following states:
    CRUSH_STATE_CHOICES = (
                         (u'MAYBE', 'Maybe'),
                         (u'WAITING', 'Waiting'), #one person has expressed interested; the other person has not responded
                         (u'MATCH', 'Match'),
                         (u'NO_CRUSH', 'No Crush'),
                         )  
                        
    crush_state=models.CharField(max_length=7,default='WAITING', choices=CRUSH_STATE_CHOICES)
    
    # date_crush_status_changed keeps track of when the crush status was changed... 
    # e.g. date 'featured maybe' became a 'crush' or a 'no crush'
    date_relationhsip_type_changed = models.DateTimeField(auto_now_add=True)
    
    # how are the admirer and crushee connected
    FRIENDSHIP_TYPE_CHOICES = (
                               (u'FRIEND','Friend'),
                               (u'FRIEND_OF_FRIEND','Friend of Friend'),
                               (u'3RD_DEGREE_FRIEND', '3rd Degree Friend'), # this won't be used initially
                               (u'STRANGER', 'Stranger'),
                               )
    
    friendship_type=models.CharField(max_length=20, default='FRIEND', choices=FRIENDSHIP_TYPE_CHOICES)
    
    # list of one or many mutual friends between the admirer and crushee
    mutual_friend_list = models.ManyToManyField(User, related_name='mutual_friends')

    # -- CRUSH LIST - FEATURE ADD-ONS-- 
    # potentially both the admirer and the crusher can pay for a method to more easily determine a match
    is_lineup_paid_for=models.BooleanField(default=False)
    is_lineup_completed=models.BooleanField(default=False)
    num_lineup_contestants=models.IntegerField(default=10) # basic lineup has 10 contestants, but for extra money this number can be configured.
    #admirer can pay to have his feature profiled on crushee's site
    is_feature_sneak_paid_for=models.BooleanField(default=False)
    is_invisibility_paid_for=models.BooleanField(default=False)
    
    def __unicode__(self):
        return 'Crush:' + str(self.crushee_list.admirer.username) + '-on-' + str(self.crushee.username)

class CustomProfileManager(models.Manager):
    def find_or_create_user(self, fb_id, fb_access_token,fb_profile,is_this_for_me):
        try:
        # Try and find existing user
            user_profile = super(CustomProfileManager,self).get_query_set().get(facebook_id=fb_id)
            user = user_profile.user
            if (is_this_for_me): #if logging user in then update his/her token
                user_profile.access_token=fb_access_token

                if user.is_active==False:# if the user was previously created (on someone else's crush list, but they are logging for first time)
                    user.is_active=True# then activate their account
                    # and also update their gender preferences; they're not always obtained indirectly
                    if ('birthday' in fb_profile):
                        date_pieces=fb_profile['birthday'].split('/')
                        if len(date_pieces)>2: # i only care to store birthday if it has a year
                            user_profile.birthday= datetime.date(int(date_pieces[2]),int(date_pieces[0]),int(date_pieces[1]))   
                    if ('gender' in fb_profile):
                        if fb_profile['gender']==u'male':
                            user_profile.gender=u'M'
                        elif fb_profile['gender']==u'female':
                            user_profile.gender=u'F'
                    if('interested_in' in fb_profile):
                        if len(fb_profile['interested_in'])==1: 
                            if fb_profile['interested_in'][0]==u'female':
                                    user_profile.gender_pref=u'F'
                            else: 
                                    user_profile.gender_pref=u'M'
                        elif len(fb_profile['interested_in']) > 1:
                            user_profile.gender_pref=u'B'
                user_profile.save()
        # No existing user, create one
        except UserProfile.DoesNotExist:
            if fb_profile == None:
                fb_profile = urllib.urlopen('https://graph.facebook.com/' + fb_id + '/?access_token=%s' % fb_access_token)
                fb_profile = json.load(fb_profile)
          
            username = fb_profile.get('username', fb_profile['id'])# if no username then grab id
            try:
                user = User.objects.create_user(username=username)
            except IntegrityError:
                return #this would be a bad database error (something out-a-sync!)
            user.first_name = fb_profile['first_name']
            user.last_name = fb_profile['last_name']
            if not(is_this_for_me):
                user.is_active=False

            # Create the user's UserProfile
            user_profile = UserProfile(user=user, facebook_id=fb_id)
            if (is_this_for_me): #if logging user in then update his/her token
                user_profile.access_token=fb_access_token
            if ('birthday' in fb_profile):
                date_pieces=fb_profile['birthday'].split('/')
                if len(date_pieces)>2: # i only care to store birthday if it has a year
                    user_profile.birthday= datetime.date(int(date_pieces[2]),int(date_pieces[0]),int(date_pieces[1]))         
            if ('gender' in fb_profile):
                if fb_profile['gender']==u'male':
                    user_profile.gender=u'M'
                elif fb_profile['gender']==u'female':
                    user_profile.gender=u'F'
            if('interested_in' in fb_profile):
                if len(fb_profile['interested_in'])==1: 
                    if fb_profile['interested_in'][0]==u'female':
                        user_profile.gender_pref=u'F'
                    else: 
                        user_profile.gender_pref=u'M'
                elif len(fb_profile['interested_in']) > 1:
                    user_profile.gender_pref=u'B'
            # Create all of the user's lists
            user_profile.my_crush_list=MyCrushList.objects.create()
            user_profile.my_secret_admirer_list=MySecretAdmirerList.objects.create()
            user_profile.my_open_admirer_list=MyOpenAdmirerList.objects.create()
            user_profile.my_not_interested_list=MyNotInterestedList.objects.create()
            user_profile.my_maybe_list=MyMaybeList.objects.create()
            user_profile.my_featured_maybe_list=MyFeaturedMaybeList.objects.create()
            
            user.save()
            user_profile.save()
        return user
        
# Custom User Profile Class allows custom User fields to be associated with unique django user instance
class UserProfile(FacebookProfile):

    objects = CustomProfileManager()
    
    GENDER_CHOICES = (
                      (u'M', u'Male'),
                      (u'F', u'Female'),
                      )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True)
    
    GENDER_PREF_CHOICES = (
                           (u'M',u'Male'),
                           (u'F',u'Female'),
                           (u'B',u'Both')
                           )
    gender_pref=models.CharField(max_length=1,choices=GENDER_PREF_CHOICES,null=True)
    
    birthday = models.DateField(null=True)
    age = models.IntegerField(null=True)
    age_pref_min=models.IntegerField(null=True)
    age_pref_max=models.IntegerField(null=True)

    # by default give every user X credits so that they can acquaint themselves with the payment process
    payment_credits = models.FloatField(default=3)
    total_credits_spent = models.FloatField(default=0)
    
    # each user has a set of lists
    my_crush_list = models.OneToOneField(MyCrushList,null=True)
    my_secret_admirer_list = models.OneToOneField(MySecretAdmirerList,null=True)
    my_open_admirer_list = models.OneToOneField(MyOpenAdmirerList,null=True)
    my_not_interested_list = models.OneToOneField(MyNotInterestedList,null=True)
    my_featured_maybe_list = models.OneToOneField(MyFeaturedMaybeList,null=True)
    my_maybe_list = models.OneToOneField(MyMaybeList,null=True)
    
    
    # future data potential for:
        # facebook likes
        # facebook interests
        # geographic location
        # list of ALL facebook friends 
            # TBD: store the pics in a better deistributed file
            # TBD: ensure MEDIA_ROOT AND MEDIA_URL settings have been configured properly in settings file
        #pic_1 = models.ImageField(upload_to='profile_pics/%Y/%m/%d', null=True)
        #pic_2 = models.ImageField(upload_to='profile_pics/%Y/%m/%d', null=True)
        #pic_3 = models.ImageField(upload_to='profile_pics/%Y/%m/%d', null = True)
        #pic_4 = models.ImageField(upload_to='profile_pics/%Y/%m/%d',null=True)
        
    def __unicode__(self):
        return '(id:' + str(self.user.id) +') '+ self.user.username


class CreditSpent(models.Model):
    # associate transaction with one particular user
    user=models.ForeignKey(User)
    # datetimefield when credit was spent
    date_spent=models.DateTimeField(auto_now_add=True)
    # amount for 
    amount_spent=models.FloatField(default=0)
    # activity for
    SERVICE_PAYMENT_CHOICES = (
                       (0,u'Secret Admirer List Addition'),
                       (1,u'No Secret Admirer List Initiation'),
                       (2,u'Early Crush List Removal'),
                       (3,u'Basic Lineup Initiation'),
                       (4,u'Custom Lineup Initiation'),
                       (5,u'Feature List Sneak'),
                       (6,u'Crush Invisibility'),
                       )
    
    service_payment_type=models.IntegerField(default=0,choices=SERVICE_PAYMENT_CHOICES)
    
 

