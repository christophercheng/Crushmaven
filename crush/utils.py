from django.conf import settings
# imports for testing
import urllib2,json,urllib
# import the logging library
import logging
from django.core.cache import cache
import time
import crush.models.user_models
from crush.utils_email import send_mailgun_email
from selenium import webdriver
import os
#from crush.models.user_models import InviteInactiveUser


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
        #logger.error("graph api fetch failed with exception: " + str(e))
        if num_tries == 0:
            # retry once more
            most_recent_user=crush.models.user_models.FacebookUser.objects.filter(is_active=True).latest('id')
            return graph_api_fetch(most_recent_user.access_token,query_string,expect_data,fql_query,1) 
            
        else:
            logger.error("Graph api fetch failed with exception: " + str(e) + " : " + str(url))
            raise e # pass on the exception for the caller to handle
        
# this function forces the cache to update its fb cookie value.  this is called daily from custom management command
def update_fb_fetch_cookie():
        try:       
            driver = webdriver.PhantomJS()
        except Exception as e:
            logger.error( "not able to get phantom driver to update fb fetch cookie.  exception: " + str(e))
            send_mailgun_email('admin@crushmaven.com','chris@crushmaven.com',"UPDATE_FB_FETCH_COOKIE HAS FAILED","UPDATE_FB_FETCH_COOKIE has failed.  driver=webdriver.phantomjs() caused exception: " + str(e) + " - Fix immediately!","UPDATE_FB_FETCH_COOKIE has failed. Fix immediately!")
            raise e
        driver.get('http://www.facebook.com')
        fb_fetch_username = os.environ.get('FB_FETCH_USERNAME', '')
        fb_fetch_password=os.environ.get('FB_FETCH_PASSWORD','')
        time.sleep(5)
        driver.find_element_by_id("email").send_keys(fb_fetch_username)
        driver.find_element_by_id("pass").send_keys(fb_fetch_password)
        driver.find_element_by_id("loginbutton").click()
        time.sleep(5)
        try:
            fb_fetch_cookie = str(driver.get_cookie(u'xs')[u'value'])
        except:
            fb_fetch_cookie=''
        if fb_fetch_cookie == "":
            logger.debug("Cookie Fetch Failed")
            #if settings.DEBUG==False:
            #    send_mailgun_email('admin@crushmaven.com','chris@crushmaven.com',"UPDATE_FB_FETCH_COOKIE HAS FAILED","UPDATE_FB_FETCH_COOKIE has failed. Fix immediately!","UPDATE_FB_FETCH_COOKIE has failed. Fix immediately!")
        else:
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
    
def user_can_be_messaged(magic_cookie,username):
 # run the actual fql batch query, try it a second time if it fails
    try:
        fetch_url='http://www.facebook.com/dialog/send?app_id=563185300424922&to=' + username + '&link=http://www.google.com&redirect_uri=http://www.crushmaven.com'
        opener = urllib2.build_opener()   
        opener.addheaders.append(('Cookie','c_user=100007492440319; xs=' + magic_cookie)) 
        fetch_response = urllib2.Request(fetch_url)
        fetch_response = opener.open(fetch_response,None,settings.URLLIB_TIMEOUT)
        fetch_response = fetch_response.read()        
        if 'platform_dialog_error' in fetch_response:
            return False
        else:
            return True
    except:
        return False

        
 