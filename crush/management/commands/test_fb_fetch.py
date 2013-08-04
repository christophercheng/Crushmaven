<<<<<<< HEAD
"fb_fetch has failed. Fix immediately!"'''
Created on Mar 19, 2013

This Scheduler Job Process is not theoretically necessary.  The inactive user list is constantly being updated (items removed and added) by the find_or_create FacebookUser Manager function.  
However, if the cache ever gets out of whack for some odd reason, this command will help to rest the state of things.  Recommend running once every 24 hours.

@author: Chris Work
'''



#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand

from crush.utils import fb_fetch
import re
from crush.utils_email import send_mailgun_email

class Command(NoArgsCommand):
    def handle_noargs(self, **options):  

        fetch_response = fb_fetch("1090",0)
        extracted_id_list =  re.findall( 'user.php\?id=(.*?)&',fetch_response,re.MULTILINE )
        #extracted_id_list =  re.findall( 'data-profileid=\\"(.*?)\\"',fetch_response,re.MULTILINE )
            # remove duplicates in extracted_list
        extracted_id_list = list(set(extracted_id_list))
        if len(extracted_id_list) < 1:
            send_mailgun_email('admin@flirtally.com','chris@flirtally.com',"FB_FETCH HAS FAILED","fb_fetch has failed. Fix immediately!")
            print "Facebook Fetch Failed!"
        else:
=======
"fb_fetch has failed. Fix immediately!"'''
Created on Mar 19, 2013

This Scheduler Job Process is not theoretically necessary.  The inactive user list is constantly being updated (items removed and added) by the find_or_create FacebookUser Manager function.  
However, if the cache ever gets out of whack for some odd reason, this command will help to rest the state of things.  Recommend running once every 24 hours.

@author: Chris Work
'''



#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand

from crush.utils import fb_fetch
import re
from crush.utils_email import send_mailgun_email

class Command(NoArgsCommand):
    def handle_noargs(self, **options):  

        fetch_response = fb_fetch("1090",0)
        extracted_id_list =  re.findall( 'user.php\?id=(.*?)&',fetch_response,re.MULTILINE )
        #extracted_id_list =  re.findall( 'data-profileid=\\"(.*?)\\"',fetch_response,re.MULTILINE )
            # remove duplicates in extracted_list
        extracted_id_list = list(set(extracted_id_list))
        if len(extracted_id_list) < 1:
            send_mailgun_email('admin@flirtally.com','chris@flirtally.com',"FB_FETCH HAS FAILED","fb_fetch has failed. Fix immediately!")
            print "Facebook Fetch Failed!"
        else:
>>>>>>> 8cec9dd4b1c1400646863c1fb29f9d92a1d7d4f2
            print "Facebook Fetch Suceeded."