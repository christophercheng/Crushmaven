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
        user_profile.facebook_username=fb_profile['username']
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
                
    # find_or_create_user called in two cases:
    # 1) after someone adds a crush from the friend selector dialog (is_this_for_me = false)
    # 2) when facebook authenticates a user (is_this_for_me = true
    def find_or_create_user(self, fb_id, fb_access_token,fb_profile,is_this_for_me):
        print "find_or_create_user called"
        try:
        # Try and find existing user
            user_profile = super(CustomProfileManager,self).get_query_set().get(facebook_id=fb_id)
            user = user_profile.user
            if (is_this_for_me): 
                user_profile.access_token=fb_access_token #if logging user in then update his/her token

                if user.is_active==False:# if the user was previously created (on someone else's crush list, but they are logging for first time)
                    user.is_active=True# then activate their account
                    user.save()
                    # update their profile with facebook data; they're not always obtained indirectly
                    self.update_profile(user_profile, fb_profile)
                    # look for any admirers at this point so their relationships can get updated
                    admirer_relationships = user.crushrelationship_set.all()
                    for relation in admirer_relationships:
                        # for each admirer relationship, change their status to 2 (crush is member, not yet started line-up)
                        relation.target_status = 2
                        relation.date_target_signed_up = datetime.datetime.now()
                        relation.save_wo_reciprocity_check()
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

    date_added = models.DateTimeField(auto_now_add=True)
    
    # keeps track of when the crush signed up
    date_target_signed_up = models.DateTimeField(null=True)

    # keeps track of when the crush responded
    date_target_responded = models.DateField(null=True)    
    
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
    # will have to write an overloaded save function here that checks to see if the platonic friend has a crush
        # if so, then modify that person's target_feeilng and target_status 
    
        # save_wo_checking is to be called by other crush relationships when they want to update the reciprocal relationship
        # this method avoids receiprocal relationship checking which could lead to infinite loop checking
    def save_wo_reciprocity_check(self,*args, **kwargs):
        super(PlatonicRelationship, self).save(*args,**kwargs) 
    
    def save(self,*args, **kwargs):  
        print "saving crush relationship object"
        # check to see if there is a reciprocal relationship i.e. is the crush also an admirer of the admirer?
        source_user = self.source_person_profile.user
        target_user = self.target_person
        target_user_profile=target_user.get_profile()
    
        #if target platonic friend has a crush on this user, then there is no match and platonic friend must be informed
        try:
            targets_crush_relationship = target_user_profile.crushrelationship_set.get(target_person=source_user)
            # if there is a crush match, then update both relationships' target_status
            targets_crush_relationship.target_status=5 # responded-crush status
            targets_crush_relationship.date_target_responded=datetime.date.today()
            targets_crush_relationship.updated_flag = True # show 'updated' on target's crush relation block
            targets_crush_relationship.save_wo_reciprocity_check()

        except PlatonicRelationship.DoesNotExist: #nothing else to do if platonic friend doesn't have a crush on the source user
            super(PlatonicRelationship, self).save(*args,**kwargs)
            return
                
        super(PlatonicRelationship, self).save(*args,**kwargs)
        return
        
# consider putting in a delete function later
          
    
    def __unicode__(self):
        return 'No Feelings for:' + str(self.target_person.username)
    
# need to override the save method 
    # check to see if the platonic friend has a crush on me, if so, then let them know of my evaluation


class CrushRelationship(BasicRelationship):
    
    #dynamically tie in the target person's response as a lookup time optimization (using django signals)
      
    TARGET_STATUS_CHOICES = (
                           (0,'Not Invited (not member)'),
                           (1,'Invited (not member)'),
                           (2,'Not Started Lineup'),
                           (3,'Started Lineup'),
                           (4,'Responded-crush'),
                           (5,'Responded-platonic'),
                           )
    target_status = models.IntegerField(default=0, choices=TARGET_STATUS_CHOICES)
    

    
    # -- PAYMENT CHECKS --
    # admirer has to pay to see the results of the match results
    is_results_paid = models.BooleanField(default=False)
    # the crush target (and potentially the admirer) will need to pay to activate the crush-line-up
    is_lineup_paid=models.BooleanField(default=False)

    is_lineup_completed=models.BooleanField(default=False)
    
    date_invite_last_sent=models.DateTimeField(null=True)
    
    num_lineup_contestants=models.IntegerField(default=10) # basic lineup has 10 contestants. in future, this number may be configurable (for a fee?)

    # need to know whether to display a 'new' or 'updated' ribbon on the crush content block
    updated_flag = models.BooleanField(default=True) # default True so status is New by default
    def resetUpdatedFlag(self):      
        self.updated_flag = False
        # save the change to the database, but don't call this level's save function cause it does too much.
        super(CrushRelationship, self).save()
        return ""
 
    # save_wo_checking is to be called by other crush relationships when they want to update the reciprocal relationship
        # this method avoids receiprocal relationship checking which could lead to infinite loop checking
    def save_wo_reciprocity_check(self,*args, **kwargs):
        super(CrushRelationship, self).save(*args,**kwargs) 
    
    def save(self,*args, **kwargs):  
        print "saving crush relationship object"
        # check to see if there is a reciprocal relationship i.e. is the crush also an admirer of the admirer?
        source_user = self.source_person_profile.user
        target_user = self.target_person
        target_user_profile=target_user.get_profile()
    
        #if admirer is also a crush of the source person's crush list, then we have a match
            # update the target_status_choices
        try:
            targets_crush_relationship = target_user_profile.crushrelationship_set.get(target_person=source_user)
            # if there is a crush match, then update both relationships' target_status
            targets_crush_relationship.target_status=4 # responded-crush status
            targets_crush_relationship.date_target_responded=datetime.date.today()
            targets_crush_relationship.updated_flag = True # show 'updated' on target's crush relation block
            targets_crush_relationship.save_wo_reciprocity_check()
            self.target_status=4
            self.date_target_responded=datetime.date.today()
            self.updated_flag = True #show 'new' or 'updated' on crush relation block
            
        except CrushRelationship.DoesNotExist:
            try:
                target_user_profile.platonicrelationship_set.get(target_person=source_user)
                # if there is a platonic match, then update this relationships' target_status (other user can't know what this user thinks of them)
                self.target_status=5
                self.date_target_responded=datetime.date.today()
                self.updated_flag = True #show 'new' or 'updated' on crush relation block
            except PlatonicRelationship.DoesNotExist:
                # target status is either 0 (not member, not invited) or 2 (member)
                if target_user.is_active == True:
                    self.target_status = 2
                else:
                    self.target_status = 0
                
        super(CrushRelationship, self).save(*args,**kwargs)
        return
        
    # TODO!!! when/where this called?    
    def delete(self,*args, **kwargs):  
        print "delete relationships fired"
        # check to see if there is a reciprocal relationship
        source_user = self.source_person_profile.user
        target_user = self.target_person
        target_user_profile=target_user.get_profile()
            # if the target person had a reciprocal relationship, update that person's (crush's) relationship with the new status
        try:
            targets_crush_relationship = target_user_profile.crushrelationship_set.get(target_person=source_user)
            if targets_crush_relationship.target_status > 2:
                # once a target has started a crush line-up, the crush can no longer be deleted
                return
            targets_crush_relationship.target_status=2
            targets_crush_relationship.save_wo_reciprocity_check()
        except CrushRelationship.DoesNotExist:
            super(CrushRelationship, self).delete(*args,**kwargs)
            return
        super(CrushRelationship, self).delete(*args,**kwargs)
        return
      
    def __unicode__(self):
        return 'Feelings for:' + str(self.target_person.username)

# 10/27/12 couldn't get this class to work cause the UserProfile object was a foreign key on the original model
    # attempts to use a backwards relation fetch through the model (profile.defaultorderedrelationship_set) failed
# use this class instead of CrushRelaionship object when obtaining a sorted list
    # by default the relationship objects will be in the order that they are added, i think :)
#class DefaultOrderedCrushRelationship(CrushRelationship):
#        class Meta:
#            proxy = True
#            ordering = ['target_status']
    
class RelationshipLogBook(models.Model): 
    # a rudimentary log of user initiated transactions specific to a crush
        # simple array of strings
        # purpose: display to user a history of what he's done
    # data includes:
        # 1) date relationship added (plutonic or crush)
        # 2) any sent app invites: when and to whom
        # 3) any credit donations to crush
        # 4) any messages sent to crush
        # 5) date changed from plutonic to crush (expect this to be a rare event)
    relationship = models.OneToOneField(CrushRelationship)

class RelationshipLogEntry(models.Model):
    date = models.DateField(auto_now_add=True)
    description = models.CharField(max_length=140) # have a twitter character limit :)
    Log = models.ForeignKey(RelationshipLogBook)
    
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
    