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
        
    for inactive_crush_friend in me.friends_with_admirers.all():
        print "creating html for: " + inactive_crush_friend.username
       
        all_admirers = CrushRelationship.objects.all_admirers(inactive_crush_friend)
        num_admirers = len(all_admirers)
        if num_admirers==0:
            continue # in this case, a user was added as a friend but then someone deleted them laster
        ajax_response +="<li class='friend_with_admirer'><a id='send_fb_invite' crush_name='" + inactive_crush_friend.get_name() + "' crush_username='" + inactive_crush_friend.username + "' href='#'>"
        ajax_response +="<img src='" + inactive_crush_friend.get_facebook_pic(40) + "'>"
        ajax_response += "<ul>"
        ajax_response += "<li class='friend_name'>" + inactive_crush_friend.first_name + "&nbsp;" + inactive_crush_friend.last_name + "</li>"
        ajax_response += "<li class='friend_admirer_count'>" + str(num_admirers) + " admirer"
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
            
        ajax_response += " (" + elapsed_days + ")</li>"
        ajax_response +="<li class='friend_help_link'>send invite</li>"
        ajax_response+="</ul></a></li>"
    if ajax_response=="":
        ajax_response='<li id="no_friends">no friends with admirers...</li>'
    return HttpResponse(ajax_response)
