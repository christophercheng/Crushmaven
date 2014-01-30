from django.conf import settings
# imports for testing
import urllib2,json,urllib
# import the logging library
import logging
from django.core.cache import cache
import time
from crush.utils_email import send_mailgun_email
from selenium import webdriver
import os
import crush.models.user_models
import crush.models.relationship_models
from django.db.models import Q
from django.db.models import Min
from crush.utils_email import send_mail_invite_reminder,send_mail_lineup_expiration_warning
from datetime import  datetime,timedelta
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
        logger.debug("graph api fetch failed with exception: " + str(e))
        if num_tries == 0:
            logger.warning( "graph api fetch failed, trying again with access_token: " + str(access_token) )
            # retry once more
            return graph_api_fetch(access_token,query_string,expect_data,fql_query,1) 
            
        else:
            logger.error("failed graph api fetch exception: " + str(e) + " : " + str(url))
            raise e # pass on the exception for the caller to handle
        
# this function forces the cache to update its fb cookie value.  this is called daily from custom management command
def update_fb_fetch_cookie():
        try:       
            driver = webdriver.PhantomJS()
        except Exception as e:
            logger.debug( "not able to get phantom driver to update fb fetch cookie.  exception: " + str(e))
            send_mailgun_email('admin@crushmaven.com','chris@crushmaven.com',"UPDATE_FB_FETCH_COOKIE HAS FAILED","UPDATE_FB_FETCH_COOKIE has failed.  driver=webdriver.phantomjs() caused exception: " + str(e) + " - Fix immediately!","UPDATE_FB_FETCH_COOKIE has failed. Fix immediately!")
            raise e
        driver.get('http://www.facebook.com')
        fb_fetch_username = os.environ.get('FB_FETCH_USERNAME', '')
        fb_fetch_password=os.environ.get('FB_FETCH_PASSWORD','')
        driver.find_element_by_id("email").send_keys(fb_fetch_username)
        driver.find_element_by_id("pass").send_keys(fb_fetch_password)
        driver.find_element_by_id("loginbutton").click()
        time.sleep(2)
        try:
            fb_fetch_cookie = str(driver.get_cookie(u'xs')[u'value'])
        except:
            fb_fetch_cookie=''
        if fb_fetch_cookie == "":
            logger.debug("Cookie Fetch Failed")
            if settings.DEBUG==False:
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
    
def monthly_invite_reminder():
    relevant_user_set = crush.models.user_models.FacebookUser.objects.filter( Q(Q(is_active=True),~Q(crush_targets=None)) ).annotate(min_crush_status=Min('crush_crushrelationship_set_from_source__target_status')).filter(min_crush_status=0)
    invite_sent_count=0
    for user in relevant_user_set:
        if user.email == '' or user.bNotify_crush_signup_reminder == False:
            continue
        crush_list=[]
        more_crushes_count=0
        # get all crush relationships for this user
        relevant_crush_list=user.crush_crushrelationship_set_from_source.filter(target_status__lt=1)[:5]
        for relevant_crush in relevant_crush_list:
            crush_list.append(relevant_crush.target_person.get_name())
        if len(relevant_crush_list)>4: # calculate number of other relationships
            more_crushes_count = user.crush_crushrelationship_set_from_source.filter(target_status__lt=1).count() - 5

        send_mail_invite_reminder(user.first_name, user.email, crush_list, more_crushes_count)
        invite_sent_count+=1
    logger.debug("Django Command: sent " + str(invite_sent_count) + " email invite reminders out!")
    return

# crush targets who like their admirer need to be notified eventually if their admirer doesn't view their response (which manually triggers notification)
def notify_missed_crush_targets():
    # go through and grab any crush relationships where the target_status is responded_crush and date_target_responded is in past AND the date_source_last_notified is empty
    current_date=datetime.now()
    relevant_relationships=crush.models.relationship_models.CrushRelationship.objects.filter(target_status=4,date_target_responded__lt = current_date,date_source_last_notified=None,is_results_paid=False)
    for relationship in relevant_relationships:
        relationship.notify_source_person()
    # for each grabbed relationship 
        # call notify source person
        # update date_source_last_notified
    return

def lineup_expiration_warning():
    current_date=datetime.now() + timedelta(days=1)
    relevant_relationships=crush.models.relationship_models.CrushRelationship.objects.filter(lineup_initialization_status=1,date_lineup_finished=None, date_lineup_expires__lt=current_date)
    for relationship in relevant_relationships:
        email_address = relationship.target_person.email
        if email_address!='':
            send_mail_lineup_expiration_warning(email_address,relationship.date_lineup_expires)
            logger.debug("admirer lineup warning sent: " + str(relationship))
    if relevant_relationships.count() == 0:
        logger.debug('no relationships to warn of lineup expiration')
    return
  
def auto_complete_expired_lineups():
    current_date=datetime.now()
    relevant_relationships=crush.models.relationship_models.CrushRelationship.objects.filter(lineup_initialization_status=1,date_lineup_finished=None, date_lineup_expires__lt=current_date)
    for relationship in relevant_relationships:
        logger.debug("Auto complete this relationship: " + str(relationship))
        relevant_lineup_members= relationship.lineupmember_set.filter(decision=None)
        for member in relevant_lineup_members:
            updated_fields=[]
            lineup_member_user = member.user
            if lineup_member_user==None:
                lineup_member_user=crush.models.user_models.FacebookUser.objects.find_or_create_user(member.username, member.relationship.target_person.access_token, False, fb_profile=None)
                # if the lineup member user was not found for whatever reason, then we need to modify the lineup and strip out this member
                if lineup_member_user == None:
                    continue
                member.user=lineup_member_user
                updated_fields.append('user')
            member.decision=1
            updated_fields.append('decision')
            member.save(update_fields=updated_fields)
            crush.models.relationship_models.PlatonicRelationship.objects.create(source_person=member.relationship.target_person, target_person=lineup_member_user,rating=1)

        relationship.date_lineup_finished=current_date
        relationship.lineup_auto_completed=True
        relationship.save(update_fields=['date_lineup_finished','lineup_auto_completed'])
    if relevant_relationships.count() == 0:
        logger.debug('no relationships to auto complete')
    return
