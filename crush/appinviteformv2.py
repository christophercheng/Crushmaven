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

EMAIL_SEPARATOR=re.compile(r'[,;]+')

class MultiEmailField(forms.Field):
    widget=forms.TextInput(attrs={'placeholder':' enter any email addresses of your crush','maxlength':'100'})
    
    def to_python(self,value):
        #'normalize data to a list of strings'
        if not value:
            return []
        email_list = EMAIL_SEPARATOR.split(value)
        cleaned_email_list = []
        for email in email_list:
                email = email.replace('\u200b','') # replace any strange zero whitespace character that sometimes creeps up in copy/pasted emails
                email = email.strip() #remove whitespace characters before and after
                if email != '':
                    cleaned_email_list.append(email)
        return cleaned_email_list
    
    def validate(self,value):
        # check if value consists only of valid emails
        
        # use the parent's handling of required fields, etc.
        super(MultiEmailField,self).validate(value)
        print "----VALIDATION PROCESS: " + str(value) + "---------" 
        for email in value:
            if email == '':
                raise ValidationError ("Are you missing an email address?")
            if not email_re.match(email):
                raise ValidationError(('%s is not a valid email address') % email)
            try:
                mailgun_result= requests.get("https://api.mailgun.net/v2/address/validate?api_key=" + settings.MAILGUN_PUBLIC_API_KEY + "&address=" + email)
                print str(mailgun_result.text)
                dictionary_result = json.loads(mailgun_result.text)
            except Exception as e:
                raise ValidationError("Please try again.  We're having issues :(")
            if not dictionary_result['is_valid']:
                raise ValidationError(('%s is not a valid email address') % email)


# same as mutliemailfield but doesn't have placeholder text
class MF_MultiEmailFieldNoHelp(MultiEmailField):
    widget=forms.TextInput(attrs={'maxlength':'100'})
# same as mutliemailfield but placeholder text is not crush specific
class MF_MultiEmailFieldHelp(MultiEmailField):
    widget=forms.TextInput(attrs={'placeholder':' enter one or more email addresses','maxlength':'100'})

class TwitterField(forms.Field):
    widget=forms.TextInput(attrs={'placeholder':' enter their twitter username','maxlength':'15'})
    
    def to_python(self,value):
        #'normalize data to a list of strings'
        if len(value) > 0 and value[0]=='@':
            value= value[1:]
        return value
    
    def validate(self,value):
        # check if value consists only of valid emails
        
        # use the parent's handling of required fields, etc.
        if ' ' in value:
            raise ValidationError ("invalid Twitter username (no spaces)")
   

class AppInviteForm2(forms.Form):

    def __init__(self,*args,**kwargs):
        mutual_friend_json=kwargs.pop('mutual_friend_json',None)
        super(AppInviteForm2, self).__init__(*args,**kwargs)
        mutual_friend_count=0
        for i,friend in enumerate(mutual_friend_json):
            if i > 0:
                self.fields['mutual_friend_%s' % i] = MF_MultiEmailFieldNoHelp(required=False,label=friend['name'],help_text=friend['id'])
            else:
                self.fields['mutual_friend_%s' % i] = MF_MultiEmailFieldHelp(required=False,label=friend['name'],help_text=friend['id'])
            mutual_friend_count+=1
        if mutual_friend_count == 0:
            self.fields['mutual_friend_%s' % mutual_friend_count] = MF_MultiEmailFieldHelp(required=False,label='Friends:',help_text='Enter one or more email addresses')
        else:
            self.fields['mutual_friend_%s' % mutual_friend_count] = MF_MultiEmailFieldNoHelp(required=False,label='Other Friends:',help_text='')
    crush_emails = MultiEmailField(required=False,label='crush_field',help_text="HEHEHEH")
    twitter_username=TwitterField(required=False,label='crush_field',help_text="HEHEHE")

    def clean(self):
        print "clean called"
        if len(self._errors) == 0:
            at_least_one_data=False
            for name,value in self.cleaned_data.items():
                if len(value) > 0:
                    at_least_one_data=True
                    break;
            if not at_least_one_data:
                raise forms.ValidationError("Enter at least one valid email address or twitter username")
        
        return super(AppInviteForm2,self).clean()
    
    # return all email addresses in an enumeration (treat output like an array)
    def get_mutual_friend_email_array(self):
        for name,value_array in self.cleaned_data.items():
            if name.startswith('mutual_friend_') and len(value_array) > 0:
                for email_address in value_array:
                    yield email_address

        
        
    

        