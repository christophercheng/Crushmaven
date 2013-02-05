from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from crush.models import CrushRelationship

# imports for testing
import urllib2
import urllib, json
import cookielib
import subprocess
from StringIO import StringIO    
import pycurl
import time
import random
from itertools import islice
from crush.models import LineupMember
from django.conf import settings
# end imports for testing

#from django.contrib.auth.models import Use
# to allow app to run in facebook canvas without csrf error:
#from django.views.decorators.csrf import csrf_exempt 
# for mail testing 

# -- Home Page --
# handles both member and guest home page
#@csrf_exempt
def home(request):
    print "HI from home"
    output_dict={}
    for header in request.META:
        output_dict[str(header)] = str(request.META[header])
    output_string=''
    for key in sorted(output_dict.iterkeys()):
        output_string = output_string + key + " : " + output_dict[key] + "\n"
        print str(key) + " : " + str(output_dict[key])
    output_string="FUCK"
    text_file = open("header_output", "w")
    text_file.write(output_string)
    text_file.close()
    
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

# -- Logout --
@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/home/")


@login_required
def testing(request):

    fetch_response=''
    #data = urllib.urlencode({'email':'schmackforever@yahoo.com','pass':'carmel1','login':'Log+In'})
    #jar = cookielib.FileCookieJar("cookies")
    #fetch_url = "https://www.locationary.com/index.jsp?ACTION_TOKEN=tile_loginBar_jsp$JspView$LoginAction"
    mobile_fb_url = "https://m.facebook.com/friends/?id=1090&f=30"
    #fetch_url = "https://m.facebook.com/marizdluna?v=friends&mutual&startindex=24&refid=17&ref=bookmark"
    fetch_url="https://www.facebook.com/ajax/browser/list/allfriends/?uid=721521885&__user=651900292&__a=1&start=0"
    curl_url="https://www.facebook.com/ajax/browser/list/allfriends/?uid=721521885&__a=1&start=0"
    my_url="http://127.0.0.1:8000"
    #fetch_url="https://m.facebook.com"
    #fetch_url = "https://www.facebook.com/lauren.douglass1"
    cnn_url="http://www.cnn.com"
    nytimes_url="http://www.nytimes.com"
    #fetch_url = "https://www.facebook.com/ajax/browser/list/allfriends/?uid=33303361&infinitescroll=1&location=friends_tab_tl&start=38&__req=8&__a=1"
    #fetch_url = "https://www.facebook.com/lauren.douglass1/friends?ft_ref=mni"
    #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
    opener = urllib2.build_opener()
    #opener.addheaders.append(('Host', 'https://m.facebook.com'))
    opener.addheaders.append(('USER_AGENT', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'))
    opener.addheaders.append(('HTTP_USER_AGENT', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'))
    opener.addheaders.append( ('Accept', '*/*') )
    #opener.addheaders.append(('Accept-Language','en-US,en;q=0.5'))
    opener.addheaders.append(('Accept-Encoding',''))
    #opener.addheaders.append(('Referer','https://www.facebook.com/lauren.douglass1/friends?ft_ref=mni'))
    #opener.addheaders.append(('Cookie', 'datr=atZ4UP1OShGVTlI-gWc21Y6h; fr=0LuO085IH0hedIzMv.AWWVHBCH6pzzhxGVVijmCO89cGM.BQeNZy.8f.AWVQP6kG; lu=Tgq-cy2cDQY2fDF37z_DtD6A; locale=en_US; c_user=651900292; csm=2; s=Aa6_YK1OD7K68gms.BRBqGN; xs=3%3A2mTnN98BEEYpPQ%3A2%3A1359389069; act=1359425131617%2F0%3A1; p=150; presence=EM359426408EuserFA2651900292A2EstateFDsb2F1359411227605Et2F_5b_5dElm2FnullEuct2F1359410437BEtrFA2loadA2EtwF1968483593EatF1359425934120EwmlFDfolderFA2inboxA2Ethread_5fidFA2user_3a637474179A2CG359426408564CEchFDp_5f651900292F58CC; sub=67108864; wd=1235x638'))
    opener.addheaders.append(('Connection', ''))
    
    #fetch_request = urllib2.Request(curl_url)
    #fetch_request = opener.open(fetch_request)
    #fetch_response = fetch_request.read()
    
    #proc = subprocess.Popen(["curl", "--head", "https://www.facebook.com/ajax/browser/list/allfriends/?uid=33303361&__user=651900292&__a=1&start=0"], stdout=subprocess.PIPE)
    #(out, err) = proc.communicate()
    

    # CURL FETCHING
#    c = pycurl.Curl()
#    fetch_response=''
#    fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me())) ORDER BY friend_count DESC LIMIT 100"
#    fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,request.user.access_token))
#    data_array = json.load(fql_query_results)['data']
#    start_position=random.randint(0, len(data_array)-11) 
#    end_position=start_position + 10
#    counter = 0
#    for fql_user in data_array[start_position:end_position]:
#        counter = counter + 1
#        for_url = "https://www.facebook.com/ajax/browser/list/allfriends/?__a=1&start=0&uid=" + str(fql_user['uid'])
#        #for_url="http://www.google.com"
#        storage = StringIO()
#        c.setopt(c.URL, curl_url)
#        c.setopt(pycurl.SSL_VERIFYPEER, 0)
#        c.setopt(pycurl.SSL_VERIFYHOST, 0)
#        c.setopt(c.WRITEFUNCTION, storage.write)
#        c.perform()
#        fetch_response = fetch_response + "Attempt:" + str(counter) + " " + storage.getvalue() 
#
#    c.close()
    cookie=''
    for key in request.COOKIES.keys():
        response_key = key
        response_value = request.COOKIES[key]
        cookie = cookie + key + "=" + request.COOKIES[key] + ";"

    fetch_response = "hey"
    return render(request,'testing.html', {'fetch_response':fetch_response,'cookie':cookie})

