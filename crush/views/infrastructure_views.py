from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from crush.models import CrushRelationship
from django.conf import settings
from crush.models.miscellaneous_models import InviteEmail
from crush.utils_email import send_mailgun_email
from crush.utils import fb_fetch#,xs_fetch
import re
#from django.test import LiveServerTestCase
from selenium import webdriver
import time

def testing(request):

    #driver = webdriver.PhantomJS("/usr/local/bin/phantomjs")
    #driver.get('http://www.facebook.com')
    #driver.find_element_by_id("email").send_keys('i.am.not.spam.i.swear@gmail.com')
    #driver.find_element_by_id("pass").send_keys('carmel1')
    #driver.find_element_by_id("loginbutton").click()
    #driver.get("https://www.facebook.com/")
    #print "cookie xs: " + str(driver.get_cookie('xs'))
    #print "all cookies: " + str(driver.get_cookies())

    #driver.close()
    result = ""
    try:
        #driver = webdriver.PhantomJS("/usr/local/bin/phantomjs")
        print"start it up now"
        print "do this"

        driver = webdriver.PhantomJS()
    except Exception as e:
        print "not able to get phantom driver: " + str(e)
        #logger.error("problems laoding phantomjs driver")
        result = "exception by webdriver startup"
        return HttpResponse(result)
    driver.get('http://www.facebook.com')
    driver.find_element_by_id("email").send_keys('i.am.not.spam.i.swear@gmail.com')
    driver.find_element_by_id("pass").send_keys('flirtally')
    driver.find_element_by_id("loginbutton").click()
    time.sleep(2)
    try:
        fb_fetch_cookie = str(driver.get_cookie(u'xs')[u'value'])
    except:
        return HttpResponse("exception by driver.get_cookie")
    driver.close()
    return HttpResponse("cookie = " + fb_fetch_cookie)
    

    
    #fetch_response = fb_fetch("1050",0)
    #extracted_id_list =  re.findall( 'user.php\?id=(.*?)&',fetch_response,re.MULTILINE )
        # remove duplicates in extracted_list
    #extracted_id_list = list(set(extracted_id_list))
    #result = "Number of results: " + str(len(extracted_id_list))
    
   
    return HttpResponse(result)

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

def home(request):

    if request.user.is_authenticated():

        if CrushRelationship.objects.visible_responded_crushes(request.user).count() > 0:
            return HttpResponseRedirect('/your_crushes/') 
        elif CrushRelationship.objects.progressing_admirers(request.user).count()>0:
            return HttpResponseRedirect('/admirers/')
        else:
            return HttpResponseRedirect('/your_crushes/')
    else:
        return render(request,'guest_home.html')


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
    logout(request)
    return HttpResponseRedirect("/home/")

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
                               'change_description': "CrushMaven is a new matchmaking service for people who already have someone in mind - for themselves or friends of theirs.  Find out who's attracted to you at crushmaven.com. | Already in a relationship?  Help set your friends up - all at crushmaven.com.",
                               'change_url':"http://www.crushmaven.com/admirer_for/" + first_name + "/" + last_initial + "/"
                               })    
    return HttpResponse("")

def xs_fetch_cookie(request):
    xs_fetch()

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
