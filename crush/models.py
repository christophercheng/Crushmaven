from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
# use signal to create user profile automatically when user created
from django.db.models.signals import post_save

# list of all the peeps I have crushes on     
class CrusheeList(models.Model): 
    # each crush list could have many users, who could also be part of other crush lists
        # thus a many to many relationship between the crush list and the crushees
        # the special characteristics of each crush is described through the CrushRelationship class
    members = models.ManyToManyField(User, through='CrushRelationship')
    admirer= models.OneToOneField(User,related_name='admirer')
    def __unicode__(self):
        return str(self.admirer.username) + ' crushee list'
    # consider creating a custom function that would prevent adding duplicates
    

# details about each unique crush 
class CrushRelationship(models.Model):
    # crushee is the user who is being desired
    crushee = models.ForeignKey(User,unique=True)
    
    crushee_list = models.ForeignKey(CrusheeList)

    # a crush relationship can be in only one of the following states:
    RELATIONSHIP_STATE_CHOICES = (
                         (0, 'Maybe'),
                         (1, 'Featured Maybe'),
                         (2, 'Crush'),
                         (3, 'Match'),
                         (4, 'No Crush'),
                         )
    relationship_state=models.IntegerField(default=2, choices=RELATIONSHIP_STATE_CHOICES)
    
    # date_crush_status_changed keeps track of when the crush status was changed... 
    # e.g. date 'featured maybe' became a 'crush' or a 'no crush'
    date_relationhsip_type_changed = models.DateField(null=True)
    
    # how are the admirer and crushee connected
    FRIENDSHIP_TYPE_CHOICES = (
                               (0,'Friend'),
                               (1,'Friend of Friend'),
                               (2,'Friend of Friend of Friend'),
                               (3, 'Stranger'),
                               )
    
    friendship_type=models.IntegerField(default=0, choices=FRIENDSHIP_TYPE_CHOICES)
    
    # list of one or many mutual friends between the admirer and crushee
    mutual_friend_list = models.ManyToManyField(User, related_name='mutual_friend')
    
    # TBD figure out if crush status data field is necessary
        # crush status could also be programatically determined by figuring out which crush list
        # the admirer is a member of - within the the crushee's profile
        # for time being let's just store the status in database
    CRUSH_STATUS_CHOICES = (
                            (0, 'Waiting'),
                            (1, 'Matched'),
                            (2, 'Not Matched'),
                            )
    
    crush_status = models.IntegerField(default=0, choices=CRUSH_STATUS_CHOICES)

    has_desired_user_viewed_admirer = models.BooleanField(default=False)

    # admirer can pay to directly notify the crushee that he or she is interested
    is_wink_paid_for = models.BooleanField(default=False)
    # potentially both the admirer and the crusher can pay for a method to more easily determine a match
    is_match_quiz_paid_for=models.BooleanField(default=False)
    is_match_quiz_completed=models.BooleanField(default=False)
    #admirer can pay to have his feature profiled on crushee's site
    is_profile_featuring_paid_for=models.BooleanField(default=False)
    
    def __unicode__(self):
        return 'Crush:' + str(self.crushee_list.admirer.username) + '-on-' + str(self.crushee.username)

# Custom User Profile Class allows custom User fields to be associated with unique django user instance
class UserProfile(models.Model):

    # User model stores username (facebook username), first & last name, email
    user = models.OneToOneField(User)

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

    # TBD: store the pics in a better deistributed file
    # TBD: ensure MEDIA_ROOT AND MEDIA_URL settings have been configured properly in settings file
    pic_1 = models.ImageField(upload_to='profile_pics/%Y/%m/%d', null=True)
    
    pic_2 = models.ImageField(upload_to='profile_pics/%Y/%m/%d', null=True)
    
    pic_3 = models.ImageField(upload_to='profile_pics/%Y/%m/%d', null = True)
    
    pic_4 = models.ImageField(upload_to='profile_pics/%Y/%m/%d',null=True)

    # by default give every user X credits so that they can acquaint themselves with the payment process
    payment_credits = models.IntegerField(default=5)

    # future data potential for:
        # facebook likes
        # facebook interests
        # geographic location
        # list of ALL facebook friends 
    
    # each user has only one crush list - a one to one relationship
    #crushee_list = models.OneToOneField(CrusheeList, null=True)
        
    def __unicode__(self):
        return '(id:' + str(self.user.id) +') '+ self.user.username
    
# override the User's create function so that user profiles are auto created when users are created
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)  