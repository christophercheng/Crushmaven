from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

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

    url(r'^crushes_completed/(?P<reveal_crush_id>\d+)/$','views.crushes_completed'),
    url(r'^crushes_completed/$','views.crushes_completed'),
    
    url(r'^app_invite_form/(?P<crush_username>\w+)/$','views.app_invite_form'),
    
    url(r'^app_invite_success/$', TemplateView.as_view(template_name='app_invite_success.html'),
        name="app_invite_success"),

    url(r'^admirers/$', 'views.admirers'),
        
    url(r'^admirers_past/$', 'views.admirers_past'),
    
    url(r'^just_friends/$', 'views.just_friends'),

    url(r'^friends_with_admirers/$', 'views.friends_with_admirers'),
    
    url(r'^friends_with_admirers_section/$', 'views.friends_with_admirers_section'), # right bar called via ajax    
    
    url(r'^select_crush_by_id/$','views.select_crush_by_id'),
    
    url(r'^lineup/(?P<admirer_id>\d+)/$','views.lineup'), 
    
    # -- MODAL DIALOG PROCESSING & CONTENT --
    
    url(r'^ajax_add_lineup_member/(?P<add_type>\w+)/(?P<admirer_display_id>\d+)/(?P<facebook_id>\d+)/$','views.ajax_add_lineup_member'),
    
    url(r'^ajax_update_num_crushes_in_progress/$','views.ajax_update_num_crushes_in_progress'),
    
    url(r'^ajax_update_num_platonic_friends/$','views.ajax_update_num_platonic_friends'),
    
    url(r'^ajax_are_lineups_initialized/$','views.ajax_are_lineups_initialized'),
        
    url(r'^ajax_display_lineup/(?P<display_id>\d+)/$','views.ajax_display_lineup'),
    
    url(r'^ajax_find_fb_user/$','views.ajax_find_fb_user'),
    
    url(r'^ajax_reconsider/$','views.ajax_reconsider'),
                               
    url(r'^modal_delete_crush/$', 'views.modal_delete_crush'),
    
    # -- SETTINGS PAGES --
    
        url(r'^settings_credits/$', 'views.settings_credits'),
    
    url(r'^settings_notifications/$','views.settings_notifications'),
    
    url(r'^settings_profile/$', 'views.settings_profile'),
    
    url(r'^credit_checker/(?P<feature_id>\d+)/$','views.credit_checker'),
    
    url(r'^paypal_purchase/$', 'views.paypal_purchase'),
    
    url(r'^paypal_ipn_listener/(?P<username>\w+)/(?P<credit_amount>\d+)/$','views.paypal_ipn_listener'),
    
    
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
