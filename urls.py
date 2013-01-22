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

urlpatterns += patterns('crush.views',
                       
    # -- BASIC APP FUNCTIONALITY  --
    # guest vs. member processing done at view module
    url(r'^$', 'app_views.home', name='app_views.home'),
    
    url(r'^home/$', 'app_views.home'),  
   # # pending crush list is also member home page
    url(r'^accounts/login/$', 'app_views.home'),

    url(r'^logout_view/$', 'app_views.logout_view'),
    
    # -- CRUSH: DISPLAY AND HANDLING PAGES --
 
    url(r'^crushes_in_progress/$', 'crush_views.crushes_in_progress'),
            
    url(r'^ajax_initialize_nonfriend_lineup/(?P<target_username>\d+)/$','crush_views.ajax_initialize_nonfriend_lineup'),
    
    url(r'^select_crush_by_id/$','crush_views.select_crush_by_id'),

    url(r'^crushes_completed/(?P<reveal_crush_id>\d+)/$','crush_views.crushes_completed'),
    
    url(r'^crushes_completed/$','crush_views.crushes_completed'),
    
    url(r'^app_invite_form/(?P<crush_username>\w+)/$','crush_views.app_invite_form'),
    
    url(r'^app_invite_success/$', TemplateView.as_view(template_name='app_invite_success.html'),
        name="app_invite_success"),
                        
    url(r'^ajax_find_fb_user/$','crush_views.ajax_find_fb_user'),
                        
    # -- ADMIRER: DISPLAY AND HANDLING PAGES --

    url(r'^admirers/(?P<show_lineup>\d+)/$', 'admirer_views.admirers'),
    
    url(r'^admirers/$', 'admirer_views.admirers'),
    
    url(r'^ajax_display_lineup_block/(?P<display_id>\d+)/$','admirer_views.ajax_display_lineup_block'),
    
    url(r'^ajax_show_lineup_slider/(?P<admirer_id>\d+)/$','admirer_views.ajax_show_lineup_slider'), 
    
    url(r'^ajax_get_lineup_slide/(?P<display_id>\d+)/(?P<lineup_position>\d+)/$','admirer_views.ajax_get_lineup_slide'),
    
    url(r'^ajax_add_lineup_member/(?P<add_type>\w+)/(?P<admirer_display_id>\d+)/(?P<facebook_id>\d+)/$','admirer_views.ajax_add_lineup_member'),
    
    url(r'^ajax_update_num_crushes_in_progress/$','admirer_views.ajax_update_num_crushes_in_progress'),
    
    url(r'^ajax_update_num_platonic_friends/$','admirer_views.ajax_update_num_platonic_friends'),
        
    url(r'^admirers_past/$', 'admirer_views.admirers_past'),
    
    # -- PLATONIC FRIENDS: DISPLAY AND HANDLING PAGES --
    
    url(r'^just_friends/$', 'platonic_friend_views.just_friends'),
    
    url(r'^ajax_reconsider/$','platonic_friend_views.ajax_reconsider'),
    
    # -- FRIENDS WITH ADMIRERS:: DISPLAY AND HANDLING PAGES --

    url(r'^friends_with_admirers/$', 'friends_with_admirers_views.friends_with_admirers'),
    
    url(r'^friends_with_admirers_section/$', 'friends_with_admirers_views.friends_with_admirers_section'), # right bar called via ajax    
    
    # -- PAYMENT PROCESSING --
    
    url(r'^ajax_update_num_credits/$','payment_views.ajax_update_num_credits'),
    
    url(r'^credit_checker/(?P<feature_id>\d+)/(?P<relationship_display_id>\d+)/$','payment_views.credit_checker'),
    
    url(r'^ajax_deduct_credit/(?P<feature_id>\d+)/(?P<relationship_display_id>\d+)/(?P<current_user_is_target>\d+)/$','payment_views.ajax_deduct_credit'),
    
    url(r'^paypal_purchase/$', 'payment_views.paypal_purchase'),
    
    url(r'^paypal_ipn_listener/(?P<username>\w+)/(?P<credit_amount>\d+)/$','payment_views.paypal_ipn_listener'),
    
    # -- SETTINGS PAGES --
    
    url(r'^settings_credits/$', 'settings_views.settings_credits'),
    
    url(r'^settings_notifications/$','settings_views.settings_notifications'),
    
    url(r'^settings_profile/$', 'settings_views.settings_profile'),
    
    # -- STATIC HELP PAGES --
    
    url(r'^help_FAQ/$', 'static_file_views.help_faq'),
    
    url(r'^help_how_it_works/$','static_file_views.help_how_it_works'),
    
    url(r'^terms/$', 'static_file_views.help_terms'),
    
    url(r'^privacy_policy/$', 'static_file_views.help_privacy_policy'),
)

urlpatterns += patterns('',
    # -- ADMIN PAGE -- #
    url(r'^admin/', include(admin.site.urls)),                        
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

)
