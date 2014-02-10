'''
Created on Mar 4, 2013

@author: Chris Work
'''

from django.contrib import admin
from crush.models.user_models import FacebookUser
from crush.models.relationship_models import CrushRelationship,PlatonicRelationship
from crush.models.miscellaneous_models import Purchase,InviteEmail,PastTwitterUsername
from crush.models.lineup_models import LineupMember
from postman.models import Message

class FacebookUserAdmin(admin.ModelAdmin):
    list_display = ('username','last_name','first_name','is_active','gender','is_single','date_joined','email') # what columns to display
    search_fields = ('first_name', 'last_name', 'username') # what the search box searches against
    list_filter = ('date_joined','is_active','gender','is_single','gender_pref') # right column auto-filter links
    ordering = ('-is_active','-date_joined','-last_name')
    fields=('first_name','last_name','email','gender_pref','site_credits','bNotify_crush_signup_reminder','bNotify_new_admirer','bNotify_lineup_expiration_warning','processed_activated_friends_admirers','date_joined','is_active','twitter_username','date_twitter_invite_last_sent','is_staff','is_superuser','password','bCompletedSurvey','source_person','target_person')

class CrushRelationshipAdmin(admin.ModelAdmin):
    list_display = ( 'source_person','target_person','friendship_type','target_status','lineup_initialization_status','date_added') # what columns to display
    search_fields = ('source_person__last_name', 'target_person__last_name') # what the search box searches against
    list_filter = ('target_status','friendship_type') # right column auto-filter links
    ordering = ('-date_added',)
    date_hierarchy = 'date_added'
    fields=('target_status','friendship_type','lineup_initialization_status','is_lineup_paid','is_results_paid','is_platonic_rating_paid','lineup_initialization_date_started','date_lineup_expires','lineup_auto_completed','date_invite_last_sent','date_target_signed_up','date_lineup_started','date_target_responded','date_source_last_notified','date_lineup_finished','date_results_paid','date_messaging_expires','updated_flag')
class PlatonicRelationshipAdmin(admin.ModelAdmin):
    list_display = ( 'source_person','target_person','friendship_type','rating','date_added',) # what columns to display
    search_fields = ('source_person__last_name', 'target_person__last_name') # what the search box searches against
    list_filter = ('rating','friendship_type') # right column auto-filter links
    ordering = ('-date_added',)
    date_hierarchy = 'date_added'
    fields=('source_person','target_person','friendship_type','rating','rating_comment')

class LineupMemberAdmin(admin.ModelAdmin):
    list_display = ('relationship','username','user','decision','position')
    search_fields=('username','relationship','user')
    list_filter=('decision',)
    fields=('username','user','position','decision')
    ordering = ('-relationship','position')
    raw_id_fields=('user',)
    
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('purchaser', 'price','credit_total','purchased_at')
    search_fields=('purchaser','tx')
    list_filter=('credit_total','price')    
    date_hierarchy = 'purchased_at'
    ordering=('-purchased_at',)
    fields=('purchaser','credit_total','price')
    raw_id_fields=('purchaser',)

class InviteEmailAdmin(admin.ModelAdmin):
    list_display = ('relationship','is_for_crush','mf_recipient_first_name','mf_recipient_fb_username','email','date_last_sent')
    search_fields = ('relationship','email')
    list_filter = ('date_last_sent',)
    ordering=('-date_last_sent','-is_for_crush','relationship','email')
    fields=('relationship','email', 'is_for_crush', 'mf_recipient_first_name','mf_recipient_fb_username','date_last_sent')
    raw_id_fields=('relationship',)
class PastTwitterUsernameAdmin(admin.ModelAdmin):
    list_display = ('user','twitter_username','date_twitter_invite_last_sent')
    search_fields = ('user','twitter_username')
    list_filter = ('date_twitter_invite_last_sent',)
    ordering=('-user','-date_twitter_invite_last_sent')
    fields=('twitter_username','date_twitter_invite_last_sent')
    raw_id_fields=('user',)

admin.site.register(FacebookUser,FacebookUserAdmin)
admin.site.register(CrushRelationship,CrushRelationshipAdmin)
admin.site.register(PlatonicRelationship,PlatonicRelationshipAdmin)
admin.site.register(LineupMember,LineupMemberAdmin)
admin.site.register(Purchase,PurchaseAdmin)
admin.site.register(InviteEmail,InviteEmailAdmin)
admin.site.register(PastTwitterUsername,PastTwitterUsernameAdmin)