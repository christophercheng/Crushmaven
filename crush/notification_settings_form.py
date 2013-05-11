'''
Created on Dec 24, 2012

@author: Chris Work
'''
from django.forms import ModelForm,EmailField
from crush.models import FacebookUser


class NotificationSettingsForm(ModelForm):

    class Meta:
        model = FacebookUser
        fields = [ 'bNotify_crush_signed_up',
                  'bNotify_crush_signup_reminder',
                  'bNotify_crush_responded',
                  'bNotify_new_admirer',
                  'bNotify_setup_lineup_completed',
                  'bNotify_setup_recommendee_responded',
                  'email']
    
    email = EmailField()

    def __init__(self,*args,**kwargs):
        super(NotificationSettingsForm,self).__init__(*args,**kwargs)
        self.label_suffix=""
        self.fields['email'].label= ""
        self.fields['bNotify_crush_signed_up'].label=" attraction signed up"
        self.fields['bNotify_crush_signup_reminder'].label=" attraction still not signed up (reminder)"
        self.fields['bNotify_crush_responded'].label=" attraction response received"
        self.fields['bNotify_new_admirer'].label=" new admirer received"
        self.fields['bNotify_setup_lineup_completed'].label=" friend setup - recomendee lineup completed"
        self.fields['bNotify_setup_recommendee_responded'].label=" friend setup - recommendee response received"
    

        