'''
Created on Dec 24, 2012

@author: Chris Work
'''
from django.forms import ModelForm,EmailField
from crush.models import FacebookUser


class PreferenceSettingsForm(ModelForm):

    class Meta:
        model = FacebookUser
        fields = ['gender_pref',                  
                  'bNotify_crush_signup_reminder',
                  'bNotify_new_admirer',
                  'email']
        
    email = EmailField()

    
    def __init__(self,*args,**kwargs):
        super(PreferenceSettingsForm,self).__init__(*args,**kwargs)
        self.fields['gender_pref'].label=""
        self.label_suffix=""
        self.fields['email'].label= ""
        self.fields['bNotify_crush_signup_reminder'].label="Invitation Not Sent Reminder"
        self.fields['bNotify_new_admirer'].label=" New Admirer Notification"
        