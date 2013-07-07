from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from fbdater.crush.notification_settings_form import NotificationSettingsForm
from fbdater.crush.profile_settings_form import ProfileSettingsForm

# -- Profile Settings Page --
@login_required
def settings_profile(request):
    print "Settings Profile Form!"
    # crush_name should be first name last name
    if request.method == 'POST': # if the form has been submitted...
        print "METHOD IS POST"
        data=request.POST
        if 'cancel' in data:
            return redirect('/settings_profile/')
        else:
            form = ProfileSettingsForm(request.POST)
            if form.is_valid():
                me=request.user
                for element in data:
                    print "element: " + str(element) + " value: " + str(data[element])
                updated_fields=[]
                if 'gender' in data: 
                    me.gender=data['gender']
                    updated_fields.append('gender')                    
                if 'gender_pref' in data: 
                    me.gender_pref=data['gender_pref']
                    updated_fields.append('gender_pref')
                me.is_single=data.get('is_single',False)
                updated_fields.append('is_single')
                if 'birthday_year' in data and data['birthday_year']:
                    me.birthday_year=data['birthday_year']
                    updated_fields.append('birthday_year')
                if 'age_pref_min' in data and data['age_pref_min']: 
                    me.age_pref_min=data['age_pref_min']
                    updated_fields.append('age_pref_min')
                if 'age_pref_max' in data and data['age_pref_max']:
                    me.age_pref_max=data['age_pref_max']
                    updated_fields.append('age_pref_max')
                me.save(update_fields=updated_fields)
                #return redirect('/settings_profile/')
                return render(request,'settings_profile.html',
                              { 'form': form,'updated':True})
    else:
        print "instantiating profile form"
        form=ProfileSettingsForm(instance=request.user)
    return render(request,'settings_profile.html',
                              { 'form': form})
    
# -- Notification settings --
@login_required
def settings_notifications(request):
    print "Settings Notification Form!"
    # crush_name should be first name last name
    if request.method == 'POST': # if the form has been submitted...
        print "METHOD IS POST"
        data=request.POST
        if 'cancel' in data:
            return redirect('/settings_notifications/')
        else:
            me=request.user
            form = NotificationSettingsForm(request.POST)
            if form.is_valid():
                for element in request.POST:
                    print str(element) + " value: " + str(request.POST[element])
                me.email=data['email']

                #me.bNotify_crush_signed_up=data.get('bNotify_crush_signed_up',False)
                me.bNotify_crush_signup_reminder = data.get('bNotify_crush_signup_reminder',False)
                #me.bNotify_crush_started_lineup=data.get('bNotify_crush_started_lineup',False)
                me.bNotify_crush_responded=data.get('bNotify_crush_responded',False)  
                me.bNotify_new_admirer=data.get('bNotify_new_admirer',False)
                me.bNotify_setup_response_received=data.get('bNotify_setup_response_received',False)
                #me.save(update_fields=['email','bNotify_crush_signed_up','bNotify_crush_signup_reminder','bNotify_crush_responded','bNotify_new_admirer','bNotify_setup_response_received'])                            
                me.save(update_fields=['email','bNotify_crush_signup_reminder','bNotify_crush_responded','bNotify_new_admirer','bNotify_setup_response_received'])                            
               
                return render(request,'settings_notifications.html',
                              { 'form': form,'updated':True})
    else:
        print "instantiating notifications form"
        form=NotificationSettingsForm(instance=request.user, initial={'email':request.user.email})
    return render(request,'settings_notifications.html',
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
