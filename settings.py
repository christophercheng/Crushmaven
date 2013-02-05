# Django settings for fbdater project.
import os, sys
# this will set the project path to /fbdater 
PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, PROJECT_PATH) 
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(SITE_ROOT, 'fbdater.sqlite'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# for testing I am running a temporary python "dumb" SMTP server that receives emails locally and displays them to the terminal
EMAIL_HOST = 'localhost'
EMAIL_PORT = '1025'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' # temporary

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False
# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(SITE_ROOT,'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '2di)!u)^iayw+r%theflbuyve&amp;rb4n*407rum9&amp;#&amp;=1p3vsko4'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',                           
    'django.core.context_processors.request',
    'django.core.context_processors.csrf',
    'django.core.context_processors.static',
    'fbdater.crush.context_processor.context_processor',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'fbdater.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'fbdater.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    
    # MAC PATH:
    #os.path.join(PROJECT_PATH, 'templates'), 
    # PC PATCH:
    os.path.join(SITE_ROOT, 'crush/templates'), 
    
    
    #"templates"
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'facebook',
    'crush',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# define the custom user that inherits from Django's User model
AUTH_USER_MODEL = 'crush.FacebookUser'

NUM_MIN_DAYS_CRUSH = 7

# Facebook settings are set via environment variables
FACEBOOK_APP_ID = '387261624645161' # Crush Discovery App on Facebook
FACEBOOK_APP_SECRET = '6345441a2465ba85844916375bbc88aa'
FACEBOOK_SCOPE = 'user_about_me, friends_about_me, user_relationship_details, user_relationships, friends_relationships, friends_relationship_details, email,user_birthday, friends_birthday, user_location, friends_location'

AUTHENTICATION_BACKENDS = (
    'facebook.backend.FacebookBackend',
    #'django.contrib.auth.backends.ModelBackend',
)

# auto delay the response between the start time and end time (in seconds)
CRUSH_RESPONSE_DELAY_START = 43200 # default is 43200 seconds = 12 hours
CRUSH_RESPONSE_DELAY_END = 86400 #86400 seconds = 24 hours
STARTING_CREDITS=100 # change to 1 in production
MINIMUM_LINEUP_MEMBERS=4 # change to 4 in production = this value excludes the secret admirer themself
IDEAL_LINEUP_MEMBERS=9 # change to 4 in production = this value excludes the secret admirer themself
FRIENDS_WITH_ADMIRERS_SEARCH_DELAY=43200 # default is 43200 seconds which = 12 hours
MINIMUM_DELETION_DAYS_SINCE_ADD=7
MINIMUM_DELETION_DAYS_SINCE_RESPONSE=7
PLATONIC_RATINGS = {
                    5:'very attractive - just not for me',
                    4:'somewhat attractive - just not for me', 
                    3:"I'm indifferent",
                    2:'slightly unattractive',
                    1:'very unattractive',




                     }

DELETION_ERROR = {0:'To prevent fraudulent behavior, attractions may not be removed within ' + str(MINIMUM_DELETION_DAYS_SINCE_ADD) +' days from the time they were added.',
                   1:'Your attraction has already started your lineup.  To prevent system gaming, attractions may only be removed once a response is received and viewed.',
                   2:'Your attraction has already responded to you.  To prevent system gaming, attractions may only be removed once their response is viewed.',
                   3: 'To prevent system gaming, attractions may only be removed once ' + str(MINIMUM_DELETION_DAYS_SINCE_RESPONSE) + ' days have passed since the since the response was originally received.',
                   }

LINEUP_STATUS_CHOICES = {0:'Not Initialized',
                         1:'Initialized',
                         2:'Sorry, we do not have enough information about your admirer to create a lineup yet.  We will notify you via email when it is ready.',
                         3:'You do not have enough friends to create a lineup at this time.',
                         4:'Sorry, we are having difficulty getting data from Facebook to create a lineup.  Please try again later.',
                         5:'Sorry, we are having difficulty initializing a lineup.  Please try again later.', # temporary failure - user can restart lineup initialization
                         }

FEATURES = {
    '1': {
        'NAME': 'Continue Viewing Secret Admirer Lineup', 
        'COST': 1,      
    },
    '2': {
        'NAME':'View Crush Response',
        'COST': 1,
    }
}

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

# LOAD development settings that override app settings
#try:
#    from dev_settings import *
#except ImportError:
#    print 'local development settings could not be imported'
#    pass

