from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# Facebook Backend Authentication URL's   
urlpatterns = patterns('facebook.views',
   (r'^facebook/login/$', 'login'),
   (r'^facebook/authentication_callback$', 'authentication_callback'),                    
)

# ----      BASIC APP FUNCTIONALITY  --
urlpatterns += patterns('crush.views.infrastructure_views',
    # guest vs. member processing done at view module
    url(r'^$', 'home', name="home_short"),
    
    url(r'^home/$', 'home',name="home_medium"),  

    url(r'^accounts/login/$', 'home',name="home_long"),
    
    (r'^ajax_submit_feedback/$','ajax_submit_feedback'),

    (r'^logout_view/$', 'logout_view'),
    
    #(r'^testing/$','testing'),
)
   
# ----      CRUSH: DISPLAY AND HANDLING PAGES      ----    
urlpatterns += patterns('crush.views.crush_views',
 
    (r'^attractions/$', 'attractions'),
            
    (r'^ajax_initialize_nonfriend_lineup/(?P<target_username>\d+)/$','ajax_initialize_nonfriend_lineup'),
    
    (r'^crushes_completed/(?P<reveal_crush_id>\d+)/$','crushes_completed'),
    
    (r'^crushes_completed/$','crushes_completed'),
    
    (r'^app_invite_form/(?P<crush_username>\w+)/$','app_invite_form'),
    
    (r'^app_invite_success/$', TemplateView.as_view(template_name='app_invite_success.html')),
                        
    (r'^ajax_find_fb_user/$','ajax_find_fb_user'),
    
    # called by crush selector dialog upon submit button press
    (r'^ajax_add_crush_targets/$','ajax_add_crush_targets'),

    # deletion handling
    (r'^ajax_admin_delete_crush_target/(?P<crush_username>\w+)/$','ajax_admin_delete_crush_target'),
    (r'^ajax_can_crush_target_be_platonic_friend/(?P<crush_username>\w+)/$','ajax_can_crush_target_be_platonic_friend'),    
    (r'^ajax_make_crush_target_platonic_friend/(?P<crush_username>\w+)/$','ajax_make_crush_target_platonic_friend'),
    
)
                        
# ----      ADMIRER: DISPLAY AND HANDLING PAGES --
urlpatterns += patterns('crush.views.admirer_views',
                        
    url(r'^admirers/(?P<show_lineup>\d+)/$', 'admirers',name="admirers_show_lineup"),
    
    url(r'^admirers/$', 'admirers',name="admirers_show_all"),

    (r'^ajax_display_lineup_block/(?P<display_id>\d+)/$','ajax_display_lineup_block'),
    
    (r'^ajax_initialization_failed/(?P<display_id>\d+)/$','ajax_initialization_failed'),
    
    (r'^ajax_show_lineup_slider/(?P<admirer_id>\d+)/$','ajax_show_lineup_slider'), 
    
    (r'^ajax_get_lineup_slide/(?P<display_id>\d+)/(?P<lineup_position>\d+)/$','ajax_get_lineup_slide'),
    
    (r'^ajax_add_lineup_member/(?P<add_type>\w+)/(?P<admirer_display_id>\d+)/(?P<facebook_id>\d+)/$','ajax_add_lineup_member'),
    
    (r'^ajax_add_lineup_member/(?P<add_type>\w+)/(?P<admirer_display_id>\d+)/(?P<facebook_id>\d+)/(?P<rating>\d)/$','ajax_add_lineup_member'),
    
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
)
    
# ----      PAYMENT PROCESSING --
urlpatterns += patterns('crush.views.payment_views', 
                         
    (r'^ajax_update_num_credits/$','ajax_update_num_credits'),
    
    (r'^credit_checker/(?P<feature_id>\d+)/(?P<unique_id>\d+)/$','credit_checker'),
    
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
    
    (r'^help_how_it_works/$','help_how_it_works'),
    
    (r'^help_terms/$', 'help_terms'),
    
    (r'^help_privacy/$', 'help_privacy'),
        
    (r'^help_contact/$', 'help_contact'),
    
    (r'^help_fb_privacy_setting/$','help_fb_privacy_setting'),
)

urlpatterns += patterns('',
    # -- ADMIN PAGE -- #
    (r'^admin/', include(admin.site.urls)),                        
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

)
