'''
Created on Dec 24, 2012

@author: Chris Work
'''
import re
from django import forms
from django.core.validators import email_re
from django.forms import ValidationError,TextInput

EMAIL_SEPARATOR=re.compile(r'[,;]+')

class MultiEmailField(forms.Field):
    widget=forms.TextInput(attrs={'placeholder':'Enter one or more email addresses'})
    
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

# same as mutliemailfield but doesn't have placeholder text
class MF_MultiEmailField(MultiEmailField):
    widget=forms.TextInput()
   

class AppInviteForm2(forms.Form):

    def __init__(self,*args,**kwargs):
        mutual_friend_json=kwargs.pop('mutual_friend_json',None)
        print mutual_friend_json
        print "TYPE: " + str(type(mutual_friend_json))
        print len(mutual_friend_json)
        super(AppInviteForm2, self).__init__(*args,**kwargs)
        mutual_friend_count=0
        for i,friend in enumerate(mutual_friend_json):
            if i > 0:
                self.fields['mutual_friend_%s' % i] = MF_MultiEmailField(required=False,label=friend['name'],help_text=friend['id'])
            else:
                self.fields['mutual_friend_%s' % i] = MultiEmailField(required=False,label=friend['name'],help_text=friend['id'])
            mutual_friend_count+=1
        if mutual_friend_count == 0:
            self.fields['mutual_friend_%s' % mutual_friend_count] = MultiEmailField(required=False,label='Friends:',help_text='Enter one or more email addresses')
        else:
            self.fields['mutual_friend_%s' % mutual_friend_count] = MF_MultiEmailField(required=False,label='Other Friends:',help_text='')
    crush_emails = MultiEmailField(required=False,label='crush_field',help_text="HEHEHEH")

    def clean(self):
        print "clean called"
        if len(self._errors) == 0:
            at_least_one_data=False
            for name,value in self.cleaned_data.items():
                if len(value) > 0:
                    at_least_one_data=True
                    break;
            if not at_least_one_data:
                raise forms.ValidationError("Enter at least one valid email address")
        
        return super(AppInviteForm2,self).clean()
    
    # return all email addresses in an enumeration (treat output like an array)
    def get_mutual_friend_email_array(self):
        for name,value_array in self.cleaned_data.items():
            if name.startswith('mutual_friend_') and len(value_array) > 0:
                for email_address in value_array:
                    yield email_address

        
        
    

        