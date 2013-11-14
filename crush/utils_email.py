from django.template.loader import render_to_string
#from crush.models.user_models import FacebookUser
from django.conf import settings
import requests
import os
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

CDN_URL = os.getenv('CDN_SUMO_URL')
STATIC_URL = 'http://' + str(CDN_URL) + '/static/'
    
def send_mailgun_email(from_string, email_address,subject,html_message,text_message,send_time=None):
        try:
            data_dict={"from": from_string,\
                          "to": email_address,"subject": subject, "html": html_message, "text": text_message}
#            data_dict={"from": from_string,\
#                           "to": email_address,"subject": subject, "html":html_message}
            if send_time != None:
                data_dict["o:deliverytime"]=str(send_time) 
            logger.debug(str(data_dict))
            logger.debug("sending mail from :" + from_string + " to: " + email_address + " with subject: " + subject + " and message: " + text_message)
            result= requests.post("https://api.mailgun.net/v2/flirtally.com/messages",auth=("api", settings.MAILGUN_API_KEY),data=data_dict)
            logger.debug( "MailGun Response: " + str(result))
        
        except Exception as e:
            print "MAIL PROBLEM! " + str(type(e)) + " : " + str(e)

def send_mail_user_logged_in(user, header_string):
    if user.username not in ['100006341528806','1057460663','100004192844461','651900292','100003843122126']:
        send_mailgun_email('Flirtally Admin <admin@flirtally.com>','chris_h_cheng@hotmail.com',user.get_name() + ' logged in!',header_string,header_string)
            
def send_mail_crush_invite(friendship_type,full_name, short_name, first_name,email_address):
    html=render_to_string('email_template_crush_invite.html',{'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_crush_invite_text.html',{'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name,'STATIC_URL':STATIC_URL})
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,full_name + ' has an admirer (one of our users)',html,text)
    
def send_mail_mf_invite(full_name,short_name,first_name,crush_pronoun_subject,crush_pronoun_possessive, email_address):
    html=render_to_string('email_template_mf_invite.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':crush_pronoun_subject,'pronoun_possessive':crush_pronoun_possessive,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_mf_invite_text.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':crush_pronoun_subject,'pronoun_possessive':crush_pronoun_possessive,'STATIC_URL':STATIC_URL})
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,full_name + " has an admirer (one of our users)",html,text)

def send_mail_new_admirer(friendship_type,full_name, short_name, first_name,email_address):
    html=render_to_string('email_template_notify_new_admirer.html',{'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_new_admirer_text.html',{'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name,'STATIC_URL':STATIC_URL})
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,short_name + ', you have a new admirer!',html,text)
    
def send_mail_new_attraction_response(full_name, short_name, first_name,pronoun_subject,pronoun_possessive,email_address,send_time=None):
    html=render_to_string('email_template_notify_new_attraction_response.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_new_attraction_response_text.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,short_name + ' responded to your crush!',html,text,send_time)
    
def send_mail_changed_attraction_response(is_attracted,full_name, short_name, first_name,pronoun_subject,pronoun_possessive,email_address):
    html=render_to_string('email_template_notify_changed_attraction_response.html',{'is_attracted':is_attracted,'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_changed_attraction_response_text.html',{'is_attracted':is_attracted,'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,short_name + ' changed ' + pronoun_possessive + ' mind',html,text)
    
def send_mail_setup_target_response(full_name, short_name, first_name,pronoun_subject,pronoun_possessive,email_address):
    html=render_to_string('email_template_notify_setup_target_response.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_setup_target_response_text.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,short_name + ' responded to your setup!',html,text)

def send_mail_setup_recommendee_response(full_name, short_name, first_name,pronoun_subject,pronoun_possessive,target_full_name,is_attracted,email_address):
    html=render_to_string('email_template_notify_setup_recommendee_response.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'target_full_name':target_full_name,'is_attracted':is_attracted,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_setup_recommendee_response_text.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'target_full_name':target_full_name,'is_attracted':is_attracted,'STATIC_URL':STATIC_URL})
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,short_name + ' responded to your setup!',html,text)

def send_mail_delivery_problem(full_name, short_name, first_name,invalid_email_address,email_address):
    html=render_to_string('email_template_notify_delivery_problem.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'invalid_email_address':invalid_email_address,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_delivery_problem_text.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'invalid_email_address':invalid_email_address,'STATIC_URL':STATIC_URL})
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,'Unsuccessful invite delivery to ' + invalid_email_address,html,text)

def send_mail_setup_recommendees_invited(email_address,full_name, short_name, first_name="",pronoun_subject="",pronoun_possessive="",send_time=None):    
    html=render_to_string('email_template_notify_setup_recommendees_invited.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_setup_recommendees_invited_text.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,short_name + ' notified your setup picks!',html,text,send_time)
    