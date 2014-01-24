from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from crush.models import CrushRelationship,FacebookUser
from django.conf import settings
from crush.models.miscellaneous_models import InviteEmail
from crush.utils_email import send_mailgun_email
from crush.utils import fb_fetch
import re
from django.core.cache import cache


@login_required
def crushlist(request):
    if request.user.username != '651900292':
        return HttpResponse("nu uhhhh")
    response = "<h2>List of Inactive Users Who Haven't Been Twitter Invited:</h1><BR><BR>"
    relevant_user_list = FacebookUser.objects.filter(is_active=False, date_twitter_invite_last_sent=None)
    for user in relevant_user_list:
        response += "<a href='www.facebook.com/" + user.username + "'>" + user.get_name() + "</a><BR>"
    return HttpResponse(response)
    

@login_required
def testing(request):
    if request.user.username != '651900292':
        return HttpResponse("nu uhhhh")
    fetch_response = fb_fetch("1050",0)
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
        
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)
# end imports for testing

#from django.contrib.auth.models import Use
# to allow app to run in facebook canvas without csrf error:
from django.views.decorators.csrf import csrf_exempt 
import hashlib, hmac
# for mail testing 

# -- Home Page --
# handles both member and guest home page

def sitemap(request):
    return HttpResponseRedirect('/static/sitemap.xml',mimetype='application/xml')

def home(request):
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
        return render(request,'guest_home.html', {})

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
        return render(request,'guest_home.html', { 'ad_visit':True,'google_ad_visit':True})

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
        return render(request,'guest_home.html', {'ad_visit':True,'bing_ad_visit':True})
    
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
        return render(request,'guest_home.html', {'ad_visit':True,'facebook_ad_visit':True})
        
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



# fake page used to create custom content for fb send dialog (from setup create form)
def setup_by(request,first_name = "",last_initial = ""):
 
    if first_name == "" and last_initial=="":
        return render(request, 'guest_home.html',
                          {
                           'change_title': 'Your friend recommended someone for you', 
                           'change_description': "CrushMaven is a new matchmaking service for people who already have someone in mind - for themselves or friends of theirs.  Log in now to see who " + first_name + " is trying to set you up with.",
                           })    
    else:
            return render(request, 'guest_home.html',
                              {
                               'change_title': first_name + " " + last_initial  + '. recommended someone for you!', 
                               'change_description': "CrushMaven is a new matchmaking service for people who already have someone in mind - for themselves or friends of theirs.  Log in now to see who " + first_name + " is trying to set you up with.",
                               'change_url':"http://www.crushmaven.com/setup_by/" + first_name + "/" + last_initial + "/"
                               })    
    return HttpResponse("")

# fake page used to create custom content for fb send dialog (from setup request)
def setup_for(request,first_name = "",last_initial = ""):
 
    if first_name == "" and last_initial=="":
        return render(request, 'guest_home.html',
                          {
                           'change_title': 'Your friend desires your matchmaking help!', 
                           'change_description': "CrushMaven is a new matchmaking service for people who already have someone in mind - for themselves or friends of theirs.  Help " + first_name + " out at crushmaven.com.",
                           })    
    else:
            return render(request, 'guest_home.html',
                              {
                               'change_title': first_name + " " + last_initial  + '. desires your matchmaking help!', 
                               'change_description': "CrushMaven is a new matchmaking service for people who already have someone in mind - for themselves or friends of theirs.  Help " + first_name + " out at crushmaven.com.",
                                'change_url':"http://www.crushmaven.com/setup_for/" + first_name + "/" + last_initial + "/"
                               })    
    return HttpResponse("")

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
