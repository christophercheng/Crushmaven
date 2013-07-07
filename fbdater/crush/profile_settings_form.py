'''
Created on Dec 24, 2012

@author: Chris Work
'''
from django.forms import ModelForm,EmailField
from django.forms.fields import DateField
from fbdater.crush.models import FacebookUser
from django.forms.extras.widgets import SelectDateWidget
from django import forms


class ProfileSettingsForm(ModelForm):

    class Meta:
        model = FacebookUser
        fields = ['gender','gender_pref','is_single','birthday_year','age_pref_min','age_pref_max']

    #birthday_year=forms.IntegerField(required=False)
    #age_pref_min=forms.IntegerField(required=False)
    #age_pref_max=forms.IntegerField(required=False)
    def clean(self):
        print "clean called"
        data = super(ProfileSettingsForm,self).clean()
        if (data['age_pref_min']!="") and (data['age_pref_max']!=""):
            if data['age_pref_min']>data['age_pref_max']:
                self._errors['age_pref_min'] = [("Minimum age preference must be less than or equal to maximum age preference.")]
#                raise forms.ValidationError(non_field_errors)
        return data
    
    def __init__(self,*args,**kwargs):
        super(ProfileSettingsForm,self).__init__(*args,**kwargs)
        self.fields['gender_pref'].label=" Gender Preference"
        self.fields['is_single'].label=" Are You Single"
        self.fields['birthday_year'].label=" Birthday Year"
        self.fields['age_pref_min'].label=" Age Preference Minimum"
        self.fields['age_pref_min'].label=" Age Preference Maximum"

        