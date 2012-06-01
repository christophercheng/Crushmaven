from django.db import models
from django.contrib.auth.models import User
# use signal to create user profile automatically when user created
from facebook.models import FacebookProfile
import urllib, json
import datetime
from django.db import IntegrityError
from django.dispatch import receiver
 
# a custom User Profile manager class to encapsulate common actions taken on a table level (not row level)
class CustomProfileManager(models.Manager):
    
    def update_profile(self,user_profile,fb_profile):
        user_profile.user.first_name = fb_profile['first_name']
        user_profile.user.last_name = fb_profile['last_name']
        if ('birthday' in fb_profile):
            date_pieces=fb_profile['birthday'].split('/')
            if len(date_pieces)>2: # i only care to store birthday if it has a year
                user_profile.birthday= datetime.date(int(date_pieces[2]),int(date_pieces[0]),int(date_pieces[1]))   
        if ('email' in fb_profile):
            user_profile.email=fb_profile['email']
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
    
    def find_or_create_user(self, fb_id, fb_access_token,fb_profile,is_this_for_me):
        try:
        # Try and find existing user
            user_profile = super(CustomProfileManager,self).get_query_set().get(facebook_id=fb_id)
            user = user_profile.user
            if (is_this_for_me): #if logging user in then update his/her token
                user_profile.access_token=fb_access_token

                if user.is_active==False:# if the user was previously created (on someone else's crush list, but they are logging for first time)
                    user.is_active=True# then activate their account
                    # and also update their profile with facebook data; they're not always obtained indirectly
                    self.update_profile(user_profile, fb_profile)
                    
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

            if not(is_this_for_me):
                user.is_active=False

            # Create the user's UserProfile
            user_profile = UserProfile(user=user, facebook_id=fb_id)
            if (is_this_for_me): #if logging user in then update his/her token
                user_profile.access_token=fb_access_token
            self.update_profile(user_profile,fb_profile)

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
    email = models.EmailField(null=True)
    age = models.IntegerField(null=True)
    age_pref_min=models.IntegerField(null=True)
    age_pref_max=models.IntegerField(null=True)

    # by default give every user 10 credits ($1) so that they can acquaint themselves with the discovery lineup process
    site_credits = models.IntegerField(default=10) 
    
    # each user has a set of user lists
    open_crushees = models.ManyToManyField(User,through='OpenCrushRelationship',related_name='open_crushees_set')
    secret_crushees = models.ManyToManyField(User, through='SecretCrushRelationship',related_name='secret_crushees_set')
    no_crushees = models.ManyToManyField(User, through='NoCrushRelationship',related_name='no_crushees_set')
    
    
        
    def __unicode__(self):
        return '(id:' + str(self.user.id) +') '+ self.user.username

# details about each unique crush 
class BasicRelationship(models.Model):

    source_person_profile=models.ForeignKey(UserProfile)
    target_person=models.ForeignKey(User)

    # date_feelings_changed keeps track of when the crush list changed
    date_added = models.DateField(auto_now_add=True)
    
    # list of one or many mutual friends between the admirer and crushee
    #mutual_friend_list = models.ManyToManyField(User,related_name='%(app_label)s_%(class)s_related')
    
    # how are the admirer and crushee connected
    FRIENDSHIP_TYPE_CHOICES = (
                               (u'FRIEND','Friend'),
                               (u'FRIEND_OF_FRIEND','Friend of Friend'),
                               (u'3RD_DEGREE_FRIEND', '3rd Degree Friend'), # this won't be used initially
                               (u'STRANGER', 'Stranger'),
                               )
    friendship_type=models.CharField(max_length=20, default='FRIEND', choices=FRIENDSHIP_TYPE_CHOICES)
    
    class Meta:
        abstract = True 
    def __unicode__(self):
        return 'Basic relationship for:' + str(self.target_person.username)

class NoCrushRelationship(BasicRelationship): 
    def __unicode__(self):
        return 'No Feelings for:' + str(self.target_person.username)


class CrushRelationship(BasicRelationship):
    
    #dynamically tie in the target person's response as a lookup time optimization (using django signals)
    TARGET_ASSESSMENT_CHOICES = (
                               (0,'Waiting'),
                               (1,'Match'),
                               (2, 'No Match'),
                               )
    target_person_assessment = models.IntegerField(default=0, choices=TARGET_ASSESSMENT_CHOICES) 
    
    def save(self,*args, **kwargs):  
        # check to see if there is a reciprocal relationship
        crusher = self.source_person_profile.user
        crushee = self.target_person
        crushee_profile=crushee.get_profile()
    
        if crusher in crushee_profile.secret_crushees.all():
            #update the crushee's relationship with the crusher
            crushee_relationship = crushee_profile.secretcrushrelationship_set.get(target_person=crusher)
            if crushee_relationship.target_person_assessment!=1:
                print "crushee : " + crushee.last_name + " secretly likes her crusher : " + crusher.last_name
                crushee_relationship.target_person_assessment=1 #interested
                crushee_relationship.save()
            #update this relationship too
            self.target_person_assessment=1
        else: 
            if crusher in crushee_profile.open_crushees.all():
                crushee_relationship = crushee_profile.opencrushrelationship_set.get(target_person=crusher)
                if crushee_relationship.target_person_assessment!=1:
                    print "crushee : " + crushee.last_name + " secretly likes her crusher : " + crusher.last_name
                    crushee_relationship.target_person_assessment=1 #interested
                    crushee_relationship.save()
                self.target_person_assessment=1
        super(CrushRelationship, self).save(*args,**kwargs)
        
    def delete(self,*args, **kwargs):  
        print "delete relationships fired"
        # check to see if there is a reciprocal relationship
        crusher = self.source_person_profile.user
        crushee = self.target_person
        crushee_profile=crushee.get_profile()
    
        if crusher in crushee_profile.secret_crushees.all():

            #update the crushee's relationship with the crusher
            crushee_relationship = crushee_profile.secretcrushrelationship_set.get(target_person=crusher)
            if crushee_relationship.target_person_assessment!=0:
                print "crushee : " + crushee.last_name + " secretly likes her crusher who is deleting the crush: " + crusher.last_name
                crushee_relationship.target_person_assessment=0 #waiting
                crushee_relationship.target_person_assessment=0 #interested
                super(CrushRelationship, self).delete(*args,**kwargs) 
                crushee_relationship.save()
                return
        else: 
            if crusher in crushee_profile.open_crushees.all():
                crushee_relationship = crushee_profile.opencrushrelationship_set.get(target_person=crusher)
                if crushee_relationship.target_person_assessment!=0:
                    print "crushee : " + crushee.last_name + " openly likes her crusher who is deleting the crush : " + crusher.last_name
                    crushee_relationship.target_person_assessment=0 #interested
                    super(CrushRelationship, self).delete(*args,**kwargs) 
                    crushee_relationship.save()
                    return
        super(CrushRelationship, self).delete(*args,**kwargs)        
    
    class Meta:
        abstract=True
    def __unicode__(self):
        return 'Feelings for:' + str(self.target_person.username)

class OpenCrushRelationship(CrushRelationship):    
        # by default, one's feelings for another are not secret
    is_secret = models.BooleanField(default=False)
    
    def __unicode__(self):
        return 'Open Feelings for:' + str(self.target_person.username) 

class SecretCrushRelationship(CrushRelationship):    
    # by default, one's feelings for another are secret
    is_secret = models.BooleanField(default=True)
    
    # -- PAYMENT CHECKS --
    # crusher has to pay to see the results of the match results
    is_results_paid = models.BooleanField(default=False)
    # potentially both the admirer and the crusher can pay for a method to more easily determine a match
    is_lineup_paid=models.BooleanField(default=False)
    is_premium_lineup_paid=models.BooleanField(default=False)
    #crusher can pay to have his crush completely hidden; crushee will have no option to take a discovery lineup test
    is_no_lineup_paid=models.BooleanField(default=False)
    is_lineup_completed=models.BooleanField(default=False)
    num_lineup_contestants=models.IntegerField(default=10) # basic lineup has 10 contestants, but for extra money this number can be configured.
    #admirer can pay to have his feature profiled on crushee's site
    #is_feature_sneak_paid_for=models.BooleanField(default=False)
    
    def __unicode__(self):
        return 'Secret Feelings for:' + str(self.target_person.username) 
    
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
    