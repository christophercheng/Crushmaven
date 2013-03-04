from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from crush.models import CrushRelationship
from django.core.mail import send_mail

# end imports for testing

#from django.contrib.auth.models import Use
# to allow app to run in facebook canvas without csrf error:
#from django.views.decorators.csrf import csrf_exempt 
# for mail testing 

# -- Home Page --
# handles both member and guest home page
#@csrf_exempt
def home(request):
    #print "HI from home"
    #output_dict={}
    #for header in request.META:
    #    output_dict[str(header)] = str(request.META[header])
    #output_string=''
    #for key in sorted(output_dict.iterkeys()):
    #    output_string = output_string + key + " : " + output_dict[key] + "\n"
    #    print str(key) + " : " + str(output_dict[key])
    #output_string="FUCK"
    #text_file = open("header_output", "w")
    #text_file.write(output_string)
    #text_file.close()
    
    if request.user.is_authenticated():
        #if len(FacebookUser.objects.all()) == 1 and request.user.username==:
        #   fake_ids=['1057460663','100004192844461','100003843122126']
        #    for crushee_id in fake_ids:
        #        selected_user=FacebookUser.objects.find_or_create_user(fb_id=crushee_id, fb_access_token=request.user.access_token,fb_profile=None,is_this_for_me=False)
        #        CrushRelationship.objects.create(target_person=request.user,source_person=selected_user,
        #                                                       friendship_type=0, updated_flag=True)
        
        if len(CrushRelationship.objects.progressing_admirers(request.user))>0 and len(CrushRelationship.objects.known_responded_crushes(request.user)) == 0:
            return HttpResponseRedirect('/admirers/')
        else:
            return HttpResponseRedirect('/attractions/')

    else:
        return render(request,'guest_home.html')


@login_required
def ajax_submit_feedback(request):
 
    email = request.user.email
    if email=="":
        email=request.user.username + '@attractedto.com'
    send_mail('Feedback',request.POST['message'],request.user.email,['attractedto@gmail.com'])
    return HttpResponse("")


# -- Logout --
@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/home/")

def under_construction(request):
    return render(request,'under_construction.html')