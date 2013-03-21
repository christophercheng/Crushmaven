from django.db import models
# use signal to create user profile automatically when user created
from datetime import  datetime,timedelta,date
import random
from django.conf import settings
from crush.models.user_models import FacebookUser
from django.db.models import F
import requests
from email import utils
import time
from django.db import transaction
# details about each unique crush 
class BasicRelationship(models.Model):
    
    class Meta:
        abstract = True 
        # this allows the models to be broken into separate model files
        app_label = 'crush' 

    date_added = models.DateTimeField(auto_now_add=True)    

    FRIENDSHIP_TYPE_CHOICES = (
                               (0,'Friend'),
                               (1,'Friend of Friend'),
                               (2,'Stranger'),
                               )
    friendship_type=models.IntegerField(max_length=1,default=0,choices=FRIENDSHIP_TYPE_CHOICES)#, choices=FRIENDSHIP_TYPE_CHOICES))
    
    # need to know whether to display a 'new' or 'updated' ribbon on the crush content block
    updated_flag = models.BooleanField(default=True) # default True so status is New by default
    def resetUpdatedFlag(self):      
        print "attempting to reset the update flag"
        self.updated_flag = False
        # save the change to the database, but don't call this level's save function cause it does too much.
        super(BasicRelationship, self).save(update_fields=['updated_flag'])
        return "" # if I don't return "" then for some reason None is actually returned
        
    def __unicode__(self):
        return 'Basic relationship for:' + str(self.target_person.facebook_username)

class PlatonicRelationshipQuerySet(models.query.QuerySet):
    
    def all_friends(self, source_user):
        return source_user.platonic_relationship_set_from_source.all()
    
class PlatonicRelationshipManager(models.Manager):
    def get_query_set(self):
        return PlatonicRelationshipQuerySet(self.model,using=self._db)
    # this magic function prevents us from defining duplicate Queryset functions in our manager
    def __getattr__(self,name):
        return getattr(self.get_query_set(),name)

class PlatonicRelationship(BasicRelationship):
    
    class Meta:
        # this allows the models to be broken into separate model files
        app_label = 'crush' 
        
    objects = PlatonicRelationshipManager()
        
    source_person=models.ForeignKey(FacebookUser,related_name='platonic_relationship_set_from_source')  
    target_person=models.ForeignKey(FacebookUser,related_name='platonic_relationship_set_from_target')
 
    rating = models.IntegerField(default=None,max_length=1,blank=True,null=True) # how source rated the target's attraction
    #rating_comment = models.CharField(max_length=50,default=None,blank=True,null=True)
    #rating_visible = models.BooleanField(default=True) # whether or not this rating/comment show up on user's public profile
 
    @transaction.commit_on_success # rollback entire function if something fails
    def save(self,*args, **kwargs):  
        #  print "saving platonic relationship object"
        if (not self.pk): # if creating a new platonic relationship
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
                reciprocal_relationship.date_target_responded=datetime.now()
                reciprocal_relationship.target_platonic_rating = self.rating
                reciprocal_relationship.updated_flag = True # show 'updated' on target's crush relation block
                reciprocal_relationship.save(update_fields=['target_status','date_target_responded','target_platonic_rating','updated_flag']);
    
            except CrushRelationship.DoesNotExist: #nothing else to do if platonic friend doesn't have a crush on the source user
                pass
        super(PlatonicRelationship, self).save(*args,**kwargs)
        return
        
# consider putting in a delete function later
          
    def __unicode__(self):
        return 'Platonic Relation:' + str(self.source_person.first_name) + " " + str(self.source_person.last_name) + " -> " + str(self.target_person.first_name) + " " + str(self.target_person.last_name)

class CrushRelationshipQuerySet(models.query.QuerySet):
    
    def all_crushes(self,admirer_user):
        return admirer_user.crush_relationship_set_from_source.all()
    
    def progressing_crushes(self,admirer_user):   
        #print "progressing crushes"
        crush_relationships = admirer_user.crush_relationship_set_from_source          
        # exclude any known responded relationships and completed relationship
            # both those relationships contain a date_target_responded date that is in the past 
            # if a relationship has a future date_target_responded date, then include it.
        return crush_relationships.exclude(date_target_responded__lt = datetime.now())     
 
    # known responded crushes are can be shown to both users
    def visible_responded_crushes(self,admirer_user):
        #print "known responded crushes"
        crush_relationships = admirer_user.crush_relationship_set_from_source
        # first exclude completed relationship, then exclude all truly unresponded crushes, then exclude unknown responded crushes
        # ie. all relationships that arent' paid (not completed) and target status > 4 (not progressing) and date_target_responded is in past  (exclude date=none and  date in future)
        return crush_relationships.filter(date_target_responded__lt=datetime.now(), is_results_paid=False )
    # unknown responded crushes cannot be shown to either user because they are in a wait period
    def hidden_responded_crushes(self,admirer_user):
        crush_relationships = admirer_user.crush_relationship_set_from_source
        # get any crush relationships where we know the response but the date responded is either:
            # None: we're waiting for original admirer to see response
            # Future date: we're not telling the admirer that their crush has already decided that theyy're not interseted
        return crush_relationships.filter(target_status__gt = 3).exclude( date_target_responded__lt=datetime.now() )
    
    def completed_crushes(self,admirer_user):
        crush_relationships = admirer_user.crush_relationship_set_from_source
        return crush_relationships.filter(is_results_paid=True)
    
    def all_admirers(self,crush_user):
        return crush_user.crush_relationship_set_from_target.all()
    
    def new_admirers(self,crush_user):
        return crush_user.crush_relationship_set_from_target.filter(target_status__lt = 3)
    
    def progressing_admirers(self,crush_user):
        #print "progressing admirers" 
        # progressing admirers are all relationships where the user is the target and date_lineup_finished is not set
        admirer_relationships = crush_user.crush_relationship_set_from_target.filter(date_lineup_finished=None)\
        # there is one exception: exclude any admirers who were previously added as the user's crush (and who responded)
            # (hint: relationship will have target_status set to 4 or 5 and the relationship's lineup will never be initialized)     
        admirer_relationships = admirer_relationships.exclude(target_status__gt = 3, lineup_initialization_status = None)
        return admirer_relationships
      
    def past_admirers(self,crush_user):
        return crush_user.crush_relationship_set_from_target.exclude(date_lineup_finished=None)
    
class CrushRelationshipManager(models.Manager):
    def get_query_set(self):
        return CrushRelationshipQuerySet(self.model,using=self._db)
    # this magic function prevents us from defining duplicate Queryset functions in our manager
    def __getattr__(self,name):
        return getattr(self.get_query_set(),name)

class CrushRelationship(BasicRelationship):
    
    class Meta:
        # this allows the models to be broken into separate model files
        app_label = 'crush' 
    
    objects = CrushRelationshipManager()
            
    source_person=models.ForeignKey(FacebookUser,related_name='crush_relationship_set_from_source')
    target_person=models.ForeignKey(FacebookUser,related_name='crush_relationship_set_from_target')
    
    #dynamically tie in the target person's response as a lookup time optimization
    TARGET_STATUS_CHOICES = (
                           (0,'Not Invited (not member)'),
                           (1,'Invited (not member)'),
                           (2,'Not Started Lineup'),
                           (3,'Started Lineup'),
                           (4,'Responded-crush'),
                           (5,'Responded-platonic'),
                           )
    target_status = models.IntegerField(default=0, choices=TARGET_STATUS_CHOICES)
    target_platonic_rating = models.IntegerField(null=True,default=None,blank=True)
    # -- PAYMENT CHECKS --
    # admirer has to pay to see the results of the match results
    is_results_paid = models.BooleanField(default=False)
    date_messaging_expires = models.DateField(default=None,null=True,blank=True)
    is_platonic_rating_paid=models.BooleanField(default=False)

    date_invite_last_sent=models.DateTimeField(null=True,default=None,blank=True) 
    
    LINEUP_INITIALIZATION_STATUS_CHOICES = (                                       
                           (0,settings.LINEUP_STATUS_CHOICES[0]),# initialization in progress
                           (1,settings.LINEUP_STATUS_CHOICES[1]),# successfully initialized
                           (2,settings.LINEUP_STATUS_CHOICES[2]),# error - source doesn't have enough friends
                           (3,settings.LINEUP_STATUS_CHOICES[3]),# error - target doesn't have enough friends
                           (4,settings.LINEUP_STATUS_CHOICES[4]),# error - facebook data fetch error
                           (5,settings.LINEUP_STATUS_CHOICES[5]) # unknown error
                           )
    lineup_initialization_status = models.IntegerField(default=None, choices=LINEUP_INITIALIZATION_STATUS_CHOICES,null=True,blank=True)
    # lineup initialized and paid can be combined into a single state variable 
    is_lineup_paid=models.BooleanField(default=False)

    date_lineup_started = models.DateTimeField(default=None, null=True,blank=True)
    
    date_lineup_finished = models.DateTimeField(default=None, null=True,blank=True)
        # keeps track of when the crush signed up
    date_target_signed_up = models.DateTimeField(default=None,null=True,blank=True)
    # keeps track of when the crush responded
    date_target_responded = models.DateTimeField(default=None,null=True,blank=True)    
    # ths is the count of the target person's total admirers (past and present).  It acts as a visual display id for the secret admirer. Set it when the crush is first created.   
    admirer_display_id = models.IntegerField(default=0, max_length=60)
    # short message that admirer can leave for crush (as seen in their lineup
    #admirer_comment = models.CharField(default=None,max_length=50, blank=True,null=True)
    
    @transaction.commit_on_success # rollback entire function if something fails
    def save(self,*args,**kwargs):
        print "calling save on crush relationship"
        if (not self.pk): # this is a newly created crush relationship
            try:  # make sure we're not adding a duplicate
                self.source_person.crush_targets.get(username=self.target_person.username)
                print "duplicate crush relationships detected. doing nothing more"
                return False
            except FacebookUser.DoesNotExist:
                pass # no duplicate crush relationship found
            try: # check if there is an existing platonic relationship, if so, delete it first
                existing_platonic_relationship = self.source_person.platonic_relationship_set_from_source.get(target_person=self.target_person)
                print "existing platonic relationship detected. deleting it before moving on"
                existing_platonic_relationship.delete()
            except PlatonicRelationship.DoesNotExist:
                pass # no duplicate platonic relationship found so continue on
            try:
                # check to see if there is a reciprocal crush relationship i.e. the crush also an admirer of the admirer
                reciprocal_relationship = CrushRelationship.objects.all_crushes(self.target_person).get(target_person=self.source_person)
                #if we have a match, update the target_status of both relationship
                reciprocal_relationship.target_status=4 # responded-crush status
                self.target_status=4
                # let the other relationship know right away that there is a response by setting the date_target_responded field to current time
                    # NOTE: we do not set the newly created relationship yet.  We wait for the original admirer to see the response
                    # this ordered delay obfuscates the originator of the mutual crushes. it also increases chance that admirer pays to see response
                reciprocal_relationship.date_target_responded=datetime.now()
                # both relationships should show the 'updated' or 'new' signs when first displayed to their respective users
                reciprocal_relationship.updated_flag = True # show 'updated' on target's crush relation block
                self.updated_flag = True #show 'new' or 'updated' on crush relation block
                # save the reciprocal crush relationship to database
                reciprocal_relationship.save(update_fields=['target_status','date_target_responded','updated_flag'])
                if reciprocal_relationship.is_results_paid==True:
                    # edge case handling - the crush used to be a platonic friend and we need to auto set the date_target_responded cause no other process will do this
                    response_wait= random.randint(settings.CRUSH_RESPONSE_DELAY_START, settings.CRUSH_RESPONSE_DELAY_END)
                    self.date_target_responded=datetime.now() + timedelta(minutes = response_wait)
                    # notify the source person (notification will go out at the future date_target_responded time
                    self.notify_source_person()
            except CrushRelationship.DoesNotExist: # did not find an existing reciprocal crush relationship          
                try:  # Now look for a reciprocal platonic relationship (crush previously added admirer as platonic friend in a lineup)
                    PlatonicRelationship.objects.all_friends(self.target_person).get(target_person=self.source_person)
                    # print "Found a reciprocal platonic relationship"
                    # Update only this relationships' target_status (for anonymity sake, other user can't know that this user likes them)
                    self.target_status=5
                    # don't tell this user that their crush isn't attracted to them right away
                        # without delay, admirer would eventually realize that immediate responses = negative responses - and not pay to see response
                    response_wait= random.randint(settings.CRUSH_RESPONSE_DELAY_START, settings.CRUSH_RESPONSE_DELAY_END)
                    self.date_target_responded=datetime.now() + timedelta(minutes=response_wait)
                    self.updated_flag = True #show 'new' or 'updated' on crush relation block
                    # notify the source person (notification will go out at the future date_target_responded time
                    self.notify_source_person()
                except PlatonicRelationship.DoesNotExist:
                    # print "did not find a reciprocal platonic or crush relationship"
                    if self.target_person.is_active == True:
                        # let admirer know that their crush is already a member 
                        self.target_status = 2 
                        # notify the target_person that they have a new admirer
                        self.notify_target_person()
                    else: # admirer is not an existing user (or is a user but not activated yet)
                        self.target_status = 0
                        # see if any active users are friends with this new inactive crush - solicit their help
                        #self.target_person.find_active_friends_of_inactivated_crush()         
            # no need to check to see if there are any incomplete lineups that have this crush as an undecided member,
                # this check is performed when the lineup slide is pulled
            # finally, give the relationship a secret admirer id.  this is the unique admirer identifier that is displayed to the crush)
                # get total previous admirers (past and present) and add 1, hopefully this won't create a 
            self.admirer_display_id=len(self.target_person.crush_relationship_set_from_target.all()) + 1
        else: # This is an existing crush relationship, just perform updates and potentially send out notfications 
            if 'update_fields' in kwargs:
                # get the original relationship (which excludes the uncommitted changes)
                original_relationship = CrushRelationship.objects.get(pk=self.pk)
                # if the admirer paid to see results of a reciprocal crush relationship (not platonic), then let the mutually attracted crush know
                # also look for any messages that were previously sent to the source person and set their status to accepted (if they were previously rejected ie hidden)
                if 'is_results_paid' in kwargs['update_fields'] and (original_relationship.is_results_paid != self.is_results_paid):
                    #print "admirer paid to see crush response result for source: " + self.source_person.get_name() + " and target: " + self.target_person.get_name()
                    try:                     
                        # find the reciprocal crush relationship if it exists ( but only if the reciprocal relationship doesn't already know - use date_target_responded to figure that out)
                        reciprocal_crush_relationship=CrushRelationship.objects.all_crushes(self.target_person).get(target_person=self.source_person)#,date_target_responded=None)
                        if reciprocal_crush_relationship.date_target_responded==None:
                            # set the reciprocal crush relationship date_target_responded field
                            reciprocal_crush_relationship.date_target_responded=datetime.now()
                            reciprocal_crush_relationship.save(update_fields=['date_target_responded'])
                            # send the other relationship's admirer a notification
                            reciprocal_crush_relationship.notify_source_person()
                            
                        else:
                            # look for previously hidden messages from the target person and make them acceptable (to read)
                            reciprocal_crush_relationship.source_person.sent_messages.filter(recipient=reciprocal_crush_relationship.target_person,moderation_status=settings.STATUS_REJECTED).update(moderation_status=settings.STATUS_ACCEPTED,recipient_deleted_at=None)
                    except Exception as e: # there is a reciprocal platonic relationship (crush is not mutually attracted to admirer) 
                        print e
                        pass # do nothing
                if 'target_status' in kwargs['update_fields'] and (original_relationship.target_status != self.target_status):
                    #print "target status change: " + str(original_relationship.target_status) + "->" + str(self.target_status) + " for source: " + self.source_person.get_name() + " and target: " + self.target_person.get_name()
                    self.notify_source_person()
        # Don't forget to commit the relationship's changes to database!
        super(CrushRelationship,self).save(*args,**kwargs)
    
    # for crush relationships in a hidden responded mode:
        # 1: crush already admirer as platonic friend so date_target_responded is in future
        # 2: crush added a lineup member as an attraction but date_target responded set to None so we can let admirer view response first
    # we should show user a false status instead (user signed up)
    def get_display_status(self):
        target_status=self.target_status
        if target_status < 4:
            return target_status
        if self.date_target_responded==None or self.date_target_responded > datetime.now():
            return 2
        else:
            return target_status
        
    def can_message(self):
    
        if self.date_messaging_expires == None or date.today() > self.date_messaging_expires:
            return False
        else:
            return True

        
    def get_target_platonic_rating_display(self):
        if self.target_platonic_rating!=None:
            return settings.PLATONIC_RATINGS[self.target_platonic_rating]
        
    def handle_lineup_paid(self): 
        feature_cost=int(settings.FEATURES['1']['COST'])
        if self.target_person.site_credits < feature_cost:
            return False
        self.is_lineup_paid=True   
        # only set the target status to 3 (started lineup) if it was less than 3 previously
            # if user was put in crush's first lineup position, then the target status will be 4 or 5 and shouldn't be changed
        if self.target_status < 3:
            self.updated_flag=True
            self.target_status = 3
            self.save(update_fields=['is_lineup_paid','target_status','updated_flag'])
        else:
            self.save(update_fields=['is_lineup_paid'])
        self.target_person.site_credits=F('site_credits') - feature_cost    
        self.target_person.save(update_fields=['site_credits'])
        print "handle_lineup_paid called"
        return True # must return true or else caller thinks payment failed
        
    def handle_results_paid(self):
        feature_cost=int(settings.FEATURES['2']['COST'])
        if self.source_person.site_credits < feature_cost:
            return False
        self.source_person.site_credits=F('site_credits') - feature_cost
        self.is_results_paid=True
        self.updated_flag=True
        # change the status of relationship's is_results_paid and save the object
        self.save(update_fields=['is_results_paid','updated_flag'])
        self.source_person.save(update_fields=['site_credits'])
        return True #must return True or else caller thinks payment failed
    
    def handle_rating_paid(self):
        feature_cost=int(settings.FEATURES['3']['COST'])
        if self.source_person.site_credits < feature_cost:
            return False
        self.source_person.site_credits=F('site_credits') - feature_cost
        self.is_platonic_rating_paid=True
        # change the status of relationship's is_ratings_paid and save the object
        self.save(update_fields=['is_platonic_rating_paid'])
        self.source_person.save(update_fields=['site_credits'])
        return True #must return True or else caller thinks payment failed
    
    def handle_messaging_paid(self):
        feature_cost=int(settings.FEATURES['4']['COST'])
        if self.source_person.site_credits < feature_cost:
            return False
        self.source_person.site_credits=F('site_credits') - feature_cost
        self.date_messaging_expires=date.today() + timedelta(days=14)
        # change the status of relationship's is_ratings_paid and save the object
        self.save(update_fields=['date_messaging_expires'])
        self.source_person.save(update_fields=['site_credits'])
        return True #must return True or else caller thinks payment failed
 
    @transaction.commit_on_success # rollback entire function if something fails
    def delete(self,*args, **kwargs):  
        print "delete relationships fired"        
        # check to see if there is a reciprocal relationship
        # if the target person had a reciprocal relationship, update that person's (crush's) relationship with the new status
        lineup_members=self.lineupmember_set.all()
        for member in lineup_members:
            member.delete()
        # delete any associated lineup members
        super(CrushRelationship, self).delete(*args,**kwargs)

        # automatically create a platonic relationship
        PlatonicRelationship.objects.create(source_person=self.source_person, target_person=self.target_person)
        
        # if the target was previously inactive, then 

        # delete any messages that this user has sent out to the crush (regardless of state)
        now = datetime.now()
        self.source_person.sent_messages.filter(recipient = self.target_person).update(sender_deleted_at=now)
        self.source_person.received_messages.filter(sender=self.target_person).update(recipient_deleted_at=now)

        return
        
    def notify_target_person(self):

        print "notifying the target person of a new admirer at : " 
        target_person=self.target_person
        target_person_email=target_person.email
        if (not target_person_email):
                return
        try:
            
            if (target_person.bNotify_new_admirer== True):
                subject= "You have a new secret admirer!"
                message="You have a new secret admirer!\nLog in now to find out who it is: " 
                print "attemping to send email to " + str([target_person_email])
                result = requests.post("https://api.mailgun.net/v2/attractedto.mailgun.org/messages",\
                                     auth=("api", settings.MAILGUN_API_KEY),\
                                     data={"from": "AttractedTo.com <notifications@attractedTo.com>",\
                                           "to": target_person_email,\
                                           "subject": subject,\
                                           "text": message})
                print "MailGun Response: " + str(result)
                #send_mail(subject=subject,message=message,from_email=from_email,recipient_list=[target_person_email])
        except Exception as e:
            print "MAIL PROBLEM! " + str(e)
            
    def notify_source_person(self):
       
        print "notifying the source person of a change in target status: " + str(self.target_status)
        target_status=self.target_status
        source_person=self.source_person
        source_person_email=source_person.email
        if (not source_person_email):
                return

        target_person=self.target_person
        target_person_name = target_person.first_name + " " + target_person.last_name
        
        try:
            send_time=None
            subject=""
            if (target_status==2 and source_person.bNotify_crush_signed_up==True): # user signed up
                subject= target_person_name + " signed up!"
                message=target_person_name + " signed up!"
            # don't send crush lineup started notifications any longer
            #elif (target_status==3 and source_person.bNotify_crush_started_lineup==True): # user started line up
            #    subject= target_person_name + " started your secret admirer lineup!"
            #    message=target_person_name + " started your secret admirer lineup!  Expect a response soon."
            elif (target_status > 3 and source_person.bNotify_crush_responded==True): # user responded
                if self.is_results_paid == True: # target person changed their mind
                    subject= target_person_name + " changed their mind."
                    if target_status ==4:
                        message=target_person_name + " changed " + target_person.get_gender_pronoun() + " mind.  They added you as an attraction!"
                    else:
                        message=target_person_name + " changed " + target_person.get_gender_pronoun() + "  mind.  They removed you from their attraction list."
                else:
                    if self.date_target_responded > datetime.now():
                        send_time=self.date_target_responded
                        send_time= send_time.timetuple()
                        send_time=time.mktime(send_time)
                        send_time = utils.formatdate(send_time)
                    subject= target_person_name + " responded to your crush!" + str(send_time)
                    message=target_person_name + " responded to your crush.  Continue to the app and find out what they think of you."
            data_dict={"from": "AttractedTo.com <notifications@attractedTo.com>",\
                           "to": source_person_email,"subject": subject,"text": message}
            if send_time != None:
                data_dict["o:deliverytime"]=str(send_time)        
            print "sending email to " + str([source_person_email]) + " at time: " + str(send_time)
            result= requests.post("https://api.mailgun.net/v2/attractedto.mailgun.org/messages",auth=("api", settings.MAILGUN_API_KEY),data=data_dict)
            print "MailGun Response: " + str(result)
                #send_mail(subject=subject,message=message,from_email=from_email,recipient_list=[source_person_email])
        except Exception as e:
            print "MAIL PROBLEM! " + str(e)
            
    def notify_source_person_bad_invite_email(self,bad_email_address):      
        subject = "Attraction invite - delivery unsuccessful (" + self.target_person.get_name() + ")"
        message = "Your invite email (" + str(bad_email_address) + ") to " + self.target_person.get_name() + " was not able to be delivered.  Please verify your attraction's email address and try again."
        data_dict={"from": "AttractedTo.com <notifications@attractedTo.com>",\
                           "to": self.source_person.email,"subject": subject,"text": message}  
        requests.post("https://api.mailgun.net/v2/attractedto.mailgun.org/messages",auth=("api", settings.MAILGUN_API_KEY),data=data_dict)  
    
    def __unicode__(self):
        return 'Crush: '  + str(self.source_person.first_name) + " " + str(self.source_person.last_name) + " -> " + str(self.target_person.first_name) + " " + str(self.target_person.last_name)
