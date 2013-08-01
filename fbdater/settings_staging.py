from settings import *
import logging
DEBUG = True
TEMPLATE_DEBUG = DEBUG

logging.basicConfig(
    level = logging.DEBUG,
    format = '%(asctime)s %(levelname)s %(message)s',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['null'],  # Quiet by default!
            'propagate': False,
            'level':'DEBUG',
            },
    }
}


# Facebook settings are set via environment variables
FACEBOOK_APP_ID = '341035956028074' # Crush Discovery App on Facebook
FACEBOOK_APP_SECRET = '66cb9c533b7b10798aa3daee3ec5c558'
FACEBOOK_SCOPE = 'user_about_me, friends_about_me, user_relationship_details, user_relationships, friends_relationships, friends_relationship_details, email,user_birthday, friends_birthday, user_location, friends_location'

URLLIB_TIMEOUT=30
LINEUP_BLOCK_TIMEOUT=240000 # this determines how long (in millisecons) each admirer block should wait for initialization request to return a result. if timeout, then relationship initialization status set to error state (via ajax call)
INITIALIZATION_TIMEOUT=200 # maximum amt of time in seconds before ajax initialization times out
INITIALIZATION_RESTART_TIME_CRUSH_STATUS_0=4 #minutes to wait to restart initialization if the current status is 0 (progressing)
INITIALIZATION_RESTART_TIME_CRUSH_STATUS_2=12 #hours to wait to restart initialization if the current status is 2 (admirer doesn't have enough friends)
INITIALIZATION_RESTART_TIME_CRUSH_STATUS_3=15 #minutes to wait to restart initialization if the current status is 3 (crush doesn't have enough friends)
INITIALIZATION_RESTART_TIME_CRUSH_STATUS_4_5=2 #minutes to wait to restart initialization if the current status is 4 or 5 (some sort of network or bug in system)

INITIALIZATION_THREADING=True
# auto delay the response between the start time and end time (in seconds)
CRUSH_RESPONSE_DELAY_START = 1 # 180 default = 3hours x 60 minutes =  180
CRUSH_RESPONSE_DELAY_END = 5 # 2160 default = 36 hours x 60 minutes = 2160
STARTING_CREDITS=100 # change to 1 in production
INITIALIZATION_TIMEOUT=25 # maximum amt of time before ajax initialization times out
MINIMUM_LINEUP_MEMBERS=1 # change to 4 in production = this value excludes the secret admirer themself
IDEAL_LINEUP_MEMBERS=9 # change to 4 in production = this value excludes the secret admirer themself
FRIENDS_WITH_ADMIRERS_SEARCH_DELAY=0# default is = 12 hours
MINIMUM_DELETION_DAYS_SINCE_ADD=7# 7 is default
MINIMUM_DELETION_DAYS_SINCE_RESPONSE_VIEW=7#7 is default
MAXIMUM_CRUSH_INVITE_EMAILS=7
MAXIMUM_MUTUAL_FRIEND_INVITE_EMAILS=30
MINIMUM_INVITE_RESEND_DAYS=0
MAXIMUM_ATTRACTIONS=50

#PAYPAL_PDT_TOKEN = 'HBfJRGv3GKoo9zF1_5t3uA12VlNyvALbtai1rgbZMrYT3wWGcMeuRMpp324'
PAYPAL_PDT_TOKEN = 'S_u0oAhiSDSQpdeppy9KqYANhD2dhH5pm5prcrCcHH0QSIoXLfrMn5-AD0e'
#PAYPAL_EMAIL = 'buyer1_1344811410_per@gmail.com'
#PAYPAL_EMAIL =  'seller_1344811486_biz@gmail.com'
PAYPAL_EMAIL = 'admin@flirtally.com'

PAYPAL_RETURN_URL = 'http://www.flirtally-staging.herokuapp.com/paypal_pdt_purchase'
PAYPAL_NOTIFY_URL = 'http://www.flirtally-staging.herokuapp.com/paypal_ipn_listener/'

# sandbox
PAYPAL_URL = 'https://www.sandbox.paypal.com/au/cgi-bin/webscr'
PAYPAL_PDT_URL = 'https://www.sandbox.paypal.com/au/cgi-bin/webscr'

# live
#PAYPAL_URL = 'https://www.paypal.com/au/cgi-bin/webscr'
#PAYPAL_PDT_URL = 'https://www.paypal.com/au/cgi-bin/webscr'

POSTMAN_SEND_NOTIFICATIONS_FREQUENCY=24#send notifications out once every 24 hours

POSTMAN_SHOW_USER_AS='get_name'
#MAILGUN_API_KEY = "key-6bhq7tq9k6oqc48hvp3uvq33gmt36kb1"
MAILGUN_API_KEY = 'key-23q7lzko-uih79w3mkh573yl1r69r7u4'

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


