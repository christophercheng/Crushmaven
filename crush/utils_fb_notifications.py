
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
    logger.debug("sending fb notification to: " + str(notify_person_username) + " with url: " + str(destination_url) + " with message: " + str(message))
    if settings.SEND_NOTIFICATIONS==False or notify_person_username in ['100006341528806','1057460663','100004192844461','651900292','100003843122126','100007405598756']:
        return
    notify_url='https://graph.facebook.com'
    notify_url+= "/" + notify_person_username
    notify_url+="/notifications?access_token="# + app_token
    notify_url += settings.FACEBOOK_APP_TOKEN
    notify_url+="&href=" + destination_url #must end in '/'
    notify_url+="&template=" + message
    notify_url=str(notify_url)
    try:
        fb_result = urllib.urlopen(notify_url,{})
        #fb_result=urllib.urlopen('http://graph.facebook.com/' + me.username + '/notes/',param)
        fb_result = json.load(fb_result)
        if 'success' not in fb_result or fb_result['success'] != True:
            logger.debug("Facebook notification unsuccessfully sent with error: " + str(fb_result))
            return False
    except Exception as e:
        logger.debug("ERROR: could not send facebook crush response notification with message: " + str(message) + " - because of exception: " + str(e))            
        return False
    return True

