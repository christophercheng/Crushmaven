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
INITIALIZATION_THREADING=False

PAYPAL_RETURN_URL = 'http://www.flirtally-staging.herokuapp.com/paypal_pdt_purchase'
PAYPAL_NOTIFY_URL = 'http://www.flirtally-staging.herokuapp.com/paypal_ipn_listener/'

# sandbox
PAYPAL_URL = 'https://www.sandbox.paypal.com/au/cgi-bin/webscr'
PAYPAL_PDT_URL = 'https://www.sandbox.paypal.com/au/cgi-bin/webscr'

# live
#PAYPAL_URL = 'https://www.paypal.com/au/cgi-bin/webscr'
#PAYPAL_PDT_URL = 'https://www.paypal.com/au/cgi-bin/webscr'


