from django.http import HttpResponse,HttpResponseNotAllowed
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from urllib2 import HTTPError


# -- Friends with Admirers Page --
@login_required
def friends_with_admirers(request):
    return render(request,'friends_with_admirers.html', {})

# -- Friends with Admirers Section (Ajax Content) --
@login_required
def ajax_friends_with_admirers_content(request,remove_username=None):
    print " called ajax friends-with-admirers-section"
    me=request.user

    try:
        if remove_username is not None:
            me.update_friends_with_admirers(remove_username)
        else:
            me.find_inactive_friends()
    except HTTPError as e:
        if e.code==400:
            return HttpResponseNotAllowed(str(e))
    except Exception as e:
        print str(e)
        return HttpResponse('') # not key functionality, so don't do anything special
        
    return HttpResponse(me.html_for_inactive_friend_section())
