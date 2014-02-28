from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from ajax_select import urls as ajax_select_urls
#from django.views.generic.base import RedirectView
from django.conf import settings

admin.autodiscover()
handler404 = 'crush.views.infrastructure_views.home'
#handler500 = '/setups_for_me/'


# Facebook Backend Authentication URL's   
urlpatterns = patterns('facebook.views',
    (r'^facebook/login/$', 'login'),
    (r'^facebook/login/(?P<next_page>\w+)/$', 'login'),
        (r'^facebook/login/(?P<next_page>\w+)/(?P<next_page_param>\w+)/$', 'login'),
    (r'^facebook/authentication_callback/$', 'authentication_callback'), 
    (r'^facebook/authentication_callback/(?P<next_page>\w+)/$', 'authentication_callback'),   
    (r'^facebook/authentication_callback/(?P<next_page>\w+)/(?P<next_page_param>\w+)/$', 'authentication_callback'),                       
)

urlpatterns += patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.STATIC_ROOT}),
)

# ----      BASIC APP FUNCTIONALITY  --
urlpatterns += patterns('crush.views.infrastructure_views',
    # guest vs. member processing done at view module

        
    url(r'^sitemap\.xml', 'sitemap'),
    
    url(r'^$', 'home', name="home_short"),
    
    url(r'^home/$', 'home',name="home_medium"),  
    
   # (r'^no_track/$','home'), 
   # to turn off tracking in anonymous pages, then add ?no_track to end of URL
    
    (r'^ghome/$','google_home'),
    (r'^bhome/$','bing_home'),
    (r'^fhome/$','facebook_home'),
    
    (r'^verify_email/(?P<username>\w+)/$','verify_email'),
    (r'^ajax_resend_verification_email/$','ajax_resend_verification_email'),
    
    (r'^ajax_submit_feedback/$','ajax_submit_feedback'),

    (r'^logout_view/$', 'logout_view'),
    
    (r'^failed_email_send/$','failed_email_send'),
    
    (r'^facebook_notification/$','home'),   


    (r'^facebook_notification/(?P<function_name>\w+)/(?P<first_arg>\w+)/(?P<second_arg>\w+)/$','facebook_notification'),   
    (r'^facebook_notification/(?P<function_name>\w+)/(?P<first_arg>\w+)/(?P<second_arg>\w+)/(?P<third_arg>\w+)/$','facebook_notification'),   
    
    (r'^inactive_crush_list/$','inactive_crush_list'),
    (r'^cached_inactive_crush_list/$','cached_inactive_crush_list'),
    (r'^testing/$','testing'),
    (r'^new_testing/$','new_testing'),    
    (r'^testing2/$','testing2'),
    
    (r'^testing_prep/$','testing_prep'),
    
    (r'^feedback_form/$','feedback_form'),
    
    (r'^post_feedback_form/$','post_feedback_form'),
        
    (r'^admirer_for/(?P<first_name>\w+)/(?P<last_initial>\w+)/$','admirer_for'),

)
   

# ----      CRUSH: DISPLAY AND HANDLING PAGES      ----    
urlpatterns += patterns('crush.views.crush_views',
 
    (r'^your_crushes/$', 'your_crushes'),
    
    (r'^your_crushes/(?P<reveal_crush_id>\w+)/$','your_crushes'),

    (r'^app_invite_form_v2/(?P<crush_username>\w+)/','app_invite_form_v2'),
        
    (r'^app_invite_success/$', TemplateView.as_view(template_name='app_invite_success.html')),
                        
    (r'^ajax_find_fb_user/$','ajax_find_fb_user'),
    
    # called by crush selector dialog upon submit button press
    (r'^ajax_add_crush_targets/$','ajax_add_crush_targets'),
    
    (r'^ajax_load_response_dialog_content/(?P<crush_id>\w+)/$','ajax_load_response_dialog_content'),
    
    (r'^ajax_get_platonic_rating/(?P<crush_id>\w+)/$','ajax_get_platonic_rating'),
    
    (r'^ajax_get_noinvite_crush_array/$','ajax_get_noinvite_crush_array'),
    
    (r'^ajax_get_invite_crush_array/$','ajax_get_invite_crush_array'),

    (r'^ajax_add_one_free_credit/$','ajax_add_one_free_credit'),
    
    # deletion handling
    (r'^ajax_can_crush_target_be_platonic_friend/(?P<crush_username>\w+)/$','ajax_can_crush_target_be_platonic_friend'),    
    (r'^ajax_make_crush_target_platonic_friend/(?P<crush_username>\w+)/$','ajax_make_crush_target_platonic_friend'),
    
    # called by new message form 
    (r'^ajax_user_can_message/(?P<crush_id>\w+)/$','ajax_user_can_message'),
)

                        
# ----      ADMIRER: DISPLAY AND HANDLING PAGES --
urlpatterns += patterns('crush.views.admirer_views',
                        
    url(r'^admirers/(?P<show_lineup>\d+)/$', 'admirers',name="admirers_show_lineup"),
    
    url(r'^admirers/$', 'admirers',name="admirers_show_all"),

    (r'^ajax_display_lineup_block/(?P<display_id>\d+)/$','ajax_display_lineup_block'),
    
    (r'^ajax_initialization_failed/(?P<display_id>\d+)/$','ajax_initialization_failed'),
    
    (r'^ajax_show_lineup_slider/(?P<admirer_id>\d+)/$','ajax_show_lineup_slider'), 
    
    (r'^ajax_get_lineup_slide/(?P<display_id>\d+)/(?P<lineup_position>\d+)/$','ajax_get_lineup_slide'),
    
    (r'^ajax_add_lineup_member/(?P<add_type>\w+)/(?P<display_id>\d+)/(?P<facebook_id>\d+)/$','ajax_add_lineup_member'),
    
    (r'^ajax_add_lineup_member/(?P<add_type>\w+)/(?P<display_id>\d+)/(?P<facebook_id>\d+)/(?P<rating>\d)/$','ajax_add_lineup_member'),
    
    (r'^ajax_add_lineup_member/(?P<add_type>\w+)/(?P<display_id>\d+)/(?P<facebook_id>\d+)/$','ajax_add_lineup_member'),
    
)

# ----      PLATONIC FRIENDS: DISPLAY AND HANDLING PAGES --
urlpatterns += patterns('crush.views.platonic_friend_views',    
    
    (r'^ajax_reconsider/$','ajax_reconsider'),
)
    
# ----      FRIENDS WITH ADMIRERS:: DISPLAY AND HANDLING PAGES --
urlpatterns += patterns('crush.views.friends_with_admirers_views', 
                        
    (r'^friends_with_admirers/$', 'friends_with_admirers'),
    
    (r'^ajax_friends_with_admirers_content/$', 'ajax_friends_with_admirers_content'), # right bar called via ajax    

    (r'^ajax_friends_with_admirers_content/(?P<remove_username>\w+)/$', 'ajax_friends_with_admirers_content'), 
)
    
# ----      PAYMENT PROCESSING --
urlpatterns += patterns('crush.views.payment_views', 
    
#    (r'^credit_checker/(?P<feature_id>\d+)/(?P<unique_id>\d+)/$','credit_checker'),
    (r'^credit_checker/$','credit_checker'),
    
    (r'^ajax_deduct_credit/(?P<feature_id>\d+)/(?P<unique_id>\d+)/$','ajax_deduct_credit'),
    
    (r'^paypal_pdt_purchase/$', 'paypal_pdt_purchase'),
    
    (r'^paypal_ipn_listener/(?P<username>\w+)/(?P<credit_amount>\d+)/$','paypal_ipn_listener'),
)
    
# ----      SETTINGS PAGES --
urlpatterns += patterns('crush.views.settings_views', 
                        
    (r'^settings_credits/$', 'settings_credits'),
    
    (r'^settings_preferences/$', 'settings_preferences'),
)
    
# ----      STATIC HELP PAGES --
urlpatterns += patterns('crush.views.static_file_views', 
    
    (r'^help_how_it_works/$','help_how_it_works'),
    
    url(r'^terms/$', 'help_terms', name='terms'),
    
    url(r'^privacy/$', 'help_privacy', name='privacy'),
        
    url(r'^contact/$', 'help_contact', name='contact'),
    
)

urlpatterns += patterns('',
    # -- ADMIN PAGE -- #
    # include the lookup urls
    (r'^admin/lookups/', include(ajax_select_urls)),
    (r'^admin/', include(admin.site.urls)),                        
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

)

urlpatterns += patterns('',
    (r'^messages/',include('postman.urls'))
)