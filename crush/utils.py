from django.conf import settings
# imports for testing
import urllib2,json,urllib
# import the logging library
import logging
from django.core.cache import cache
import time
from crush.utils_email import send_mailgun_email
from selenium import webdriver
# Get an instance of a logger
logger = logging.getLogger(__name__)

# if the access_token is invalid, then returns HTTPError (subclass of URLError) with code 400
# if the query string is invalid, then returns HTTPError with code 404
# if urllib2 times out then returns URLError with reason="timed out"
def graph_api_fetch(access_token,query_string,expect_data=True, fql_query=False,num_tries=0):
    
    try:
        if not fql_query:
            url='https://graph.facebook.com/' + query_string
            if access_token!='':
                if "?" not in url:
                    url += "?access_token=" + access_token
                else:
                    url += "&access_token=" + access_token
            results= urllib2.urlopen(url,None,settings.URLLIB_TIMEOUT)
        else:
            # for some reason this guy didn't like urllib2
            params = {'q':query_string}
            if access_token!='':
                params['access_token'] = access_token
            url='https://graph.facebook.com/fql?' + urllib.urlencode(params)
            results= urllib2.urlopen(url,None,settings.URLLIB_TIMEOUT)

        results = json.load(results)
        if expect_data:
            if 'data' in results:
                return results['data']
            else:
                # retry once more
                if num_tries == 0:
                    return graph_api_fetch(access_token,query_string,expect_data,fql_query,1) 
                else:
                    return None
        else:
            return results  
    except Exception as e: 
        if num_tries == 0:
            logger.warning( "graph api fetch failed, trying again with access_token: " + str(access_token) )
            # retry once more
            return graph_api_fetch(access_token,query_string,expect_data,fql_query,1) 
            
        else:
            logger.error("failed graph api fetch exception: " + str(e))
            raise e # pass on the exception for the caller to handle
        
# this function forces the cache to update its fb cookie value.  this is called daily from custom management command
def update_fb_fetch_cookie():
        try:       
            driver = webdriver.PhantomJS("./vendor/phantomjs/bin")
        except Exception as e:
            print "not able to get phantom driver: " + str(e)
            send_mailgun_email('admin@crushmaven.com','chris@crushmaven.com',"UPDATE_FB_FETCH_COOKIE HAS FAILED","UPDATE_FB_FETCH_COOKIE has failed.  driver=webdriver.phantomjs() caused exception.  Fix immediately!","UPDATE_FB_FETCH_COOKIE has failed. Fix immediately!")
            raise e
        driver.get('http://www.facebook.com')
        driver.find_element_by_id("email").send_keys('i.am.not.spam.i.swear@gmail.com')
        driver.find_element_by_id("pass").send_keys('flirtally')
        driver.find_element_by_id("loginbutton").click()
        time.sleep(2)
        try:
            fb_fetch_cookie = str(driver.get_cookie(u'xs')[u'value'])
        except:
            fb_fetch_cookie=''
        if fb_fetch_cookie == "":
            logger.debug("Cookie Fetch Failed")
            send_mailgun_email('admin@crushmaven.com','chris@crushmaven.com',"UPDATE_FB_FETCH_COOKIE HAS FAILED","UPDATE_FB_FETCH_COOKIE has failed. Fix immediately!","UPDATE_FB_FETCH_COOKIE has failed. Fix immediately!")
        logger.debug("Obtained Daily Cookie: " + fb_fetch_cookie)
        cache.set(settings.FB_FETCH_COOKIE,fb_fetch_cookie)
        driver.close()
        
def fb_fetch(fb_user_id,start_index):
    try:
        opener = urllib2.build_opener()   
        magic_cookie=cache.get(settings.FB_FETCH_COOKIE,'')
        if magic_cookie=='':
            update_fb_fetch_cookie()
            magic_cookie=cache.get(settings.FB_FETCH_COOKIE,'')
        opener.addheaders.append(('Cookie','c_user=100007492440319; xs=' + magic_cookie)) 
        fetch_url="https://www.facebook.com/ajax/browser/list/allfriends/?uid=" + str(fb_user_id) + "&__a=1&start=" + str(start_index)
        fetch_response = urllib2.Request(fetch_url)
        fetch_response = opener.open(fetch_response,None,settings.URLLIB_TIMEOUT)
        fetch_response = fetch_response.read()    

        return fetch_response
    except Exception as e: 
        logger.error("fb_fetch exception: " + str(e))
        raise e # pass on the exception for the caller to handle
    
#def send_mailgun_email(from_string, email_address,subject,message,send_time=None):
#        try:
#            data_dict={"from": from_string,\
#                           "to": email_address,"subject": subject,"text": message}
#            if send_time != None:
#                data_dict["o:deliverytime"]=str(send_time) 
#            print "sending mail from :" + from_string + " to: " + email_address + " with subject: " + subject + " and message: " + message
#            #result= requests.post("https://api.mailgun.net/v2/attractedto.mailgun.org/messages",auth=("api", settings.MAILGUN_API_KEY),data=data_dict)
#            #print "MailGun Response: " + str(result)
#        except Exception as e:
#            print "MAIL PROBLEM! " + str(e)

#@login_required
#def testing(request):
#    return
#
#    fetch_response=''
#    #data = urllib.urlencode({'email':'schmackforever@yahoo.com','pass':'carmel1','login':'Log+In'})
#    #jar = cookielib.FileCookieJar("cookies")
#    #fetch_url = "https://www.locationary.com/index.jsp?ACTION_TOKEN=tile_loginBar_jsp$JspView$LoginAction"
#    mobile_fb_url = "https://m.facebook.com/friends/?id=1090&f=30"
#    #fetch_url = "https://m.facebook.com/marizdluna?v=friends&mutual&startindex=24&refid=17&ref=bookmark"
#    fetch_url="https://www.facebook.com/ajax/browser/list/allfriends/?uid=721521885&__user=651900292&__a=1&start=0"
#    curl_url="https://www.facebook.com/ajax/browser/list/allfriends/?uid=721521885&__a=1&start=0"
#    my_url="http://127.0.0.1:8000"
#    #fetch_url="https://m.facebook.com"
#    #fetch_url = "https://www.facebook.com/lauren.douglass1"
#    cnn_url="http://www.cnn.com"
#    nytimes_url="http://www.nytimes.com"
#    #fetch_url = "https://www.facebook.com/ajax/browser/list/allfriends/?uid=33303361&infinitescroll=1&location=friends_tab_tl&start=38&__req=8&__a=1"
#    #fetch_url = "https://www.facebook.com/lauren.douglass1/friends?ft_ref=mni"
#    #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
#    opener = urllib2.build_opener()
#    #opener.addheaders.append(('Host', 'https://m.facebook.com'))
#    opener.addheaders.append(('USER_AGENT', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'))
#    opener.addheaders.append(('HTTP_USER_AGENT', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'))
#    opener.addheaders.append( ('Accept', '*/*') )
#    #opener.addheaders.append(('Accept-Language','en-US,en;q=0.5'))
#    opener.addheaders.append(('Accept-Encoding',''))
#    #opener.addheaders.append(('Referer','https://www.facebook.com/lauren.douglass1/friends?ft_ref=mni'))
#    #opener.addheaders.append(('Cookie', 'datr=atZ4UP1OShGVTlI-gWc21Y6h; fr=0LuO085IH0hedIzMv.AWWVHBCH6pzzhxGVVijmCO89cGM.BQeNZy.8f.AWVQP6kG; lu=Tgq-cy2cDQY2fDF37z_DtD6A; locale=en_US; c_user=651900292; csm=2; s=Aa6_YK1OD7K68gms.BRBqGN; xs=3%3A2mTnN98BEEYpPQ%3A2%3A1359389069; act=1359425131617%2F0%3A1; p=150; presence=EM359426408EuserFA2651900292A2EstateFDsb2F1359411227605Et2F_5b_5dElm2FnullEuct2F1359410437BEtrFA2loadA2EtwF1968483593EatF1359425934120EwmlFDfolderFA2inboxA2Ethread_5fidFA2user_3a637474179A2CG359426408564CEchFDp_5f651900292F58CC; sub=67108864; wd=1235x638'))
#    opener.addheaders.append(('Connection', ''))
#    
#    #fetch_request = urllib2.Request(curl_url)
#    #fetch_request = opener.open(fetch_request)
#    #fetch_response = fetch_request.read()
#    
#    #proc = subprocess.Popen(["curl", "--head", "https://www.facebook.com/ajax/browser/list/allfriends/?uid=33303361&__user=651900292&__a=1&start=0"], stdout=subprocess.PIPE)
#    #(out, err) = proc.communicate()
#    
#
#    # CURL FETCHING
##    c = pycurl.Curl()
##    fetch_response=''
##    fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me())) ORDER BY friend_count DESC LIMIT 100"
##    fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,request.user.access_token))
##    data_array = json.load(fql_query_results)['data']
##    start_position=random.randint(0, len(data_array)-11) 
##    end_position=start_position + 10
##    counter = 0
##    for fql_user in data_array[start_position:end_position]:
##        counter = counter + 1
##        for_url = "https://www.facebook.com/ajax/browser/list/allfriends/?__a=1&start=0&uid=" + str(fql_user['uid'])
##        #for_url="http://www.google.com"
##        storage = StringIO()
##        c.setopt(c.URL, curl_url)
##        c.setopt(pycurl.SSL_VERIFYPEER, 0)
##        c.setopt(pycurl.SSL_VERIFYHOST, 0)
##        c.setopt(c.WRITEFUNCTION, storage.write)
##        c.perform()
##        fetch_response = fetch_response + "Attempt:" + str(counter) + " " + storage.getvalue() 
##
##    c.close()
#    cookie=''
#    for key in request.COOKIES.keys():
#        response_key = key
#        response_value = request.COOKIES[key]
#        cookie = cookie + key + "=" + request.COOKIES[key] + ";"
#
#    fetch_response = "hey"
#    return render(request,'testing.html', {'fetch_response':fetch_response,'cookie':cookie})


#import mechanize

# def xs_fetch():
#     br = mechanize.Browser()
#     br.set_handle_robots(False)
#     cookies = mechanize.CookieJar()
#     br.set_cookiejar(cookies)
#     br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.41 Safari/534.7')]
# 
#     br.open("http://www.facebook.com/")
#     br.select_form(nr = 0)
#     br.form['email'] = "i.am.not.spammer.i.swear@gmail.com"
#     br.form['pass'] = 'iamnotspammeriswear"'
#     response = br.submit()
#     br.open("https://www.facebook.com/")
#     print response.read()
#     print " -------------- "
#     print response.info()  # headers
