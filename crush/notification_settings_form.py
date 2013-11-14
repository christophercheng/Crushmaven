'''
Created on Dec 24, 2012

@author: Chris Work
'''
from django.forms import ModelForm,EmailField
from crush.models import FacebookUser


class NotificationSettingsForm(ModelForm):

    class Meta:
        model = FacebookUser
        fields = [ 
                  #'bNotify_crush_signed_up',
                  'bNotify_crush_signup_reminder',
                  'bNotify_crush_responded',
                  'bNotify_new_admirer',
                  'email']
    
    email = EmailField()

    def __init__(self,*args,**kwargs):
        super(NotificationSettingsForm,self).__init__(*args,**kwargs)
        self.label_suffix=""
        self.fields['email'].label= ""
        #self.fields['bNotify_crush_signed_up'].label=" attraction signed up"
        self.fields['bNotify_crush_signup_reminder'].label="You still have not sent out an invitation."
        self.fields['bNotify_crush_responded'].label=" One of your crushes has responded."
        self.fields['bNotify_new_admirer'].label=" You have a new admirer."
        #self.fields['bNotify_setup_response_received'].label=" One of your friends responded to your setup."
    

        