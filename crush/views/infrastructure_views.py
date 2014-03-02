from django.http import HttpResponseRedirect,HttpResponse,HttpResponseForbidden
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from crush.models import CrushRelationship
from crush.models import FacebookUser
from django.conf import settings
from crush.models.miscellaneous_models import InviteEmail
from crush.utils_email import send_mailgun_email, send_facebook_mail_crush_invite
from crush.utils import fb_fetch,graph_api_fetch
import re
from django.db.models import Count
from django.core.cache import cache
# to allow app to run in facebook canvas without csrf error:
from django.views.decorators.csrf import csrf_exempt
import datetime
from django.core.mail import send_mail


import hashlib, hmac
# for mail testing 
# import the logging library
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)

@csrf_exempt
def facebook_notification(request,function_name,first_arg,second_arg,third_arg=""):
    if function_name=="crush_response":
        return crush_response(request,first_arg,second_arg)
    elif function_name=="lineup_expiration":
        return lineup_expiration(request,first_arg,second_arg)
    elif function_name=="missed_invite_tip":
        return missed_invite_tip(request,first_arg,second_arg,third_arg)

@csrf_exempt
def crush_response(request,first_name,last_name):
    return render(request, 'email_template_notify_new_attraction_response.html',{'full_name':first_name + " " + last_name,'short_name':first_name,'first_name':first_name,'facebook_canvas':True})

@csrf_exempt
def lineup_expiration(request,target_person_username,display_id):
    try:
        relationship = CrushRelationship.objects.get(target_person__username = target_person_username,display_id=display_id)
    except:
        return render(request,'email_template_notify_lineup_expiration_warning.html',{'expiration_date':datetime.datetime.now(),'STATIC_URL':settings.STATIC_URL,'facebook_canvas':True})
    return render(request,'email_template_notify_lineup_expiration_warning.html',{'expiration_date':relationship.date_lineup_expires,'STATIC_URL':settings.STATIC_URL,'facebook_canvas':True})

@csrf_exempt
def missed_invite_tip(request,source_person_username,source_person_first_name,email_type):
    html_template = "email_template_missed_invite_tip_other.html"
    if 'hotmail' == email_type:
        html_template = "email_template_missed_invite_tip_hotmail.html"
    elif 'yahoo' == email_type:
        html_template = "email_template_missed_invite_tip_yahoo.html"   
    return render(request,html_template,{'recipient_fb_username':source_person_username,'STATIC_URL':settings.STATIC_URL,'source_first_name':source_person_first_name})
 

@login_required
def inactive_crush_list(request):
    if request.user.username != 'admin':
        return HttpResponse("nu uhhhh")
    #call_command('daily_maintenance')
    #lineup_expiration_warning()
    inactive_crushes = FacebookUser.objects.filter(is_active=False).annotate(num_admirers=Count('admirer_set')).filter(num_admirers__gt=0)
    response = 'INACTIVE CRUSH LIST: <BR><BR>'
    for crush in inactive_crushes:
        response += str(crush.username) + "<BR>"
    return HttpResponse(response)

@login_required
def clear_cached_inactive_crush_list(request):
    if request.user.username != 'admin':
        return HttpResponse("nu uhhhh")
    cache.delete(settings.INACTIVE_USER_CACHE_KEY)
    return HttpResponse("Cache Cleared")  

@login_required
def cached_inactive_crush_list(request):
    
    if request.user.username != 'admin':
        return HttpResponse("nu uhhhh")
    #call_command('daily_maintenance')
    #lineup_expiration_warning()
    inactive_crushes = cache.get(settings.INACTIVE_USER_CACHE_KEY)   
    response = 'CACHED INACTIVE CRUSH LIST: <BR><BR>'
    if inactive_crushes==None:
        response += 'EMPTY'
        return HttpResponse(response)
    for crush in inactive_crushes:
        response += str(crush) + "<BR>"
    return HttpResponse(response)
    
@login_required
def new_testing(request):
    if request.user.username != '100007405598756':
        return HttpResponse("nu uhhhh")
    #send_mail('Your friend added you as a crush 2', "Visit www.crushmaven.com to learn more.\r\n\r\nCrushMaven is the new matchmaking service that discovers anonymously if the person you're attracted to feels the same - or why they don't", 'CrushMaven <notifications@crushmaven.com>',
    #['chris.h.cheng@facebook.com'])
    response=''
    inactive_crushes = FacebookUser.objects.filter(is_active=False).annotate(num_admirers=Count('admirer_set')).filter(num_admirers__gt=0)
    for inactive_crush in inactive_crushes:
        logger.debug("Trying to get fb username for uid: " + inactive_crush.username + " " + inactive_crush.first_name + " " + inactive_crush.last_name)
        query_string=str(inactive_crush.username) + "?fields=username"
        try:
            data = graph_api_fetch(request.user.access_token,query_string,False)
            try:
                if 'username' in data:
                    fb_username=data['username']
                    fb_username += "@facebook.com"
                    response += fb_username + "<BR>"
            except Exception as e:
                continue
        except:
            continue
    return HttpResponse(response)
    

@login_required
def testing(request):
    if request.user.username != '651900292':
        return HttpResponse("nu uhhhh")
    try:
        fetch_response = fb_fetch("1050",0)
    except Exception as e:
        return HttpResponse(str(e))
    extracted_id_list =  re.findall( 'user.php\?id=(.*?)&',fetch_response,re.MULTILINE )
        # remove duplicates in extracted_list
    extracted_id_list = list(set(extracted_id_list))
    result = "Number of results: " + str(len(extracted_id_list))
    
   
    return HttpResponse(result)
@login_required
def testing2(request):
    if request.user.username != '651900292':
        return HttpResponse("nu uhhhh")
    #if request.user.username != '651900292':
    #    return HttpResponse("nu uhhhh")
    magic_cookie=str(cache.get(settings.FB_FETCH_COOKIE,''))
    return HttpResponse("cookie in cache: " + magic_cookie)
@login_required
def testing_prep(request):
    if request.user.username != '651900292':
       return HttpResponse("nu uhhhh")
    cache.set(settings.FB_FETCH_COOKIE,"137%3AyoNXnPd5mpliVA%3A2%3A1389009777%3A14734")
    return HttpResponse("done")

# -- Home Page --
# handles both member and guest home page

def sitemap(request):
    return HttpResponseRedirect('/static/sitemap.xml',mimetype='application/xml')
@csrf_exempt # for canvas app center facebook 
def home(request,source=''):
    get_parameter_string=""
    if request.GET.__contains__('signin'): # in the facebook authentication process, we append signin as GET parameter so we know when we just logged in
        get_parameter_string += "?signin=true" #this is used to check if user is on mobile when signing in
    if source == 'verified_email':
        if get_parameter_string == '':
            get_parameter_string += '?verified_email=true'
        else:
            get_parameter_string += '&verified_email=true'
    if request.user.is_authenticated():

        if CrushRelationship.objects.visible_responded_crushes(request.user).count() > 0:
            return HttpResponseRedirect('/your_crushes/' + get_parameter_string) 
        elif CrushRelationship.objects.progressing_admirers(request.user).count()>0:
            return HttpResponseRedirect('/admirers/' + get_parameter_string)
        else:
            return HttpResponseRedirect('/your_crushes/' + get_parameter_string)
    else:
        if request.GET.__contains__('fb_app_center_login'):
            return HttpResponseRedirect('/facebook/login')
        else:
            return render(request,'guest_home.html', {'facebook_app_id':settings.FACEBOOK_APP_ID})

@login_required
def verify_email(request,username):
    me = request.user
    if me.is_email_verified:
        return home(request)
    if me.username == username:
        me.is_email_verified=True
    me.save(update_fields=['is_email_verified'])
    return home(request,'verified_email')

@login_required
def ajax_resend_verification_email(request):
    me = request.user
    if me.is_email_verified:
        return HttpResponse('')
    me.send_verification_email()
    return HttpResponse('')
    
        
#same as home but allows me to do special tracking
def google_home(request):
    get_parameter_string=""
    if request.GET.__contains__('signin'): # in the facebook authentication process, we append signin as GET parameter so we know when we just logged in
        get_parameter_string = "?signin=true" #this is used to check if user is on mobile when signing in
    if request.user.is_authenticated():
    
        if CrushRelationship.objects.visible_responded_crushes(request.user).count() > 0:
            return HttpResponseRedirect('/your_crushes/' + get_parameter_string) 
        elif CrushRelationship.objects.progressing_admirers(request.user).count()>0:
            return HttpResponseRedirect('/admirers/' + get_parameter_string)
        else:
            return HttpResponseRedirect('/your_crushes/' + get_parameter_string)
    else:
        return render(request,'guest_home.html', { 'ad_visit':True,'google_ad_visit':True,'facebook_app_id':settings.FACEBOOK_APP_ID})

#same as home but allows me to do special tracking
def bing_home(request):
    get_parameter_string=""
    if request.GET.__contains__('signin'): # in the facebook authentication process, we append signin as GET parameter so we know when we just logged in
        get_parameter_string = "?signin=true" #this is used to check if user is on mobile when signing in
    if request.user.is_authenticated():
    
        if CrushRelationship.objects.visible_responded_crushes(request.user).count() > 0:
            return HttpResponseRedirect('/your_crushes/' + get_parameter_string) 
        elif CrushRelationship.objects.progressing_admirers(request.user).count()>0:
            return HttpResponseRedirect('/admirers/' + get_parameter_string)
        else:
            return HttpResponseRedirect('/your_crushes/' + get_parameter_string)
    else:
        return render(request,'guest_home.html', {'ad_visit':True,'bing_ad_visit':True,'facebook_app_id':settings.FACEBOOK_APP_ID})
    
    #same as home but allows me to do special tracking
def facebook_home(request):
    if request.user.is_authenticated():
    
            if CrushRelationship.objects.visible_responded_crushes(request.user).count() > 0:
                return HttpResponseRedirect('/your_crushes/') 
            elif CrushRelationship.objects.progressing_admirers(request.user).count()>0:
                return HttpResponseRedirect('/admirers/')
            else:
                return HttpResponseRedirect('/your_crushes/')
    else:
        return render(request,'guest_home.html', {'ad_visit':True,'facebook_ad_visit':True,'facebook_app_id':settings.FACEBOOK_APP_ID})
        
@login_required
def ajax_submit_feedback(request):
    message=request.POST['message']
    from_email= request.user.email
    if from_email == "":
        from_email = request.user.username + "_" + "noemail" + "@crushmaven.com"
    send_mailgun_email(from_email, 'feedback@crushmaven.com', 'CrushMaven User Feedback',message,message)
    return HttpResponse("")


# -- Logout --
@login_required
def logout_view(request):
    if request.user.username in ['100006341528806','1057460663','100004192844461','651900292','100003843122126','100007405598756','admin']:
        logout_path="/home?no_track"
    else:
        logout_path="/home/"
    logout(request)
    return HttpResponseRedirect(logout_path)

def under_construction(request):
    return render(request,'under_construction.html')

def verify_mailgun_post(token, timestamp, signature):
    return signature == hmac.new(
                             key=settings.MAILGUN_API_KEY,
                             msg='{}{}'.format(timestamp, token),
                             digestmod=hashlib.sha256).hexdigest()

# -- Logout --
@csrf_exempt
def failed_email_send(request):
    post_data=request.POST
    logger.debug("Bad email data:" + str(post_data))
    if not 'token' in post_data or not verify_mailgun_post(post_data['token'],post_data['timestamp'],post_data['signature']):
        return HttpResponse("")
    try:
        bad_email_address=post_data['recipient']
        logger.debug( "bad email: " + str(bad_email_address) + " from " + str(request.user) )
        bad_email_results = InviteEmail.objects.filter(email=str(bad_email_address))
        for bad_email in bad_email_results:
            relationship=bad_email.relationship
            bad_email.delete()
            relationship.notify_source_person_bad_invite_email(bad_email_address)
            # check the crush relationship - if no other invite emails sent, then change it's status back to 0
            if relationship.inviteemail_set.count() == 0 and relationship.target_status == 1:
                    relationship.target_status=0
                    relationship.date_invite_last_sent=None
                    relationship.save(update_fields=['target_status','date_invite_last_sent'])
    except Exception as e:
        print e
        pass
    return HttpResponse("Got it")

# facebook javascript api requires a channel.html file for cross-site authentication
def facebook_channel_file(request):
    return render(request,'channel.html')


# fake page used to create custom content for fb send dialog (from friends-with-admirer sidebar)
def admirer_for(request,first_name,last_initial):
    return render(request, 'guest_home.html',
                              {
                               'change_title': first_name + " " + last_initial + '. has an admirer!', 
                               'change_description': "CrushMaven is a new matchmaking service that finds out if someone you like feels the same - anonymously and without any social awkwardness. More than just friends?  Find out at crushmaven.com.",
                               'change_url':"http://" + request.META['HTTP_HOST'] + "/admirer_for/" + first_name + "/" + last_initial + "/",
                               'facebook_app_id':settings.FACEBOOK_APP_ID
                               })    
    return HttpResponse("")

# fake page used to create custom content for fb send dialog (from friends-with-admirer sidebar)
def feedback_form(request):
    if request.user.bCompletedSurvey:
        return HttpResponseRedirect('/your_crushes/') # only allow form to be filled out once
    questions=[
               {'Do you think this site is useful?': [{'Yes': None},{'No':'Why not?'}]},
               {'Would you recommend this site to a friend?': [{'Yes': None},{'No':'Why not?'}]},
               {'Do you understand how this site works?': [{'Yes': None},{'Kind of':'What is not clear to you?'},{'No':'What is not clear to you?'}]},
               {'Do you trust that your identity as an admirer will be kept private if you use this site?': [{'Yes': None},{'No':'Why not?'}]},
              { 'Would you use this site for someone you really liked?': [{'Yes': None},{'No':'Why not?'}]},
               {'How would you describe your relationship with your crush(s)?': [{'Close friends': None},{'We are acquaintances':None},{'They know of me': None},{'They don\'t know me at all': None},{'Other': 'Explain'}]},
               {'Would you pay $1 to see how your crush responded?': [{'Yes': None},{'No':'Why not?'}]},
               {'Would you pay $5 to see how your crush responded?': [{'Yes': None},{'No':'Why not?'}]},
               {'Do you understand how credits work?': [{'Yes': None},{'No':None}]},
               {'Would you use your PayPal account to purchase credits?': [{'Yes': None},{'I don\'t have a PayPal account':None},{'No':'Why not?'}]},
               {'Would you use your credit card to purchase credits?': [{'Yes': None},{'I don\'t have a credit card':None},{'No':'Why not?'}]},
               {'Did you send your crush an invitation using our invite dialog?': [{'Yes': None},{'No':'Why not?'}]}, 
               {'Do you understand why we ask you for your crush\'s contact information to send invites?': [{'Yes': None},{'No':None}]},  
               {'How difficult was our invite dialog to use?': [{'Not difficult at all': None},{'A bit difficult':'Explain'},{'Very difficult':'Explain'}]},              
               {'Do you know the email address of your crushes?': [{'Yes': None},{'No':None}]},
               {'Do you know the twitter username of your crushes?': [{'Yes': None},{'No':None}]},
               {'Would you pay $1 to send an anonymous invite through facebook (which increases your chances of receiving a response)?': [{'Yes': None},{'No':'Why not?'}]},
                {'Did you know we can send an invitation to mutual friends of your crush and ask them to forward it to your crush?': [{'Yes': None},{'No':None}]},
                {'Would you send invitations through mutual friends of your crush?': [{'Yes': None},{'No':'Why not?'}]},
                {'How can we improve our site for you?': [{'It\'s perfect - no suggestions':None},{'My suggestions':''}]},
                ]

    return render(request, 'feedback_form.html',{'questions':questions})    

def post_feedback_form(request):
    
    if request.user.bCompletedSurvey != True:
        request.user.bCompletedSurvey=True;
        current_credits=request.user.site_credits
        current_credits += 1
        request.user.site_credits = current_credits
        request.user.save(update_fields=['bCompletedSurvey','site_credits'])
        ajax_submit_feedback(request)
        
        return HttpResponse("Good")
    else:
        return HttpResponseForbidden("Already Submitted Form")
