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
            #logger.debug(str(data_dict))
            logger.debug("sending mail from :" + from_string + " to: " + email_address + " with subject: " + subject)
            result= requests.post("https://api.mailgun.net/v2/crushmaven.com/messages",auth=("api", settings.MAILGUN_API_KEY),data=data_dict)
            logger.debug( "MailGun Response: " + str(result))
        
        except Exception as e:
            print "MAIL PROBLEM! " + str(type(e)) + " : " + str(e)

def send_mail_user_logged_in(user, header_string):
    if user.username not in ['100006341528806','1057460663','100004192844461','651900292','100003843122126','100007405598756']:
        send_mailgun_email('CrushMaven Admin <admin@crushmaven.com>','admin@crushmaven.com',user.get_name() + ' logged in!','http://www.facebook.com/' + str(user.username) + " " + header_string,'http://www.facebook.com/' + str(user.username) + " " + header_string)
        send_mailgun_email('CrushMaven Admin <admin@crushmaven.com>','6465732737@vmobl.com',user.get_name() + ' logged in!','http://www.facebook.com/'+str(user.username),'http://www.facebook.com/'+str(user.username))
            
def send_mail_crush_invite(friendship_type,full_name, short_name, first_name,email_address,recipient_fb_username=None):
    html=render_to_string('email_template_crush_invite.html',{'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name,'STATIC_URL':STATIC_URL,'recipient_fb_username':recipient_fb_username})
    text=render_to_string('email_template_crush_invite_text.html',{'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven Notifications <notifications@crushmaven.com>',email_address,full_name + ', you have a new admirer (not spam)',html,text)
    
def send_mail_mf_invite(full_name,short_name,first_name,crush_pronoun_subject,crush_pronoun_possessive, email_address,recipient_first_name = '',recipient_fb_username=''):
    html=render_to_string('email_template_mf_invite.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':crush_pronoun_subject,'pronoun_possessive':crush_pronoun_possessive,'STATIC_URL':STATIC_URL,'recipient_first_name':recipient_first_name,'recipient_fb_username':recipient_fb_username})
    text=render_to_string('email_template_mf_invite_text.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':crush_pronoun_subject,'pronoun_possessive':crush_pronoun_possessive,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven Notifications <notifications@crushmaven.com>',email_address,full_name + " needs your help (not spam)",html,text)

def send_mail_new_admirer(friendship_type,full_name, short_name, first_name,email_address):
    html=render_to_string('email_template_notify_new_admirer.html',{'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_new_admirer_text.html',{'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven Notifications <notifications@crushmaven.com>',email_address,short_name + ', you have a new admirer!',html,text)
    
def send_mail_new_attraction_response(full_name, short_name, first_name,pronoun_subject,pronoun_possessive,email_address,send_time=None):
    html=render_to_string('email_template_notify_new_attraction_response.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_new_attraction_response_text.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven Notifications <notifications@crushmaven.com>',email_address,short_name + ' responded to your crush!',html,text,send_time)
    
def send_mail_changed_attraction_response(is_attracted,full_name, short_name, first_name,pronoun_subject,pronoun_possessive,email_address):
    html=render_to_string('email_template_notify_changed_attraction_response.html',{'is_attracted':is_attracted,'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_changed_attraction_response_text.html',{'is_attracted':is_attracted,'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven Notifications <notifications@crushmaven.com>',email_address,short_name + ' changed ' + pronoun_possessive + ' mind',html,text)
   
def send_mail_delivery_problem(full_name, short_name, first_name,invalid_email_address,email_address):
    html=render_to_string('email_template_notify_delivery_problem.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'invalid_email_address':invalid_email_address,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_delivery_problem_text.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name,'invalid_email_address':invalid_email_address,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven Notifications <notifications@crushmaven.com>',email_address,'Unsuccessful invite delivery to ' + invalid_email_address,html,text)

def send_mail_lineup_expiration_warning(email_address,expiration_date):
    html=render_to_string('email_template_notify_lineup_expiration_warning.html',{'expiration_date':expiration_date,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_notify_lineup_expiration_warning_text.html',{'expiration_date':expiration_date,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven Notifications <notifications@crushmaven.com>',email_address,'Your admirer lineup is about to expire',html,text)
    
    
def send_mail_invite_reminder(first_name, email_address, crush_list, more_crushes_count):
    html=render_to_string('email_template_invite_reminder.html',{'first_name':first_name,'crush_list':crush_list,'more_crushes_count':more_crushes_count,'STATIC_URL':STATIC_URL})
    text=render_to_string('email_template_invite_reminder_text.html',{'first_name':first_name,'crush_list':crush_list,'more_crushes_count':more_crushes_count,'STATIC_URL':STATIC_URL})
    send_mailgun_email('CrushMaven Notifications <notifications@crushmaven.com>',email_address,'You forgot to invite your crush',html,text)
