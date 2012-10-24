from django.db import models
from django.contrib.auth.models import User
# use signal to create user profile automatically when user created
from facebook.models import FacebookProfile
import urllib, json
import datetime
from django.db import IntegrityError

# a custom User Profile manager class to encapsulate common actions taken on a table level (not row-user level)
class CustomProfileManager(models.Manager):
    
    # helper function used by find_or_create_user function to separate profile data extraction from facebook and insertion into the user profile object
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
                
    # who calls this function? where/when is it used?
    def find_or_create_user(self, fb_id, fb_access_token,fb_profile,is_this_for_me):
        try:
        # Try and find existing user
            user_profile = super(CustomProfileManager,self).get_query_set().get(facebook_id=fb_id)
            user = user_profile.user
            if (is_this_for_me): #if logging user in then update his/her token
                user_profile.access_token=fb_access_token

                if user.is_active==False:# if the user was previously created (on someone else's crush list, but they are logging for first time)
                    user.is_active=True# then activate their account
                    user.save()  
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

    # by default give every user 1 credit ($1) so that they can acquaint themselves with the crush lineup process
    site_credits = models.IntegerField(default=1) 
    
    
    # each user has a set of user lists representing their 'just friends' and their crushes
    # here is an idiosyncrasy of this implementation:
        # to access a user's crushes, you need to go through the user's UserProfile object
        # to access a user's admirers, you need to go through the user's User object

    just_friends_targets = models.ManyToManyField(User, through='PlatonicRelationship',related_name='friends_not_into_me_set')
    crush_targets = models.ManyToManyField(User, through='CrushRelationship',related_name='admirers_set')
    
    def __unicode__(self):
        return '(id:' + str(self.user.id) +') '+ self.user.username


# details about each unique crush 
class BasicRelationship(models.Model):


    # QUESTION: why is the source person's user profile instead of the actual user himself not stored
    # ANSWER: django disallows the creation of a model with two foreign keys of the same type
    
    # using the source person's profile as a foreign key is necessary because django requires that the intermediate 'through' 
    # relationship must have one foreign key that points back to the target model
    source_person_profile=models.ForeignKey(UserProfile)
    # to find the crush relationships of a given user (where they are the admirer):
        # request.user.get_profile().user_is_source_person_relationship_set <= this makes sense but doesn't differentiate crushes from just-friends
        # request.user.get_profile().crushrelationship_set.all() <= this is confusing
    # to find the plutonic friendships of a given user:
        # request.user.get_profile().nocrushrelationship_set.all() 
            # this doesn't say whether the set is the set of relationships where user is source or target
    
    target_person=models.ForeignKey(User)
    # to find the relationships where a given user is the one being admired:
        # request.user.target_person_relatioinship_set

    

    # date_feelings_changed keeps track of when the crush list changed
    date_added = models.DateField(auto_now_add=True)
    
    # list of one or many mutual friends between the admirer and crushee
    #mutual_friend_list = models.ManyToManyField(User,related_name='%(app_label)s_%(class)s_related')
    
    # how are the admirer and crushee connected
    FRIENDSHIP_TYPE_CHOICES = (
                               (u'FRIEND','Friend'),
                               (u'FRIEND_OF_FRIEND','Friend of Friend'),
                               (u'STRANGER', 'Stranger'),
                               )
    friendship_type=models.CharField(max_length=20, default='FRIEND', choices=FRIENDSHIP_TYPE_CHOICES)
    
    class Meta:
        abstract = True 
    def __unicode__(self):
        return 'Basic relationship for:' + str(self.target_person.username)

class PlatonicRelationship(BasicRelationship): 
    def __unicode__(self):
        return 'No Feelings for:' + str(self.target_person.username)


class CrushRelationship(BasicRelationship):
    
    #dynamically tie in the target person's response as a lookup time optimization (using django signals)
    TARGET_FEELING_CHOICES = (
                               (0,'Unknown'),
                               (1,'Crush'),
                               (2, 'Platonic'),
                               )
    TARGET_STATUS_CHOICES = (
                           (0,'Invites Not Sent'),
                           (1,'Invites Sent'),
                           (2,'Signed Up'),
                           (3,'Started Lineup'),
                           (4,'Responded'),
                           )
    
    target_feeling = models.IntegerField(default=0, choices=TARGET_FEELING_CHOICES) 
    target_status = models.IntegerField(default=0, choices=TARGET_STATUS_CHOICES)
    
    # -- PAYMENT CHECKS --
    # admirer has to pay to see the results of the match results
    is_results_paid = models.BooleanField(default=False)
    # the crush target (and potentially the admirer) will need to pay to activate the crush-line-up
    is_lineup_paid=models.BooleanField(default=False)

    is_lineup_completed=models.BooleanField(default=False)
    num_lineup_contestants=models.IntegerField(default=10) # basic lineup has 10 contestants. in future, this number may be configurable (for a fee?)

    # TODO!!! when/where this called?
    def save(self,*args, **kwargs):  
        # check to see if there is a reciprocal relationship i.e. is the crush also an admirer of the admirer?
        admirer = self.source_person_profile.user
        crush = self.target_person
        crush_profile=crush.get_profile()
    
        # check first to see if the admirer (source person) is in the crush's (target person's) just_friend_list; then check if in the target person's crush_list
    
        #if source person is in the target's just_friend_list, then we don't have a match
        if admirer in crush_profile.just_friends_targets.all():
            self.target_person_response=2   
    
        #if admirer is also a crush of the source person's crush list, then we have a match
        else :
            if admirer in crush_profile.crush_targets.all():
                #update 1 of 2: the target person's relationship with the source person (the admirer)
                crush_relationship = crush_profile.crushrelationship_set.get(target_person=admirer)
                if crush_relationship.target_person_response!=1:
                    print "crush : " + crush.last_name + " secretly likes her crusher : " + admirer.last_name
                    crush_relationship.target_person_response=1 #interested
                    crush_relationship.save()
            # update 2 of 2: this relationship!!!
                self.target_person_response=1
 
        super(CrushRelationship, self).save(*args,**kwargs)
        
    # TODO!!! when/where this called?    
    def delete(self,*args, **kwargs):  
        print "delete relationships fired"
        # check to see if there is a reciprocal relationship
        admirer = self.source_person_profile.user
        crush = self.target_person
        crush_profile=crush.get_profile()
    
        if admirer in crush_profile.crush_targets.all():

            #update the target person's (crush's) relationship with the source person (admirer)
            crush_relationship = crush_profile.crushrelationship_set.get(target_person=admirer)
            if crush_relationship.target_person_response!=0:
                print "crush : " + crush.last_name + " secretly likes her crusher who is deleting the crush: " + admirer.last_name
                crush_relationship.target_person_response=0 #waiting
                super(CrushRelationship, self).delete(*args,**kwargs) 
                # TODO!!! need to alert the target person of the change!
                crush_relationship.save()
                return
 
        super(CrushRelationship, self).delete(*args,**kwargs)        
    
    def __unicode__(self):
        return 'Feelings for:' + str(self.target_person.username)


    
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
    