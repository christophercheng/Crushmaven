from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
# use signal to create user profile automatically when user created
from django.db.models.signals import post_save
from facebook.models import FacebookProfile

# list of all the peeps I have crushes on     
class CrushList(models.Model): 
    # each crush list could have many users, who could also be part of other crush lists
        # thus a many to many relationship between the crush list and the crushees
        # the special characteristics of each crush is described through the CrushRelationship class
    list_members = models.ManyToManyField(User, through='Relationship')
    list_owner= models.OneToOneField(User, related_name='admirer') #the admirer

class MaybeList(CrushList):
    def __unicode__(self):
        return str(self.list_owner.username) + ' Maybe List'

class FeaturedMaybeList(CrushList):
    
    queued_admirers = models.ManyToManyField(User)
    def __unicode__(self):
        return str(self.list_owner.username) + ' Featured Maybe List'  

class MyCrushList(CrushList):
    def __unicode__(self):
        return str(self.list_owner.username) + ' My Crush List'  
    
class MySecretAdmirerList(CrushList):
    def __unicode__(self):
        return str(self.list_owner.username) + ' My Secret Admirer List'  
    
class MyNotSecretAdmirerList(CrushList):
    def __unicode__(self):
        return str(self.list_owner.username) + ' My Not Secret List'  
    
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
                        
    crush_state=models.CharField(max_length=7,default='MAYBE', choices=CRUSH_STATE_CHOICES)
    
    # date_crush_status_changed keeps track of when the crush status was changed... 
    # e.g. date 'featured maybe' became a 'crush' or a 'no crush'
    date_relationhsip_type_changed = models.DateTimeField(null=True)
    
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

# Custom User Profile Class allows custom User fields to be associated with unique django user instance
class UserProfile(FacebookProfile):

    GENDER_CHOICES = (
                      (u'M', u'Male'),
                      (u'F', u'Female'),
                      )
    gender = models.CharField(max_length=1, default='M', choices=GENDER_CHOICES, )
    
    GENDER_PREF_CHOICES = (
                           (u'M',u'Male'),
                           (u'F',u'Female'),
                           (u'B',u'Both')
                           )
    gender_pref=models.CharField(max_length=1, default='F', choices=GENDER_PREF_CHOICES)
    
    age = models.IntegerField(default=999)
    age_pref_min=models.IntegerField(default=999)
    age_pref_max=models.IntegerField(default=999)

    # by default give every user X credits so that they can acquaint themselves with the payment process
    payment_credits = models.FloatField(default=3)
    total_credits_spent = models.FloatField(default=0)
    
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
    
 

