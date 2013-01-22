from django.db import models
from django.db.models import F

class NotificationSettings(models.Model):
    
    class Meta:
        # this allows the models to be broken into separate model files
        app_label = 'crush' 
        
    bNotify_crush_signed_up = models.BooleanField(default=True)
    bNotify_crush_signup_reminder = models.BooleanField(default=True)
    bNotify_crush_started_lineup = models.BooleanField(default=False) # off by default cause reciprocal lineup crushes don't instantiate a lineup
    bNotify_crush_responded = models.BooleanField(default=True)
    bNotify_new_admirer = models.BooleanField(default=True)

class EmailRecipient(models.Model):

    class Meta:
        # this allows the models to be broken into separate model files
        app_label = 'crush' 
        
    crush_relationship = models.ForeignKey('CrushRelationship')
    recipient_address=models.CharField(max_length=200) # is this long enough?
    date_sent=models.DateTimeField(auto_now_add=True)
    is_email_crush=models.BooleanField(default=True) # if false, then the email was sent to a mutual friend

# details about each crush's secret admirer lineup (SAL)
class LineupMembership(models.Model):
    
    class Meta:
        # this allows the models to be broken into separate model files
        app_label = 'crush'
    # each lineup has many lineup members (10 by default) and each lineup member has only one lineup it belongs to (similar to blog entry)
    relationship = models.ForeignKey('CrushRelationship')
    lineup_member=models.ForeignKey('FacebookUser')
    position = models.IntegerField() # example x.y where x is id of lineup and y is position in lineup (0 through 9)

    DECISION_CHOICES = ( # platonic levels represent crush's rating of member's attractiveness
                           (0,'Crush'),
                           (1,'Platonic 1'),
                           (2,'Platonic 2'),
                           (3,'Platonic 3'),
                           (4,'Platonic 4'),
                           (5,'Platonic 5'),
                           )
    decision = models.IntegerField(null=True, choices=DECISION_CHOICES, default=None)
    comment = models.CharField(null=True,default=None,max_length=200)

class Purchase(models.Model):

    class Meta:
        # this allows the models to be broken into separate model files
        app_label = 'crush' 
        
    credit_total = models.IntegerField(default=0) # e.g. 100
    price = models.DecimalField( decimal_places=2, max_digits=7 )
    purchaser = models.ForeignKey('FacebookUser')
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
