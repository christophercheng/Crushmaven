from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from crush.models import CrushRelationship
from django.conf import settings
from crush.models.miscellaneous_models import InviteEmail
from crush.utils_email import send_mailgun_email



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
        return render(request,'guest_home.html',{'site_root':settings.SITE_ROOT,'project_path':settings.PROJECT_PATH})


@login_required
def ajax_submit_feedback(request):
    message=request.POST['message']
    from_email= request.user.email
    if from_email == "":
        from_email = request.user.username + "_" + "noemail" + "@flirtally.com"
    send_mailgun_email(from_email, 'feedback@flirtally.com', 'Flirtally User Feedback',message,message,request.user.email)
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
    if not verify_mailgun_post(post_data['token'],post_data['timestamp'],post_data['signature']):
        return
    try:
        bad_email_address=post_data['recipient']
        print "bad email: " + str(bad_email_address) + " from " + str(request.user)
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