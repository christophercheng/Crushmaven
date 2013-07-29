'''
Created on Mar 19, 2013

@author: Chris Work

PURPOSE: reminds user that they have a message, so they can read it (and pay for it!)

'''



#from __future__ import unicode_literals
from django.core.management.base import NoArgsCommand
from datetime import datetime,timedelta

from postman.models import Message

from django.db.models import Q
from django.conf import settings
import requests
from django.core.cache import cache
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class Command(NoArgsCommand):

        
    def handle_noargs(self, **options):
        date_last_sent = cache.get(settings.DATE_NOTIFICATIONS_LAST_SENT_CACHE_KEY)
        if date_last_sent == None:
            # if there is some sort of failure, process last two days worth of new messages
            date_last_sent=datetime.now()-timedelta(hours=settings.POSTMAN_SEND_NOTIFICATIONS_FREQUENCY)
            logger.debug( "date last sent that is used to process emails: " + str(date_last_sent) )

        # filter through ALL messages that are STATUS_ACCEPTED AND read_at==None and sent after the last notification date
        # output is an array of recipient id's
  
        new_recipient_emails = Message.objects.filter(Q(moderation_status=settings.STATUS_ACCEPTED),Q(read_at=None),Q(sent_at__gt=date_last_sent))\
                                        .values_list('recipient__email',flat=True).order_by('recipient__email').distinct()
        subject = "New message(s) from your attractions"
        message = "Sign in to view and respond to your new message(s)."
        data_dict={"from": "Flirtally <notifications@flirtally.com>",\
                        "subject": subject,"text": message}  
        for email in new_recipient_emails:
            # send them a notification email
            data_dict["to"]=email
            result = requests.post("https://api.mailgun.net/v2/attractedto.mailgun.org/messages",auth=("api", settings.MAILGUN_API_KEY),data=data_dict)  
            print "Sent notification to " + str(email) + " with result: " + str(result)
        cache.set(settings.DATE_NOTIFICATIONS_LAST_SENT_CACHE_KEY,datetime.now()) 
