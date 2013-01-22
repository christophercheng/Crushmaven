from django.db import models
# use signal to create user profile automatically when user created
import datetime
from smtplib import SMTPException
from django.core.mail import send_mail
import random
from django.conf import settings
from crush.models.user_models import FacebookUser
import crush.models.miscellaneous_models

# details about each unique crush 
class BasicRelationship(models.Model):
    
    class Meta:
        abstract = True 
        # this allows the models to be broken into separate model files
        app_label = 'crush' 
    # to find the relationships where a given user is the one being admired:
        # request.user.target_person_relatioinship_set

    date_added = models.DateTimeField(auto_now_add=True)
    
        
    # how are the admirer and crushee connected
    FRIENDSHIP_TYPE_CHOICES = (
                               (0,'Friend'),
                               (1,'Friend of Friend'),
                               (2,'Stranger'),
                               )
    friendship_type=models.IntegerField(max_length=1,default=0,choices=FRIENDSHIP_TYPE_CHOICES)#, choices=FRIENDSHIP_TYPE_CHOICES)
    
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
    

        
    def get_reciprocal_nonresponded_incomplete_crush_relation(self):
        try:
            return self.target_person.get_incomplete_crush_relations().get(target_person=self.source_person)
        except CrushRelationship.DoesNotExist:
            return False
        
    def __unicode__(self):
        return 'Basic relationship for:' + str(self.target_person.facebook_username)

class PlatonicRelationship(BasicRelationship):
    
    class Meta:
        # this allows the models to be broken into separate model files
        app_label = 'crush' 
        
    source_person=models.ForeignKey(FacebookUser,related_name='platonic_relationship_set_from_source')
    
    target_person=models.ForeignKey(FacebookUser,related_name='platonic_relationship_set_from_target')
    # will have to write an overloaded save function here that checks to see if the platonic friend has a crush
        # if so, then modify that person's target_feeilng and target_status 
 
    def save(self,*args, **kwargs):  
        #  print "saving platonic relationship object"
        if (not self.pk):
            try:
                self.source_person.just_friends_targets.get(username=self.target_person.username)
                print "existing platonic relationship detected. doing nothing more"
                return False
            except FacebookUser.DoesNotExist:
                pass
            try:
                self.source_person.crush_targets.get(username=self.target_person.username)
                print "existing crush relationship detected. doing nothing more"
                return False
            except FacebookUser.DoesNotExist:
                pass
            # check to see if there is a reciprocal relationship i.e. is the platonic friend an admirer of the user?
            #if target platonic friend has a crush on this user, then platonic friend must be informed
            try:
                reciprocal_relationship = self.target_person.crush_relationship_set_from_source.get(target_person=self.source_person)
                # if there is a reciprocal relationship, then update both relationships' target_status
                reciprocal_relationship.target_status=5 # responded-crush status
                response_wait= random.randint(settings.CRUSH_RESPONSE_DELAY_START, settings.CRUSH_RESPONSE_DELAY_END)
                reciprocal_relationship.date_target_responded=datetime.datetime.now() + datetime.timedelta(0,response_wait)
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
    
    class Meta:
        # this allows the models to be broken into separate model files
        app_label = 'crush' 
            
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
    
    lineup_members = models.ManyToManyField(FacebookUser, through='LineupMembership')
    
    
    LINEUP_INITIALIZATION_STATUS_CHOICES = (
                           (0,settings.LINEUP_STATUS_CHOICES[0]),# initialization in progress
                           (1,settings.LINEUP_STATUS_CHOICES[1]),# successfully initialized
                           (2,settings.LINEUP_STATUS_CHOICES[2]),# error - source doesn't have enough friends
                           (3,settings.LINEUP_STATUS_CHOICES[3]),# error - target doesn't have enough friends
                           (4,settings.LINEUP_STATUS_CHOICES[4]),# error - facebook data fetch error
                           (5,settings.LINEUP_STATUS_CHOICES[5]) # unknown error
                           )
    lineup_initialization_status = models.IntegerField(default=None, choices=LINEUP_INITIALIZATION_STATUS_CHOICES,null=True)
    # lineup initialized and paid can be combined into a single state variable 

    is_lineup_paid=models.BooleanField(default=False)
    # is_lineup_completed=models.BooleanField(default=False) deprecate this - check if date_lineup_finished is not None instead
    date_lineup_started = models.DateTimeField(default=None, null=True)
    
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
            
            # make sure we're not adding a duplicate
            try:
                self.source_person.crush_targets.get(username=self.target_person.username)
                print "duplicate crush relationships detected. doing nothing more"
                return False
            except FacebookUser.DoesNotExist:
                pass
            try:
                print "testing for existing platonic relationship"
                existing_platonic_relationship = self.source_person.platonic_relationship_set_from_source.get(target_person=self.target_person)
                print "existing platonic relationship detected. deleting it before moving on"
                existing_platonic_relationship.delete()
            except PlatonicRelationship.DoesNotExist:
                pass
            # give the relationship a secret admirer id.  this is the unique admirer identifier that is displayed to the crush)
            # get total previousadmirers (past and present) and add 1
            self.admirer_display_id=len(self.target_person.crush_relationship_set_from_target.all()) + 1
          
            try:
                # check to see if there is a reciprocal relationship i.e. is the crush also an admirer of the admirer?
                #if admirer is also a crush of the source person's crush list, then we have a match
                # update the target_status_choices
                reciprocal_relationship = self.target_person.crush_relationship_set_from_source.get(target_person=self.source_person)
                reciprocal_relationship.target_status=4 # responded-crush status
                # determine the response wait period
                response_wait= random.randint(settings.CRUSH_RESPONSE_DELAY_START, settings.CRUSH_RESPONSE_DELAY_END)
                reciprocal_relationship.date_target_responded=datetime.datetime.now() + datetime.timedelta(0,response_wait)
                reciprocal_relationship.updated_flag = True # show 'updated' on target's crush relation block
                reciprocal_relationship.save(update_fields=['target_status','date_target_responded','updated_flag'])
                self.target_status=4
                # massage the date_target_responded for the crush recipient since we want to mask the initiator
                self.date_target_responded=datetime.datetime.now() + datetime.timedelta(0,response_wait) # this should be randomized a bit.
                
                self.updated_flag = True #show 'new' or 'updated' on crush relation block
                
            except CrushRelationship.DoesNotExist:
                # did not find an existing reciprocal crush relationship"
                try:
                    self.target_person.platonic_relationship_set_from_source.get(target_person=self.source_person)
                    # print "found a reciprocal platonic relationship"
                    # if there is a platonic match, then update this relationships' target_status (other user can't know what this user thinks of them)
                    self.target_status=5
                    response_wait= random.randint(settings.CRUSH_RESPONSE_DELAY_START, settings.CRUSH_RESPONSE_DELAY_END)
                    self.date_target_responded=datetime.datetime.now() + datetime.timedelta(0,response_wait)
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
                        # see if any active users are friends with this new inactive crush - solicit their help
                        #self.target_person.find_active_friends_of_inactivated_crush()         
            # check to see if there are any incomplete lineups that have this crush as an undecided member, if so , preset their decision
            incomplete_admirer_rels = self.source_person.crush_relationship_set_from_target.filter(date_lineup_finished=None)
            for rel in incomplete_admirer_rels:
                try:
                    duplicate_lineup_membership = rel.lineupmembership_set.get(lineup_member=self.target_person)
                    duplicate_lineup_membership.decision = 0
                    duplicate_lineup_membership.save(update_fields=['decision'])
                except crush.models.miscellaneous_models.LineupMembership.DoesNotExist:
                    pass      
        else:
            # check if the target status is being changed so that a possible notification can be sent out
            original_relationship = CrushRelationship.objects.get(pk=self.pk)
            if 'update_fields' in kwargs and 'target_status' in kwargs['update_fields'] and (original_relationship.target_status != self.target_status):
                print "target status change: " + str(original_relationship.target_status) + "->" + str(self.target_status) + " for source: " + self.source_person.first_name + " " + self.source_person.last_name + " and target: " + self.target_person.first_name + " " + self.target_person.last_name
                self.notify_source_person(crush_relationship=self,target_status=self.target_status)
        print "finished saving crush relationship object: 12"
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
        return 'CrushRelationship:'  + str(self.source_person.first_name) + " " + str(self.source_person.last_name) + " -> " + str(self.target_person.first_name) + " " + str(self.target_person.last_name)
