'''
Created on Dec 24, 2012

@author: Chris Work
'''
import re
from django import forms
from django.core.validators import email_re
from django.forms import ValidationError
import requests
from django.conf import settings
import json
from django.utils.safestring import mark_safe
import logging
logger = logging.getLogger(__name__)# Get an instance of a logger
EMAIL_SEPARATOR=re.compile(r'[,;]+')

class MultiEmailField(forms.Field):
    widget=forms.TextInput(attrs={'maxlength':'100'})
    
    def to_python(self,value):
        #'normalize data to a list of strings'
        #self.label = Brad Davis
        # self.help_text = facebook username
        if not value:
            return {'cleaned_email_list':[]}
        email_list = EMAIL_SEPARATOR.split(value)
        cleaned_email_list = []
        for email in email_list:
                email = email.replace('\u200b','') # replace any strange zero whitespace character that sometimes creeps up in copy/pasted emails
                email = email.strip() #remove whitespace characters before and after
                if email != '':
                    cleaned_email_list.append(email)
        cleaned_email_object = {'recipient_first_name':self.label,'recipient_fb_username': self.help_text, 'cleaned_email_list':cleaned_email_list}

        return cleaned_email_object
    
    def validate(self,value):
        # check if value consists only of valid emails
        
        # use the parent's handling of required fields, etc.
        super(MultiEmailField,self).validate(value)
        for email in value['cleaned_email_list']:

            if email == '':
                raise ValidationError ("Are you missing an email address?")
            if not email_re.match(email):
                logger.error("unable to validate email through regex" + str(email))
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


# same as mutliemailfield but doesn't have placeholder text
class MF_MultiEmailFieldNoHelp(MultiEmailField):
    widget=forms.TextInput(attrs={'maxlength':'100'})
# same as mutliemailfield but placeholder text is not crush specific
class MF_MultiEmailFieldHelp(MultiEmailField):
    widget=forms.TextInput(attrs={'placeholder':'enter any email addresses','maxlength':'100'})
# same as mutliemailfield but placeholder text is not crush specific

# any friends
class AF_MultiEmailField(MultiEmailField):
    widget=forms.TextInput(attrs={'placeholder':'emails','maxlength':'100'})
# same as mutliemailfield but placeholder text is not crush specific

class TwitterField(forms.Field):
    widget=forms.TextInput(attrs={'placeholder':'username','maxlength':'15'})
    
    def to_python(self,value):
        #'normalize data to a list of strings'
        if len(value) > 0 and value[0]=='@':
            value= value[1:]
        
        return {'cleaned_email_list':value}
    
    def validate(self,value):
        # check if value consists only of valid emails
        
        # use the parent's handling of required fields, etc.
        if ' ' in value['cleaned_email_list']:
            raise ValidationError ("invalid Twitter username (can't contain spaces)")

class PhoneField(forms.Field):
    widget=forms.TextInput(attrs={'placeholder':'enter only numbers','maxlength':'20'})
    
    def to_python(self,value):
        
        return {'cleaned_email_list':value}
    
    def validate(self,value):
        non_decimal = re.compile(r'[^\d]+')
        original_value=value['cleaned_email_list']
        filtered_value = non_decimal.sub('', original_value)
        if filtered_value!=original_value:
            raise ValidationError ("Enter only numbers (no characters, spaces, punctuation)")
        if len(filtered_value) < 9:
            raise ValidationError ("Enter a complete phone number")


    
class AppInviteForm2(forms.Form):

    def __init__(self,*args,**kwargs):
        mutual_friend_json=kwargs.pop('mutual_friend_json',None)
        self.source_person_email = kwargs.pop('source_person_email',None)
        self.source_person_username=kwargs.pop('source_person_username',None)
        super(AppInviteForm2, self).__init__(*args,**kwargs)
        mutual_friend_count=0
        for i,friend in enumerate(mutual_friend_json):
            if i > 0:
                self.fields['mutual_friend_%s' % i] = MF_MultiEmailFieldNoHelp(required=False,label=friend['name'],help_text=friend['id'])
            else:
                self.fields['mutual_friend_%s' % i] = MF_MultiEmailFieldHelp(required=False,label=friend['name'],help_text=friend['id'])
            mutual_friend_count+=1

        #if mutual_friend_count == 0:
        #    self.fields['mutual_friend_%s' % mutual_friend_count] = MF_MultiEmailFieldHelp(required=False,label='Friends:',help_text='Enter one or more email addresses')
        #else:
        #    self.fields['mutual_friend_%s' % mutual_friend_count] = MF_MultiEmailFieldNoHelp(required=False,label='Other Friends:',help_text='')
    crush_emails = MultiEmailField(required=False,label='crush_field',help_text="HEHEHEH")
    twitter_username=TwitterField(required=False,label='crush_field',help_text="HEHEHE")
    phone=PhoneField(required=False,label='crush_field',help_text="HEHEHE")
    mf_generic_emails = AF_MultiEmailField(required=False,label='crush_field',help_text="HEHEHEH")
    source_person_email=''
    source_person_site_credits=''
    source_person_username=''

    def clean(self):
        if len(self._errors) == 0:
            at_least_one_data=False
            
            for name,value in self.cleaned_data.items():
                if type( value ) == dict:
                    if len(value['cleaned_email_list']) > 0:
                        at_least_one_data=True
                        break;
                else:
                    if value == True:
                        at_least_one_data=True;
                        break;

            if not at_least_one_data:
                logger.debug("Invite Error: User tried to submit invite form without any contact information")
                raise forms.ValidationError("Provide at least one invite option")
            # check that user has entered his or her email in the crush email field
            crush_emails = self.cleaned_data['crush_emails']['cleaned_email_list']
            if self.source_person_email in crush_emails:
                logger.debug("Invite Error: User tried to submit their own email as crush email invite")
                raise forms.ValidationError("Please enter your crush's email - not your own")
        
        return super(AppInviteForm2,self).clean()
    
    # return all email addresses in an enumeration (treat output like an array)
    def get_mutual_friend_email_array(self):
        result_list=[]
        for name,value in self.cleaned_data.items():
            if name.startswith('mutual_friend_') and len(value['cleaned_email_list']) > 0:
                result_list.append(value)
        return result_list
                #for email_address in value_array['cleaned_email_list']:
                #    yield {'mf_email':email_address,'mf_recipient_first_name':

        
        
    

        