from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from crush.notification_settings_form import NotificationSettingsForm
from crush.preference_settings_form import PreferenceSettingsForm
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)
# -- Profile Settings Page --
@login_required
def settings_preferences(request):
    # crush_name should be first name last name
    if request.method == 'POST': # if the form has been submitted...
        data=request.POST
        if 'cancel' in data:
            return redirect('/settings_preferences/')
        else:
            form = PreferenceSettingsForm(request.POST)
            if form.is_valid():
                me=request.user
                for element in data:
                    print "element: " + str(element) + " value: " + str(data[element])
                updated_fields=[]                  
                if 'gender_pref' in data: 
                    me.gender_pref=data['gender_pref']
                    updated_fields.append('gender_pref')
                me.save(update_fields=updated_fields)
                return render(request,'settings_preferences.html',
                              { 'form': form,'updated':True})
    else:
        form=PreferenceSettingsForm(instance=request.user)
    return render(request,'settings_preferences.html',
                              { 'form': form})
    

# -- Credit Settings Page --
@login_required
def settings_credits(request):

    if 'amount' in request.POST:
        new_credits = int(request.POST['amount'])
        if new_credits==0:
            request.user.site_credits = 0
            request.user.save(update_fields=['site_credits'])
                          
    # obtain total credits
    credit_available = request.user.site_credits
    
    success_path = '/settings_credits'
    cancel_url = 'http://' + request.get_host() + success_path
    
    paypal_success_url = settings.PAYPAL_RETURN_URL + "/?success_path=" + success_path
    paypal_notify_url = settings.PAYPAL_NOTIFY_URL + request.user.username + "/"
    
    return render(request,'settings_credits.html',
                      {'credit_available':credit_available,
                       'paypal_url': settings.PAYPAL_URL, 
                       'paypal_email': settings.PAYPAL_EMAIL, 
                       'paypal_success_url': paypal_success_url,
                       'paypal_cancel_url': cancel_url,
                       'paypal_notify_url':paypal_notify_url})
