from django.http import HttpResponse,HttpResponseNotAllowed
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from crush.models import CrushRelationship
from urllib2 import URLError,HTTPError
import datetime


# -- Friends with Admirers Page --
@login_required
def friends_with_admirers(request):
    return render(request,'friends_with_admirers.html', {})

# -- Friends with Admirers Section (Ajax Content) --
@login_required
def ajax_friends_with_admirers_content(request,remove_username=None):
    print " called friends-with-admirers-section"
    ajax_response=""
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
        
    for counter,inactive_crush_friend in enumerate(me.friends_with_admirers.all()):
        print "creating html for: " + inactive_crush_friend.username
       
        all_admirers = CrushRelationship.objects.all_admirers(inactive_crush_friend)
        num_admirers = len(all_admirers)
        if num_admirers==0:
            continue # in this case, a user was added as a friend but then someone deleted them laster
        ajax_response+="<div id='friend_admirer" + str(counter) + "'>"
        ajax_response +="<img src='" + inactive_crush_friend.get_facebook_picture() + "' width=20 height=20><small>" + inactive_crush_friend.first_name + "&nbsp;&nbsp;" + inactive_crush_friend.last_name
        ajax_response += "<br>" + str(num_admirers) + " secret admirer"
        if num_admirers > 1:
            ajax_response += "s"
        elapsed_days = (datetime.datetime.now() - all_admirers[num_admirers-1].date_added).days
        if elapsed_days==0:
            elapsed_days = "today"
        elif elapsed_days == 1:
            elapsed_days = "yesterday"
        elif elapsed_days > 60:
            elapsed_days = str(elapsed_days/30) + " months ago"
        elif elapsed_days > 30:
            elapsed_days = "1 month ago"
        else:
            elapsed_days = str(elapsed_days) + " days ago"
            
        ajax_response += " (" + elapsed_days + ")"
        ajax_response +='<br><span class="app_invite_link"><a id="send_fb_invite" crush_name="' + inactive_crush_friend.get_name() + '" crush_username="' + inactive_crush_friend.username + '" href="#">help them sign up</a>'
        ajax_response+="</small></span></div>"
    if ajax_response=="":
        ajax_response="You have no friends with admirers."
    return HttpResponse(ajax_response)
