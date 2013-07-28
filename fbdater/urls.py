from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from ajax_select import urls as ajax_select_urls
from django.views.generic.base import RedirectView
from django.conf import settings

admin.autodiscover()
handler404 = 'crush.views.infrastructure_views.home'
#handler500 = '/setups_for_me/'

# Facebook Backend Authentication URL's   
urlpatterns = patterns('facebook.views',
    (r'^facebook/login/$', 'login'),
    (r'^facebook/login/(?P<next_page>\w+)/$', 'login'),
    (r'^facebook/authentication_callback/$', 'authentication_callback'), 
    (r'^facebook/authentication_callback/(?P<next_page>\w+)/$', 'authentication_callback'),                    
)

urlpatterns += patterns('',
(r'^favicon\.png$', RedirectView.as_view(url='/static/images/favicon.png')),
)


# in case something bad has happened enable this view so that all site requests go here
#urlpatterns += patterns('crush.views.infrastructure_views',    
#    (r'', 'under_construction'),
#)
urlpatterns += patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.STATIC_ROOT}),


#    url(r'^accounts/login/$','django.contrib.auth.views.login'),
)


#initialize_nf_crush(request,admirer_id,crush_id,admirer_gender,minimum_lineup_members):

# ----      LINEUP FUNCTIONALITY  --
urlpatterns += patterns('crush.views.lineup_views',
  
    (r'^initialize_fof_crush/$','initialize_fof_crush'),

)

# ----      BASIC APP FUNCTIONALITY  --
urlpatterns += patterns('crush.views.infrastructure_views',
    # guest vs. member processing done at view module
    url(r'^$', 'home', name="home_short"),
    
    url(r'^home/$', 'home',name="home_medium"),  
    
    (r'^ajax_submit_feedback/$','ajax_submit_feedback'),

    (r'^logout_view/$', 'logout_view'),
    
    (r'^failed_email_send/$','failed_email_send'),
    
    #(r'^testing/$','testing'),
)
   
# ----      CRUSH: DISPLAY AND HANDLING PAGES      ----    
urlpatterns += patterns('crush.views.crush_views',
 
    (r'^attractions/$', 'attractions'),
    
    (r'^attractions/(?P<reveal_crush_id>\w+)/$','attractions'),
    
    (r'^attractions_completed/(?P<reveal_crush_id>\w+)/$','attractions_completed'),
    
    (r'^attractions_completed/$','attractions_completed'),

    (r'^app_invite_form_v2/(?P<crush_username>\w+)/','app_invite_form_v2'),
        
    (r'^app_invite_success/$', TemplateView.as_view(template_name='app_invite_success.html')),
                        
    (r'^ajax_find_fb_user/$','ajax_find_fb_user'),
    
    # called by crush selector dialog upon submit button press
    (r'^ajax_add_crush_targets/$','ajax_add_crush_targets'),
    
    (r'^ajax_load_response_dialog_content/(?P<crush_id>\w+)/$','ajax_load_response_dialog_content'),
    
    (r'^ajax_get_platonic_rating/(?P<crush_id>\w+)/$','ajax_get_platonic_rating'),
    
    # deletion handling
    (r'^ajax_can_crush_target_be_platonic_friend/(?P<crush_username>\w+)/$','ajax_can_crush_target_be_platonic_friend'),    
    (r'^ajax_make_crush_target_platonic_friend/(?P<crush_username>\w+)/$','ajax_make_crush_target_platonic_friend'),
    
    # called by new message form 
    (r'^ajax_user_can_message/(?P<crush_id>\w+)/$','ajax_user_can_message'),
)

# ----      setup: DISPLAY AND HANDLING PAGES      ----    
urlpatterns += patterns('crush.views.setup_views',
                        
    (r'^setup_create_form/$','setup_create_form'),

    (r'^setup_create_form/(?P<target_person_username>\w+)/$','setup_create_form'),    
    
    (r'^setups_for_me/$','setups_for_me'),
    
    (r'^setups_for_me/(?P<requested_username>\w+)/$','setups_for_me'),
   
    (r'^completed_setups_for_me/$','completed_setups_for_me'),
    
    (r'^setups_by_me/$','setups_by_me'),
    
    (r'^completed_setups_by_me/$','completed_setups_by_me'),
    
    (r'^setup_requests_for_me/$','setup_requests_for_me'),
    
    (r'^setup_requests_by_me/$','setup_requests_by_me'),
    
    (r'^ajax_get_recommendee_exclude_ids/(?P<setup_target>\w+)/$','ajax_get_recommendee_exclude_ids'),
    
    (r'^ajax_create_setup_request/(?P<setup_request_target>\w+)/$','ajax_create_setup_request'),
    
    (r'^ajax_update_date_notification_last_sent/(?P<target_username>\w+)/$','ajax_update_date_notification_last_sent'),
    
    (r'^ajax_update_setup_lineup_member_date_last_notified/(?P<member_username>\w+)/$','ajax_update_setup_lineup_member_date_last_notified'),
    
)
                        
# ----      ADMIRER: DISPLAY AND HANDLING PAGES --
urlpatterns += patterns('crush.views.admirer_views',
                        
    url(r'^admirers/(?P<show_lineup>\d+)/$', 'admirers',name="admirers_show_lineup"),
    
    url(r'^admirers/$', 'admirers',name="admirers_show_all"),

    (r'^ajax_display_lineup_block/(?P<display_id>\d+)/$','ajax_display_lineup_block'),
    
    (r'^ajax_initialization_failed/(?P<display_id>\d+)/$','ajax_initialization_failed'),
    
    (r'^ajax_show_lineup_slider/(?P<admirer_id>\d+)/$','ajax_show_lineup_slider'), 
    
    (r'^ajax_show_lineup_slider/(?P<admirer_id>\d+)/(?P<is_admirer_type>\d)/$','ajax_show_lineup_slider'), 
    
    (r'^ajax_get_lineup_slide/(?P<display_id>\d+)/(?P<lineup_position>\d+)/$','ajax_get_lineup_slide'),
    
    (r'^ajax_get_lineup_slide/(?P<display_id>\d+)/(?P<lineup_position>\d+)/(?P<is_admirer_type>\d)/$','ajax_get_lineup_slide'),
    
    (r'^ajax_add_lineup_member/(?P<add_type>\w+)/(?P<display_id>\d+)/(?P<facebook_id>\d+)/$','ajax_add_lineup_member'),
    
    (r'^ajax_add_lineup_member/(?P<add_type>\w+)/(?P<display_id>\d+)/(?P<facebook_id>\d+)/(?P<rating>\d)/$','ajax_add_lineup_member'),
    
    (r'^ajax_add_lineup_member/(?P<add_type>\w+)/(?P<display_id>\d+)/(?P<facebook_id>\d+)/(?P<is_admirer_type>\d)/$','ajax_add_lineup_member'),
    
    (r'^ajax_add_lineup_member/(?P<add_type>\w+)/(?P<display_id>\d+)/(?P<facebook_id>\d+)/(?P<rating>\d)/(?P<is_admirer_type>\d)/$','ajax_add_lineup_member'),
    
    (r'^ajax_update_num_crushes_in_progress/$','ajax_update_num_crushes_in_progress'),
    
    (r'^ajax_update_num_platonic_friends/$','ajax_update_num_platonic_friends'),
    
    (r'^ajax_update_num_new_admirers/$','ajax_update_num_new_admirers'),
    
    (r'^ajax_update_num_new_responses/$','ajax_update_num_new_responses'),
    
    (r'^ajax_update_num_new_responses/$','ajax_update_num_new_responses'),
    
    (r'^admirers_past/$','admirers_past'),
)

# ----      PLATONIC FRIENDS: DISPLAY AND HANDLING PAGES --
urlpatterns += patterns('crush.views.platonic_friend_views',    

    (r'^just_friends/$', 'just_friends'),
    
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
                         
    (r'^ajax_update_num_credits/$','ajax_update_num_credits'),
    
#    (r'^credit_checker/(?P<feature_id>\d+)/(?P<unique_id>\d+)/$','credit_checker'),
    (r'^credit_checker/$','credit_checker'),
    
    (r'^ajax_deduct_credit/(?P<feature_id>\d+)/(?P<unique_id>\d+)/$','ajax_deduct_credit'),
    
    (r'^paypal_pdt_purchase/$', 'paypal_pdt_purchase'),
    
    (r'^paypal_ipn_listener/(?P<username>\w+)/(?P<credit_amount>\d+)/$','paypal_ipn_listener'),
)
    
# ----      SETTINGS PAGES --
urlpatterns += patterns('crush.views.settings_views', 
                        
    (r'^settings_credits/$', 'settings_credits'),
    
    (r'^settings_notifications/$','settings_notifications'),
    
    (r'^settings_profile/$', 'settings_profile'),
)
    
# ----      STATIC HELP PAGES --
urlpatterns += patterns('crush.views.static_file_views', 
    
    (r'^help_FAQ/$', 'help_faq'),
    
    (r'^how_it_works/$','help_how_it_works'),

    (r'^how_it_works/(?P<help_type>\w+)/$','help_how_it_works'),
    
    (r'^terms/$', 'help_terms'),
    
    (r'^privacy/$', 'help_privacy'),
        
    (r'^contact/$', 'help_contact'),
    
    (r'^help_fb_privacy_setting/$','help_fb_privacy_setting'),
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