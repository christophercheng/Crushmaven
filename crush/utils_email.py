from django.template.loader import get_template
from django.template.loader import render_to_string
from django.template import Context
from django.conf import settings
import requests, logging

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

logger = logging.getLogger(__name__)
    
def send_mailgun_email(from_string, email_address,subject,html_message,text_message,send_time=None):
        try:
            #data_dict={"from": from_string,\
            #              "to": email_address,"subject": subject, "html": html_message.encode('utf-8'), "text":text_message.encode('utf-8')}
            data_dict={"from": from_string,\
                           "to": email_address,"subject": subject, "html":html_message}
            if send_time != None:
                data_dict["o:deliverytime"]=str(send_time) 
            print data_dict
            print "sending mail from :" + from_string + " to: " + email_address + " with subject: " + subject + " and message: " + text_message
            result= requests.post("https://api.mailgun.net/v2/flirtally.com/messages",auth=("api", settings.MAILGUN_API_KEY),data=data_dict)
            print "MailGun Response: " + str(result)
            logger.info('Mailgun Response' + str(result))
        
        except Exception as e:
            print "MAIL PROBLEM! " + str(e)
            
def send_mail_crush_invite(friendship_type,full_name, short_name, first_name,email_address):
    t = get_template('email_template_crush_invite.html')
    html=t.render(Context({'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name}))
    t = get_template('email_template_crush_invite_text.html')
    text=t.render(Context({'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name}))
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,short_name + ', you have an admirer!',html,text)
    
def send_mail_mf_invite(full_name,short_name,first_name, email_address):
    html=render_to_string('email_template_mf_invite.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name})
    text=render_to_string('email_template_mf_invite_text.html',{'full_name':full_name,'short_name':short_name,'first_name':first_name})
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,'Your friend ' + full_name + ' has an admirer!',html,text)

def send_mail_new_admirer(friendship_type,full_name, short_name, first_name,email_address):
    t = get_template('email_template_notify_new_admirer.html')
    html=t.render(Context({'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name}))
    t = get_template('email_template_notify_new_admirer_text.html')
    text=t.render(Context({'friendship_type':friendship_type,'full_name':full_name,'short_name':short_name,'first_name':first_name}))
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,short_name + ', you have a new admirer!',html,text)
    
def send_mail_new_attraction_response(full_name, short_name, first_name,pronoun_subject,pronoun_possessive,email_address,send_time=None):
    t = get_template('email_template_notify_new_attraction_response.html')
    html=t.render(Context({'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive}))
    t = get_template('email_template_notify_new_attraction_response_text.html')
    text=t.render(Context({'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive}))
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,short_name + ' responded to your attraction!',html,text,send_time)
    
def send_mail_changed_attraction_response(is_attracted,full_name, short_name, first_name,pronoun_subject,pronoun_possessive,email_address):
    t = get_template('email_template_notify_changed_attraction_response.html')
    html=t.render(Context({'is_attracted':is_attracted,'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive}))
    t = get_template('email_template_notify_changed_attraction_response_text.html')
    text=t.render(Context({'is_attracted':is_attracted,'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive}))
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,short_name + ' changed ' + pronoun_possessive + ' mind',html,text)
    
def send_mail_setup_target_response(full_name, short_name, first_name,pronoun_subject,pronoun_possessive,email_address):
    t = get_template('email_template_notify_setup_target_response.html')
    html=t.render(Context({'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive}))
    t = get_template('email_template_notify_setup_target_response_text.html')
    text=t.render(Context({'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive}))
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,short_name + ' responded to your setup!',html,text)

def send_mail_setup_recommendee_response(full_name, short_name, first_name,pronoun_subject,pronoun_possessive,target_full_name,is_attracted,email_address):
    t = get_template('email_template_notify_setup_recommendee_response.html')
    html=t.render(Context({'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'target_full_name':target_full_name,'is_attracted':is_attracted}))
    t = get_template('email_template_notify_setup_recommendee_response_text.html')
    text=t.render(Context({'full_name':full_name,'short_name':short_name,'first_name':first_name,'pronoun_subject':pronoun_subject,'pronoun_possessive':pronoun_possessive,'target_full_name':target_full_name,'is_attracted':is_attracted}))
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,short_name + ' responded to your setup!',html,text)

def send_mail_delivery_problem(full_name, short_name, first_name,invalid_email_address,email_address):
    t = get_template('email_template_notify_delivery_problem.html')
    html=t.render(Context({'full_name':full_name,'short_name':short_name,'first_name':first_name,'invalid_email_address':invalid_email_address}))
    t = get_template('email_template_notify_delivery_problem_text.html')
    text=t.render(Context({'full_name':full_name,'short_name':short_name,'first_name':first_name,'invalid_email_address':invalid_email_address}))
    send_mailgun_email('Flirtally <notifications@flirtally.com>',email_address,'Unsuccessful invite delivery to ' + invalid_email_address,html,text)