'''
Created on Mar 19, 2013

This Scheduler Job Process calls update_fb_fetch_cookie whose main purpose is to find an updated xs cookie from the facebook account i.am.not.spam.i.swear@gmail.com.  This cookie is then set to cache where it can be used to fetch non-api facebook data.
 Recommend running once every 24 hours.

@author: Chris Work
'''



#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand
from crush.utils import update_fb_fetch_cookie, fb_fetch
import re
from crush.utils_email import send_mailgun_email

class Command(NoArgsCommand):
    def handle_noargs(self, **options):  

        update_fb_fetch_cookie()
        fetch_response = fb_fetch("2030",0)
        extracted_id_list =  re.findall( 'user.php\?id=(.*?)&',fetch_response,re.MULTILINE )
        #extracted_id_list =  re.findall( 'data-profileid=\\"(.*?)\\"',fetch_response,re.MULTILINE )
            # remove duplicates in extracted_list
        extracted_id_list = list(set(extracted_id_list))
        if len(extracted_id_list) < 1:
            send_mailgun_email('admin@crushmaven.com','chris@crushmaven.com',"FB_FETCH HAS FAILED","fb_fetch has failed. Fix immediately!","fb_fetch has failed. Fix immediately!")
            print "Facebook Fetch Failed!"
        