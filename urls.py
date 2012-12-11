from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('facebook.views',
       # Facebook Backend Authentication URL's        
    url(r'^facebook/login/$', 'login'),
    url(r'^facebook/authentication_callback$', 'authentication_callback'),                    
)

urlpatterns += patterns('crush',
                       
    # -- HOME PAGE --
    # guest vs. member processing done at view module
    url(r'^$', 'views.home', name='home'),
    
    url(r'^home/$', 'views.home'),
    
   # # pending crush list is also member home page
    url(r'^accounts/login/$', 'views.home'),
 
    url(r'^crushes_in_progress/$', 'views.crushes_in_progress'),
    
    url(r'^crushes_matched/$','views.crushes_matched'),
    
    url(r'^crushes_not_matched/$','views.crushes_not_matched'),

    url(r'^admirers/$', 'views.admirers'),
        
    url(r'^admirers_past/$', 'views.admirers_past'),
    
    url(r'^just_friends/$', 'views.just_friends'),

    url(r'^friends_with_admirers/$', 'views.friends_with_admirers'),
    
    url(r'^lineup/(?P<admirer_id>\d+)/$','views.lineup'), 
    
    # -- MODAL DIALOG PROCESSING & CONTENT --
    
    url(r'^ajax_add_as_crush/(?P<crush_id>\d+)/$','views.ajax_add_as_crush'),
                        
    url(r'^modal_delete_crush/$', 'views.modal_delete_crush'),
    
    # -- SETTINGS PAGES --
    
    url(r'^settings_profile/$', 'views.settings_profile'),
    
    url(r'^settings_credits/$', 'views.settings_credits'),
    
    url(r'^settings_notifications/$','views.settings_notifications'),
    
    # -- HELP --
    url(r'^help_FAQ/$', 'views.help_faq'),
    
    url(r'^help_how_it_works/$','views.help_how_it_works'),
    
    # -- TERMS & CONDITIONS, Pricay Policy --
    url(r'^terms/$', 'views.help_terms'),
    
    url(r'^privacy_policy/$', 'views.help_privacy_policy'),
    
    # -- LOGOUT --
    url(r'^logout_view/$', 'views.logout_view'),
    
)

urlpatterns += patterns('',
    # -- ADMIN PAGE -- #
    url(r'^admin/', include(admin.site.urls)),                        
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

)
