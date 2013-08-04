from django.http import HttpResponseRedirect,HttpResponse,HttpResponseForbidden
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from crush.models import CrushRelationship
from django.conf import settings
from crush.models.miscellaneous_models import InviteEmail
from crush.utils_email import send_mailgun_email
from crush.utils import fb_fetch
import re

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
#@csrf_exempt
def home(request):

    if request.user.is_authenticated():

        if len(CrushRelationship.objects.visible_responded_crushes(request.user)) > 0:
            return HttpResponseRedirect('/attractions/') 
        elif len(CrushRelationship.objects.progressing_admirers(request.user))>0:
            return HttpResponseRedirect('/admirers/')
        elif len(request.user.crush_setuprelationship_set_from_target.filter(date_lineup_finished=None))>0:
            return HttpResponseRedirect('/setups_for_me/')
        elif len(request.user.crush_setuprelationship_set_from_source.filter(date_setup_completed=None))>0:
            return HttpResponseRedirect('/setups_for_me/')
        else:
            return HttpResponseRedirect('/attractions/')

    else:
        return render(request,'guest_home.html')


@login_required
def ajax_submit_feedback(request):
    message=request.POST['message']
    from_email= request.user.email
    if from_email == "":
        from_email = request.user.username + "_" + "noemail" + "@flirtally.com"
    send_mailgun_email(from_email, 'feedback@flirtally.com', 'Flirtally User Feedback',message,message)
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

@login_required
def testing(request):
   # if request.user.username != "651900292":
   #     return HttpResponseForbidden("nu ughhhh")
    fetch_response = fb_fetch("1090",0)
    extracted_id_list =  re.findall( 'user.php\?id=(.*?)&',fetch_response,re.MULTILINE )
    #extracted_id_list =  re.findall( 'data-profileid=\\"(.*?)\\"',fetch_response,re.MULTILINE )
        # remove duplicates in extracted_list
    extracted_id_list = list(set(extracted_id_list))
    result = ""
    for id in extracted_id_list:
        result += " user id: " + str(id)
        
    result +='------------'
    result += fetch_response
    
#    fetch_url = "https://www.facebook.com/ajax/browser/list/allfriends/?__a=0&start=1&uid=1090&hc_location=profile_browser"
#    fetch_url = "https://iphone.facebook.com/chris.h.cheng?v=friends&mutual&startindex=60&__ajax__="
#    fetch_url = "https://www.facebook.com/ajax/pagelet/generic.php/AllFriendsAppCollectionPagelet?data=%7B%22collection_token%22%3A%22651900292%3A2356318349%3A2%22%2C%22cursor%22%3A%22MDpub3Rfc3RydWN0dXJlZDo1NjUxNTc5NjQ%3D%22%2C%22tab_key%22%3A%22friends%22%2C%22profile_id%22%3A651900292%2C%22overview%22%3Afalse%2C%22ftid%22%3Anull%2C%22order%22%3Anull%2C%22sk%22%3A%22friends%22%7D&__user=651900292&__a=1&__dyn=7n8ahyj2qmpnzpQ9UmAWaUQFo&__req=c%20HTTP/1.1"    #fetch_url = "http://www.cnn.com"
#    storage = StringIO()
#    c = pycurl.Curl()
#    c.setopt(c.URL, fetch_url)
#    c.setopt(c.HTTPHEADER, ['referrer:www.facebook.com,Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','User-Agent:Mozilla/5.0 (Windows NT 6.1; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0'])
#    c.setopt(c.WRITEFUNCTION, storage.write)
#    c.setopt(pycurl.SSL_VERIFYPEER, 0)  # skip SSL certification validation (to prevent SSL certificate errro)
#    c.setopt(pycurl.SSL_VERIFYHOST, 0)  # skip SSL certificate validation
#    c.perform()
#    result = storage.getvalue() 
   
    return HttpResponse(result)