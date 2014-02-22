'''
Created on Dec 24, 2012

@author: Chris Work
'''
from django.forms import ModelForm,EmailField
from crush.models import FacebookUser
from django import forms
from django.core.validators import email_re
from django.forms import ValidationError
import requests
from django.conf import settings
import json
import logging
logger = logging.getLogger(__name__)# Get an instance of a logger
import re
EMAIL_SEPARATOR=re.compile(r'[,;]+')

class CMEmailField(forms.Field):
    widget=forms.TextInput(attrs={'maxlength':'100'})

    def to_python(self,email):

        email = email.replace('\u200b','') # replace any strange zero whitespace character that sometimes creeps up in copy/pasted emails
        email = email.strip() #remove whitespace characters before and after
        return email    
    def validate(self,email):
        # check if value consists only of valid emails
        
        # use the parent's handling of required fields, etc.
        super(CMEmailField,self).validate(email)

        if email == '':
            raise ValidationError ("Enter an email address")
        if 'facebook.com' in email:
            raise ValidationError("We cannot use facebook.com emails")
        if not email_re.match(email):
            raise ValidationError(('%s is not a valid email address') % email)
        try:
            mailgun_result= requests.get("https://api.mailgun.net/v2/address/validate?api_key=" + settings.MAILGUN_PUBLIC_API_KEY + "&address=" + email)
            dictionary_result = json.loads(mailgun_result.text)
        except Exception as e:
            logger.error("unable to validate email through mailgun " + str(email) + " exception: " + str(e))
            raise ValidationError("Please try again.  We're having issues :(")
        if not dictionary_result['is_valid']:
            logger.debug("Invite Error: User tried to submit invite form with email not validated by Mailgun: " + str(email))
            raise ValidationError(('%s is not a valid email address') % email)


class PreferenceSettingsForm(ModelForm):

    class Meta:
        model = FacebookUser
        fields = ['gender_pref',                  
                  'bNotify_crush_signup_reminder',
                  'bNotify_new_admirer',
                  'bNotify_lineup_expiration_warning',
                  'email']
        
    email = CMEmailField(required=True)

    
    def __init__(self,*args,**kwargs):
        super(PreferenceSettingsForm,self).__init__(*args,**kwargs)
        self.fields['gender_pref'].label=""
        self.label_suffix=""
        self.fields['email'].label= ""
        self.fields['bNotify_crush_signup_reminder'].label="Crush Invite Reminder"
        self.fields['bNotify_new_admirer'].label="New Admirer Notification"
        self.fields['bNotify_lineup_expiration_warning'].label="Lineup Expiration Warning"
        