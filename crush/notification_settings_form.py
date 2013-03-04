'''
Created on Dec 24, 2012

@author: Chris Work
'''
from django.forms import ModelForm,EmailField
from crush.models import FacebookUser


class NotificationSettingsForm(ModelForm):

    class Meta:
        model = FacebookUser
        fields = ['email',  'bNotify_crush_signed_up',
                  'bNotify_crush_signup_reminder',
                  'bNotify_crush_started_lineup',
                  'bNotify_crush_responded',
                  'bNotify_new_admirer']
    
    email = EmailField()
    

        