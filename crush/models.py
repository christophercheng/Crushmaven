from django.db import models
# use signal to create user profile automatically when user created
import urllib, json
import datetime
from django.db import IntegrityError
from django.contrib.auth.models import (UserManager, AbstractUser)
from django.db.models import F

from smtplib import SMTPException
from django.core.mail import send_mail,send_mass_mail

class NotificationSettings(models.Model):
    bNotify_crush_signed_up = models.BooleanField(default=True)
    bNotify_crush_signup_reminder = models.BooleanField(default=True)
    bNotify_crush_started_lineup = models.BooleanField(default=True)
    bNotify_crush_responded = models.BooleanField(default=True)
    bNotify_new_admirer = models.BooleanField(default=True)
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
        print "find_or_create_user called"
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
                    admirer_relationships = user.crush_relationship_set_from_target.all()
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
                fb_profile = urllib.urlopen('https://graph.facebook.com/' + str(fb_id) + '/?access_token=%s' % fb_access_token)
                fb_profile = json.load(fb_profile)
            fb_id=fb_profile['id']
            fb_username = fb_profile.get('username', fb_id)# if no username then grab id
            default_notification_settings=NotificationSettings.objects.create()
            try:
                print "creating username - please fucking work: " + fb_username
                user = self.create_user(username=fb_id,notification_settings=default_notification_settings)
                user.access_token=fb_access_token
                user.is_active=is_this_for_me

                print "completed creation call"
            except IntegrityError:
                print "unable to create a new user for some odd reason"
                return #this would be a bad database error (something out-a-sync!)
            print "calling the update_user function"
            self.update_user(user,fb_profile)
            user.save(update_fields=['is_active','access_token','birthday_year','email','gender','is_single','gender_pref','first_name','last_name'])
        return user

# Custom User Profile Class allows custom User fields to be associated with unique django user instance
class FacebookUser(AbstractUser):
    
    # ------- START OF REQUIRED FIELDS
    access_token = models.CharField(max_length=50)
    
    notification_settings=models.OneToOneField(NotificationSettings)
    
    # this will be populated by the facebook username first, then the facebook id if username is non-existant
    facebook_username = models.CharField(max_length=60) 
    
    GENDER_CHOICES = (
                      (u'M', u'Male'),
                      (u'F', u'Female'),
                      )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    GENDER_PREF_CHOICES = (
                           (u'M',u'Male'),
                           (u'F',u'Female'),
                           (u'B',u'Both')
                           )
    gender_pref=models.CharField(max_length=1,choices=GENDER_PREF_CHOICES)

    is_single = models.BooleanField(default=True)
    # --------  END OF REQUIRED FIELDS
    
    # ----------  START OF OPTIONAL FIELDS
  #  year = 1920
  #  YEARS = []
  #  while year < 2007:
  #      YEARS.append(year)
  #      year +=1
    birthday_year = models.IntegerField(null=True,blank=True,max_length=4,choices=[(y,y) for y in range(1920,datetime.datetime.now().year-6)])
    age_pref_min=models.IntegerField(null=True, blank=True,choices=[(y,y) for y in range(7,80)])
    age_pref_max=models.IntegerField(null=True,blank=True,choices=[(y,y) for y in range(7,100)])
    # by default give every user 1 credit ($1) so that they can acquaint themselves with the crush lineup process
    site_credits = models.IntegerField(default=1000) 
    
    # each user has a set of user lists representing their 'just friends' and their crushes
    # here is an idiosyncrasy of this implementation:
        # to access a user's crushes, you need to go through the user's UserProfile object
        # to access a user's admirers, you need to go through the user's User object

    just_friends_targets = models.ManyToManyField('self', symmetrical=False, through='PlatonicRelationship',related_name='platonic_friend_set')
    crush_targets = models.ManyToManyField('self', symmetrical=False, through='CrushRelationship',related_name='admirer_set')

    # ----------- END  OF OPTIONAL FIELDS
    objects = FacebookUserManager()
    
    def get_facebook_profile(self):
        fb_profile = urllib.urlopen(
                        'https://graph.facebook.com/me?access_token=%s'
                        % self.access_token)
        data = json.load(fb_profile)
        data.update({'picture': self.get_facebook_picture()})
        return data

    def get_facebook_picture(self):
        return u'http://graph.facebook.com/%s/picture?type=large' \
                                                            % self.username
                                                            
    #=========  Crush Filters =========
    
    def get_all_incomplete_crush_relations(self):
        return self.crush_relationship_set_from_source.filter(is_results_paid=False)
    
    def get_nonresponded_incomplete_crush_relations(self):
        return self.crush_relationship_set_from_source.filter(target_status__lt = 4)
    
    def get_responded_incomplete_crush_relations(self):
        return self.crush_relationship_set_from_source.filter(target_status__gt = 3, is_results_paid=False)
    
    def get_completed_crush_relations(self):
        return self.crush_relationship_set_from_source.filter(is_results_paid=True)
    
    #=========  Admirer Filters =========
        
    def get_all_incomplete_admirer_relations(self):
        return self.crush_relationship_set_from_target.filter(date_lineup_finished = None)
    
    def get_all_new_incomplete_admirer_relations(self):
        return self.crush_relationship_set_from_target.filter(is_lineup_paid=False)
        
    def get_all_completed_admirer_relations(self):
        return self.crush_relationship_set_from_target.exclude(date_lineup_finished = None)
    
    #=========  Debug Self Reference Function =========
    def __unicode__(self):
        return '(id:' + str(self.username) +') ' + self.facebook_username
    
# details about each unique crush 
class BasicRelationship(models.Model):
    
    class Meta:
        abstract = True 
    # to find the relationships where a given user is the one being admired:
        # request.user.target_person_relatioinship_set

    date_added = models.DateTimeField(auto_now_add=True)
    
    # list of one or many mutual friends between the admirer and crushee
    #mutual_friend_list = models.ManyToManyField(User,related_name='%(app_label)s_%(class)s_related')
    
    # need to know whether to display a 'new' or 'updated' ribbon on the crush content block
    updated_flag = models.BooleanField(default=True) # default True so status is New by default
    def resetUpdatedFlag(self):      
        print "attempting to reset the update flag"
        self.updated_flag = False
        # save the change to the database, but don't call this level's save function cause it does too much.
        super(BasicRelationship, self).save(update_fields=['updated_flag'])
        return "" # if I don't return "" then for some reason None is actually returned
    
    # how are the admirer and crushee connected
    FRIENDSHIP_TYPE_CHOICES = (
                               (u'FRIEND','Friend'),
                               (u'FRIEND_OF_FRIEND','Friend of Friend'),
                               (u'STRANGER', 'Stranger'),
                               )
    friendship_type=models.CharField(max_length=20, default='FRIEND', choices=FRIENDSHIP_TYPE_CHOICES)
        
    def get_reciprocal_nonresponded_incomplete_crush_relation(self):
        try:
            return self.target_person.get_incomplete_crush_relations().get(target_person=self.source_person)
        except CrushRelationship.DoesNotExist:
            return False
        
    def __unicode__(self):
        return 'Basic relationship for:' + str(self.target_person.facebook_username)

class PlatonicRelationship(BasicRelationship):
    
    source_person=models.ForeignKey(FacebookUser,related_name='platonic_relationship_set_from_source')
    
    target_person=models.ForeignKey(FacebookUser,related_name='platonic_relationship_set_from_target')
    # will have to write an overloaded save function here that checks to see if the platonic friend has a crush
        # if so, then modify that person's target_feeilng and target_status 
 
    def save(self,*args, **kwargs):  
        #  print "saving platonic relationship object"
        if (not self.pk):
            # check to see if there is a reciprocal relationship i.e. is the platonic friend an admirer of the user?
            #if target platonic friend has a crush on this user, then platonic friend must be informed
            try:
                reciprocal_relationship = self.target_person.crush_relationship_set_from_source.get(target_person=self.source_person)
                # if there is a reciprocal relationship, then update both relationships' target_status
                reciprocal_relationship.target_status=5 # responded-crush status
                reciprocal_relationship.date_target_responded=datetime.datetime.now()
                reciprocal_relationship.updated_flag = True # show 'updated' on target's crush relation block
                reciprocal_relationship.save(update_fields=['target_status','date_target_responded','updated_flag'])
    
            except CrushRelationship.DoesNotExist: #nothing else to do if platonic friend doesn't have a crush on the source user
                pass
                
        super(PlatonicRelationship, self).save(*args,**kwargs)
        return
        
# consider putting in a delete function later
          
    def __unicode__(self):
        return 'Platonic relationship with:' + str(self.target_person.first_name) + " " + str(self.target_person.last_name)
    
# need to override the save method 
    # check to see if the platonic friend has a crush on me, if so, then let them know of my evaluation


class CrushRelationship(BasicRelationship):
    source_person=models.ForeignKey(FacebookUser,related_name='crush_relationship_set_from_source')
    
    target_person=models.ForeignKey(FacebookUser,related_name='crush_relationship_set_from_target')
    
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
    
    date_invite_last_sent=models.DateTimeField(null=True,default=None) 
    
    is_lineup_initialized=models.BooleanField(default=False)
    # actual lineup members have a foreign key to a Crush Lineup
    is_lineup_paid=models.BooleanField(default=False)
    # is_lineup_completed=models.BooleanField(default=False) deprecate this - check if date_lineup_finished is not None instead
    date_lineup_started = models.DateTimeField(default=None, null=True)
    number_unrated_lineup_members = models.IntegerField(default=10)
    date_lineup_finished = models.DateTimeField(default=None, null=True)
        # keeps track of when the crush signed up
    date_target_signed_up = models.DateTimeField(default=None,null=True)
    # keeps track of when the crush responded
    date_target_responded = models.DateTimeField(default=None,null=True)    

    # ths is the count of the target person's total admirers (past and present).  It acts as a visual display id for the secret admirer. Set it when the crush is first created.   
    admirer_display_id = models.IntegerField(default=0)
 
    
    # save_wo_checking is to be called by other crush relationships when they want to update the reciprocal relationship
        # this method avoids receiprocal relationship checking which could lead to infinite loop checking
    def save(self,*args,**kwargs):
        print "calling save on crush relationship"
        if (not self.pk):
            # give the relationship a secret admirer id.  this is the unique admirer identifier that is displayed to the crush)
            # get total previous admirers (past and present) and add 1
            self.admirer_display_id=len(self.target_person.crush_relationship_set_from_target.all()) + 1
        
            try:
                # check to see if there is a reciprocal relationship i.e. is the crush also an admirer of the admirer?
                #if admirer is also a crush of the source person's crush list, then we have a match
                # update the target_status_choices
                reciprocal_relationship = self.target_person.crush_relationship_set_from_source.get(target_person=self.source_person)
                reciprocal_relationship.target_status=4 # responded-crush status
                reciprocal_relationship.date_target_responded=datetime.datetime.now()
                reciprocal_relationship.updated_flag = True # show 'updated' on target's crush relation block
                reciprocal_relationship.save(update_fields=['target_status','date_target_responded','updated_flag'])
                self.target_status=4
                # massage the date_target_responded for the crush recipient since we want to mask the initiator
                self.date_target_responded=datetime.datetime.now() # this should be randomized a bit.
                self.updated_flag = True #show 'new' or 'updated' on crush relation block
                
            except CrushRelationship.DoesNotExist:
                # did not find an existing reciprocal crush relationship"
                try:
                    self.target_person.platonic_relationship_set_from_source.get(target_person=self.source_person)
                    # print "found a reciprocal platonic relationship"
                    # if there is a platonic match, then update this relationships' target_status (other user can't know what this user thinks of them)
                    self.target_status=5
                    self.date_target_responded=datetime.datetime.now()
                    self.updated_flag = True #show 'new' or 'updated' on crush relation block
                except PlatonicRelationship.DoesNotExist:
                    # print "did not find a reciprocal platonic or crush relationship"
                    # target status is either 0 (not member, not invited) or 2 (member)
                    if self.target_person.is_active == True:
                        self.target_status = 2
                        # notify the target_person that they have a new admirer
                        self.notify_target_person(crush_relationship=self)
                    else:
                        self.target_status = 0
                   
        else:
            # check if the target status is being changed so that a possible notification can be sent out
            original_relationship = CrushRelationship.objects.get(pk=self.pk)
            if 'update_fields' in kwargs and 'target_status' in kwargs['update_fields'] and (original_relationship.target_status != self.target_status):
                print "target status change: " + str(original_relationship.target_status) + "->" + str(self.target_status) + " for source: " + self.source_person.first_name + " " + self.source_person.last_name + " and target: " + self.target_person.first_name + " " + self.target_person.last_name
                self.notify_source_person(crush_relationship=self,target_status=self.target_status)
        super(CrushRelationship,self).save(*args,**kwargs)

    def notify_target_person(self,crush_relationship):
        print "notifying the target person of a new admirer: "
        target_person=crush_relationship.target_person
        target_person_email=target_person.email
        if (not target_person_email):
                return
        settings=target_person.notification_settings
        from_email="info@crushdiscovery.com"
        try:
            if (settings.bNotify_new_admirer== True):
                subject= "You have a new secret admirer!"
                message="You have a new secret admirer!\nLog in now to find out who it is: " 
                send_mail(subject=subject,message=message,from_email=from_email,recipient_list=[target_person_email])
        except SMTPException:
            print "crap: could not send notification email"
            
    def notify_source_person(self,crush_relationship,target_status):
        print "notifying the source person of a change in target status: " + str(target_status)
        source_person=crush_relationship.source_person
        source_person_email=source_person.email
        settings=source_person.notification_settings
        if (not source_person_email):
                return
        from_email="info@crushdiscovery.com"
        target_person=crush_relationship.target_person
        target_person_name = target_person.first_name + " " + target_person.last_name
        
        try:
            subject=""
            if (target_status==2 and settings.bNotify_crush_signed_up==True): # user signed up
                subject= target_person_name + " signed up!"
                message=target_person_name + " signed up!"
            elif (target_status==3 and settings.bNotify_crush_started_lineup==True): # user started line up
                subject= target_person_name + " started your secret admirer lineup!"
                message=target_person_name + " started your secret admirer lineup!  Expect a response soon."
            elif (target_status > 3 and settings.bNotify_crush_responded==True): # user responded
                subject= target_person_name + " responded to your crush!"
                message=target_person_name + " responded to your crush.  Continue to app to find out what they think of you."
            if subject !="":
                print "attemping to send email to " + str([source_person_email])
                send_mail(subject=subject,message=message,from_email=from_email,recipient_list=[source_person_email])
        except SMTPException:
            print "crap: could not send notification email"
        

    # TODO!!! when/where this called?    
    def delete(self,*args, **kwargs):  
        print "delete relationships fired"
        # check to see if there is a reciprocal relationship
        # if the target person had a reciprocal relationship, update that person's (crush's) relationship with the new status
        try:
            print "attempting to find the crush relationship"
            reciprocal_relationship = self.target_person.crush_relationship_set_from_source.get(target_person=self.source_person)
            if reciprocal_relationship.target_status > 2:
                # once a target has started a crush line-up, the crush can no longer be deleted
                if not ( (self.source_person.username == u'1057460663') | (self.source_person.username == u'651900292')):
                    return # change this to: if user is not a staff (admin) member then return
            reciprocal_relationship.target_status=2
            reciprocal_relationship.save(update_fields=['target_status'])
        except CrushRelationship.DoesNotExist:
            print "cannot find a reciprocal crush relationship to delete!"
            pass
        print "successfully updated target crush's settings, now calling super class's delete to take care of rest"
        super(CrushRelationship, self).delete(*args,**kwargs)
        return
            
    def __unicode__(self):
        return 'CrushRelationship with:' + str(self.target_person.first_name) + " " + str(self.target_person.last_name)

class EmailRecipient(models.Model):
    crush_relationship = models.ForeignKey(CrushRelationship)
    recipient_address=models.CharField(max_length=200) # is this long enough?
    date_sent=models.DateTimeField(auto_now_add=True)
    is_email_crush=models.BooleanField(default=True) # if false, then the email was sent to a mutual friend


# details about each crush's secret admirer lineup (SAL)
class LineupMember(models.Model):
    # each lineup has many lineup members (10 by default) and each lineup member has only one lineup it belongs to (similar to blog entry)
    LineupRelationship = models.ForeignKey(CrushRelationship)
    LineupUser=models.ForeignKey(FacebookUser)
    
    # instead of letting Django auto create a primary ID, let's create a custom one so we can track the sequential position of each member in lineup using the id
    position = models.FloatField() # example x.y where x is id of lineup and y is position in lineup (0 through 9)
    position.primary_key=True
    
    # crush's decision about this person, default is none - so there are actually 2.5 states
    decision = models.NullBooleanField()


class Purchase(models.Model):
    credit_total = models.IntegerField(default=0) # e.g. 100
    price = models.DecimalField( decimal_places=2, max_digits=7 )
    purchaser = models.ForeignKey(FacebookUser)
    purchased_at = models.DateTimeField(auto_now_add=True)
    tx = models.CharField( max_length=250 )
    
  
    def save(self,*args, **kwargs): 
        print "purchase save overridden function called" 
        if not self.pk:
            print "creating purchase  object with new credit total: " + str(self.credit_total)
            print "SERIOUSLY CREATE THIS DAMN PURCHASE OBJECT!"
            # give the relationship a secret admirer id.  this is the unique admirer identifier that is displayed to the crush)
            # get total previous admirers (past and present) and add 1
            current_user = self.purchaser
            current_user.site_credits = F('site_credits') + self.credit_total     
            current_user.save(update_fields = ['site_credits']) 
        return super(Purchase, self).save(*args,**kwargs)
    
# 10/27/12 couldn't get this class to work cause the UserProfile object was a foreign key on the original model
    # attempts to use a backwards relation fetch through the model (profile.defaultorderedrelationship_set) failed
# use this class instead of CrushRelaionship object when obtaining a sorted list
    # by default the relationship objects will be in the order that they are added, i think :)
#class DefaultOrderedCrushRelationship(CrushRelationship):
#        class Meta:
#            proxy = True
#            ordering = ['target_status']