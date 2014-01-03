from settings import *
import logging
DEBUG = True
TEMPLATE_DEBUG = DEBUG
ALLOWED_HOSTS = ['*']#new for django 1.5 
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
FACEBOOK_APP_ID = '711097435568407' # Crush Discovery App on Facebook
FACEBOOK_APP_SECRET = '5fa571d36c1ec81500b3abeac016abe1'
INITIALIZATION_THREADING=True

MINIMUM_LINEUP_MEMBERS=1 # change to 4 in production = this value excludes the secret admirer themself
IDEAL_LINEUP_MEMBERS=9 # change to 9 in production = this value excludes the secret admirer themself
MINIMUM_DELETION_DAYS_SINCE_ADD=0# 7 is default

PAYPAL_RETURN_URL = 'http://www.flirtally-staging.herokuapp.com/paypal_pdt_purchase'
PAYPAL_NOTIFY_URL = 'http://www.flirtally-staging.herokuapp.com/paypal_ipn_listener/'

# sandbox
PAYPAL_URL = 'https://www.sandbox.paypal.com/au/cgi-bin/webscr'
PAYPAL_PDT_URL = 'https://www.sandbox.paypal.com/au/cgi-bin/webscr'

# live
#PAYPAL_URL = 'https://www.paypal.com/au/cgi-bin/webscr'
#PAYPAL_PDT_URL = 'https://www.paypal.com/au/cgi-bin/webscr'


