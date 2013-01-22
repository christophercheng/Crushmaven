from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

#from django.contrib.auth.models import Use
# to allow app to run in facebook canvas without csrf error:
#from django.views.decorators.csrf import csrf_exempt 
# for mail testing 

# -- Home Page --
# handles both member and guest home page
#@csrf_exempt
def home(request):
    
    if request.user.is_authenticated():
        #if len(FacebookUser.objects.all()) == 1 and request.user.username==:
        #   fake_ids=['1057460663','100004192844461','100003843122126']
        #    for crushee_id in fake_ids:
        #        selected_user=FacebookUser.objects.find_or_create_user(fb_id=crushee_id, fb_access_token=request.user.access_token,fb_profile=None,is_this_for_me=False)
        #        CrushRelationship.objects.create(target_person=request.user,source_person=selected_user,
        #                                                       friendship_type=0, updated_flag=True)
        return HttpResponseRedirect('/crushes_in_progress/')

    else:
        return render(request,'guest_home.html')

# -- Logout --
@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/home/")
