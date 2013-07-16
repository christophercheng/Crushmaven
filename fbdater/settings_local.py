
DEBUG = True
TEMPLATE_DEBUG = DEBUG


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'flirtally_db',                      # Or path to database file if using sqlite3.
        'USER': 'flirtally',                      # Not used with sqlite3.
        'PASSWORD': 'flirtally',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
       'PORT': '5432',                      # Set to empty string for default. Not used with sqlite3.
    }           

#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
#       'NAME': 'fbdater.sqlite',                      # Or path to database file if using sqlite3.
#        'USER': '',                      # Not used with sqlite3.
#        'PASSWORD': '',                  # Not used with sqlite3.
#        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
#        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
#    }   

}

# Facebook settings are set via environment variables
FACEBOOK_APP_ID = '387261624645161' # Crush Discovery App on Facebook
FACEBOOK_APP_SECRET = '6345441a2465ba85844916375bbc88aa'
FACEBOOK_SCOPE = 'user_about_me, friends_about_me, user_relationship_details, user_relationships, friends_relationships, friends_relationship_details, email,user_birthday, friends_birthday, user_location, friends_location'


URLLIB_TIMEOUT=30
LINEUP_BLOCK_TIMEOUT=240000 # this determines how long (in millisecons) each admirer block should wait for initialization request to return a result. if timeout, then relationship initialization status set to error state (via ajax call)
INITIALIZATION_TIMEOUT=200 # maximum amt of time in seconds before ajax initialization times out
INITIALIZATION_RESTART_TIME_CRUSH_STATUS_0=4 #minutes to wait to restart initialization if the current status is 0 (progressing)
INITIALIZATION_RESTART_TIME_CRUSH_STATUS_2=12 #hours to wait to restart initialization if the current status is 2 (admirer doesn't have enough friends)
INITIALIZATION_RESTART_TIME_CRUSH_STATUS_3=15 #minutes to wait to restart initialization if the current status is 3 (crush doesn't have enough friends)
INITIALIZATION_RESTART_TIME_CRUSH_STATUS_4_5=2 #minutes to wait to restart initialization if the current status is 4 or 5 (some sort of network or bug in system)

INITIALIZATION_THREADING=False
# auto delay the response between the start time and end time (in seconds)
CRUSH_RESPONSE_DELAY_START = 1 # 180 default = 3hours x 60 minutes =  180
CRUSH_RESPONSE_DELAY_END = 5 # 2160 default = 36 hours x 60 minutes = 2160
STARTING_CREDITS=100 # change to 1 in production
INITIALIZATION_TIMEOUT=25 # maximum amt of time before ajax initialization times out
MINIMUM_LINEUP_MEMBERS=1 # change to 4 in production = this value excludes the secret admirer themself
IDEAL_LINEUP_MEMBERS=9 # change to 4 in production = this value excludes the secret admirer themself
FRIENDS_WITH_ADMIRERS_SEARCH_DELAY=0# default is = 12 hours
MINIMUM_DELETION_DAYS_SINCE_ADD=0# 7 is default
MINIMUM_DELETION_DAYS_SINCE_RESPONSE_VIEW=0#7 is default
MAXIMUM_CRUSH_INVITE_EMAILS=7
MAXIMUM_MUTUAL_FRIEND_INVITE_EMAILS=30
MINIMUM_INVITE_RESEND_DAYS=0
MAXIMUM_ATTRACTIONS=50

# TODO - THESE MUST BE SET
#RESOURCES_DIR = '/media/shared/src/django-paypal-store-example/samplesite/resources/'
PAYPAL_PDT_TOKEN = 'HBfJRGv3GKoo9zF1_5t3uA12VlNyvALbtai1rgbZMrYT3wWGcMeuRMpp324'
#PAYPAL_EMAIL = 'buyer1_1344811410_per@gmail.com'
PAYPAL_EMAIL =  'seller_1344811486_biz@gmail.com'
PAYPAL_RETURN_URL = 'http://142.255.66.205:443/paypal_pdt_purchase'
PAYPAL_NOTIFY_URL = 'http://142.255.66.205:443/paypal_ipn_listener/'
# sandbox
PAYPAL_URL = 'https://www.sandbox.paypal.com/au/cgi-bin/webscr'
PAYPAL_PDT_URL = 'https://www.sandbox.paypal.com/au/cgi-bin/webscr'

# live
#PAYPAL_URL = 'https://www.paypal.com/au/cgi-bin/webscr'
#PAYPAL_PDT_URL = 'https://www.paypal.com/au/cgi-bin/webscr'


POSTMAN_SEND_NOTIFICATIONS_FREQUENCY=24#send notifications out once every 24 hours

POSTMAN_SHOW_USER_AS='get_name'
MAILGUN_API_KEY = "key-6bhq7tq9k6oqc48hvp3uvq33gmt36kb1"



