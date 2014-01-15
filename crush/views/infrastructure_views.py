from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from crush.models import CrushRelationship
from django.conf import settings
from crush.models.miscellaneous_models import InviteEmail
from crush.utils_email import send_mailgun_email
from crush.utils import fb_fetch
import re
from django.core.cache import cache
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
    magic_cookie=str(cache.get(settings.FB_FETCH_COOKIE,''))
    return HttpResponse("cookie in cache: " + magic_cookie)
@login_required
def testing_prep(request):
    if request.user.username != '651900292':
        return HttpResponse("nu uhhhh")
    cache.set(settings.FB_FETCH_COOKIE,"151%3AmpkGYqrbJNvC7A%3A2%3A1388994027%3A15839")
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

    if request.user.is_authenticated():

        if CrushRelationship.objects.visible_responded_crushes(request.user).count() > 0:
            return HttpResponseRedirect('/your_crushes/') 
        elif CrushRelationship.objects.progressing_admirers(request.user).count()>0:
            return HttpResponseRedirect('/admirers/')
        else:
            return HttpResponseRedirect('/your_crushes/')
    else:
        return render(request,'guest_home.html', {'facebook_app_id':settings.FACEBOOK_APP_ID})

#same as home but allows me to do special tracking
def google_home(request):
    if request.user.is_authenticated():
    
            if CrushRelationship.objects.visible_responded_crushes(request.user).count() > 0:
                return HttpResponseRedirect('/your_crushes/') 
            elif CrushRelationship.objects.progressing_admirers(request.user).count()>0:
                return HttpResponseRedirect('/admirers/')
            else:
                return HttpResponseRedirect('/your_crushes/')
    else:
        return render(request,'guest_home.html', {'facebook_app_id':settings.FACEBOOK_APP_ID, 'ad_visit':True,'google_ad_visit':True})

#same as home but allows me to do special tracking
def bing_home(request):
    if request.user.is_authenticated():
    
            if CrushRelationship.objects.visible_responded_crushes(request.user).count() > 0:
                return HttpResponseRedirect('/your_crushes/') 
            elif CrushRelationship.objects.progressing_admirers(request.user).count()>0:
                return HttpResponseRedirect('/admirers/')
            else:
                return HttpResponseRedirect('/your_crushes/')
    else:
        return render(request,'guest_home.html', {'facebook_app_id':settings.FACEBOOK_APP_ID,'ad_visit':True,'bing_ad_visit':True})
    
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
        return render(request,'guest_home.html', {'facebook_app_id':settings.FACEBOOK_APP_ID,'ad_visit':True,'facebook_ad_visit':True})
        
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
    if request.user.username in ['100006341528806','1057460663','100004192844461','651900292','100003843122126','100007405598756']:
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

#import sleekxmpp
#import logging

#logging.basicConfig(level=logging.DEBUG)

#class SendMsgBot(sleekxmpp.ClientXMPP):
    """
    A basic SleekXMPP bot that will log in, send a message,
    and then log out.
    """
"""
    
    def __init__(self, jid, recipient, message):

        sleekxmpp.ClientXMPP.__init__(self, jid, 'ignore')

    
        # The message we wish to send, and the JID that
        # will receive it.
        self.recipient = recipient
        self.msg = message
    
        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start, threaded=True)

    def start(self, event):
    
        self.send_presence()
    
        self.get_roster()
    
        self.send_message(mto=self.recipient,
                        mbody=self.msg,
                        mtype='chat')
    
        # Using wait=True ensures that the send queue will be
        # emptied before ending the session.
        self.disconnect(wait=True)
        

def send_fb_chat_message(access_token,fb_from_id,fb_to_id,msg):

    
    xmpp = SendMsgBot(fb_from_id, fb_to_id, unicode(msg))
    
    xmpp.credentials['api_key'] = settings.FACEBOOK_APP_ID
    xmpp.credentials['access_token'] = access_token
    
    if xmpp.connect(('chat.facebook.com', 5222)):
        xmpp.process(block=True)
        print("Done")
    else:
        print("Unable to connect.")
"""      
