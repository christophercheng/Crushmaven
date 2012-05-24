from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('facebook.views',
       # Facebook Backend Authentication URL's        
    url(r'^facebook/login/$', 'login'),
    url(r'^facebook/authentication_callback$', 'authentication_callback'),                    
)

urlpatterns += patterns('crush.views',
                       
    # -- HOME PAGE --
    # guest vs. member processing done at view module
    url(r'^$', 'home', name='home'),
    
    url(r'^home/$', 'home'),
    
    # -- CRUSH SEARCH -- 
    url(r'^search/$', 'search'),
    
    # -- CRUSH LIST --
    url(r'^crush_list/$', 'crush_list'),
        
    # -- ADMIRER LIST --
    url(r'^admirer_list/$', 'admirer_list'),
    
    # -- NOT INTERESTED LIST --
    url(r'^not_interested_list/$', 'not_interested_list'),
    
    # -- ADMIRER LINEUP --
    url(r'^admirer_lineup/$', 'admirer_lineup'),
    
    # -- INVITE FRIENDS --
    url(r'^invite/$', 'invite'),
    
    # -- PROFILE --
    url(r'^my_profile/$', 'my_profile'),

    # -- CREDITS --
    url(r'^my_credits/$', 'my_credits'),
    
    # -- FAQ --
    url(r'^FAQ/$', 'faq'),
    
    # -- TERMS & CONDITIONS --
    url(r'^terms/$', 'terms'),
    
)

urlpatterns += patterns('',
                        
    url(r'^logout/$', 'django.contrib.auth.views.logout'),
    # -- ADMIN PAGE -- #
    url(r'^admin/$', include(admin.site.urls)),
    
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

)
