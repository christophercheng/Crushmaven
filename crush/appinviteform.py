'''
Created on Dec 24, 2012

@author: Chris Work
'''
import re
from django import forms
from django.core.validators import email_re
from django.forms import ValidationError,TextInput

EMAIL_SEPARATOR=re.compile(r'[,; ]+')

class MultiEmailField(forms.Field):
    widget=forms.TextInput(attrs={'placeholder':'Enter one or more email addresses'})
    def to_python(self,value):
        #'normalize data to a list of strings'
        if not value:
            return []
        return EMAIL_SEPARATOR.split(value)
    
    def validate(self,value):
        # check if value consists only of valid emails
        
        # use the parent's handling of required fields, etc.
        super(MultiEmailField,self).validate(value)
        print "----VALIDATION PROCESS: " + str(value) + "---------" 
        for email in value:
            print "processing email: " + str(email)
            if not email_re.match(email):
                raise ValidationError(('%s is not a valid email address') % email)


class AppInviteForm(forms.Form):

    def __init__(self,*args,**kwargs):
        self.friendlist_string=kwargs.pop('friendlist_string',None)
        super(AppInviteForm, self).__init__(*args,**kwargs)
    
    crush_emails = MultiEmailField(required=False)
    mutual_friend_emails = MultiEmailField(required=False)

    def clean(self):
        print "clean called"
        if (self.data['crush_emails']=="") and (self.data['mutual_friend_emails']==""):
            raise forms.ValidationError("Enter at least one valid email address")
        return super(AppInviteForm,self).clean()


        
        
    

        