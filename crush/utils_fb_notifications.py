
#from crush.models.user_models import FacebookUser
from django.conf import settings
import urllib,json
import os
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

CDN_URL = os.getenv('CDN_SUMO_URL')
STATIC_URL = 'http://' + str(CDN_URL) + '/static/'
#returns True if good, False else
def notify_person_on_facebook(notify_person_username,destination_url, message):

    obtain_app_access_token_url="https://graph.facebook.com/oauth/access_token?client_id=" + settings.FACEBOOK_APP_ID + "&client_secret=" + settings.FACEBOOK_APP_SECRET + "&grant_type=client_credentials"
    app_token=''
    try:
        fb_result = urllib.urlopen(obtain_app_access_token_url)
        fb_result = fb_result.read()
        logger.debug("facebook obtain access token result: " + str(fb_result))
        app_token=fb_result
    except Exception as e:
        logger.debug("ERROR: couldn't obtain app token to notify facebook user because of exception: " + str(e))
        

    notify_url='https://graph.facebook.com'
    notify_url+= "/" + notify_person_username
    notify_url+="/notifications?"# + app_token
    notify_url += settings.FACEBOOK_APP_TOKEN
    notify_url+="&href=" + destination_url #must end in '/'
    notify_url+="&template=" + message
    try:
        fb_result = urllib.urlopen(notify_url,{})
        #fb_result=urllib.urlopen('http://graph.facebook.com/' + me.username + '/notes/',param)
        fb_result = json.load(fb_result)
        if 'success' not in fb_result or fb_result['success'] != True:
            logger.debug("Facebook notification unsuccessfully sent with message: " + str(message))
            return False
    except Exception as e:
        logger.debug("ERROR: could not send facebook crush response notification with message: " + str(message) + " - because of exception: " + str(e))            
        return False
    return True

