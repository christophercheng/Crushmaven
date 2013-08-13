'''
Created on Mar 4, 2013

@author: Chris Work
'''

from django.contrib import admin
from crush.models.user_models import FacebookUser
from crush.models.relationship_models import CrushRelationship,PlatonicRelationship,SetupRelationship,SetupRequestRelationship
from crush.models.miscellaneous_models import Purchase,InviteEmail
from crush.models.lineup_models import LineupMember,SetupLineupMember

class FacebookUserAdmin(admin.ModelAdmin):
    list_display = ('username','last_name','first_name','is_active','gender','is_single','date_joined','email') # what columns to display
    search_fields = ('first_name', 'last_name', 'username') # what the search box searches against
    list_filter = ('date_joined','is_active','gender','is_single','gender_pref') # right column auto-filter links
    ordering = ('-is_active','-date_joined','-last_name')
    #fields=('first_name','last_name','email','gender','gender_pref','is_single','site_credits','bNotify_crush_signed_up','bNotify_crush_signup_reminder','bNotify_crush_responded','bNotify_new_admirer','birthday_year','age_pref_min','age_pref_max','date_joined','is_active','is_staff','is_superuser','password')
    #fields=('first_name','last_name','email','gender','gender_pref','is_single', 'matchmaker_preference','site_credits','bNotify_crush_signup_reminder','bNotify_crush_responded','bNotify_new_admirer','processed_activated_friends_admirers','birthday_year','age_pref_min','age_pref_max','date_joined','is_active','is_staff','is_superuser','password')
    fields=('first_name','last_name','email','gender','gender_pref','is_single','site_credits','bNotify_crush_signup_reminder','bNotify_crush_responded','bNotify_new_admirer','processed_activated_friends_admirers','birthday_year','age_pref_min','age_pref_max','date_joined','is_active','is_staff','is_superuser','password')

class CrushRelationshipAdmin(admin.ModelAdmin):
    list_display = ( 'source_person','target_person','friendship_type','target_status','date_added',) # what columns to display
    search_fields = ('source_person__last_name', 'target_person__last_name') # what the search box searches against
    list_filter = ('target_status','friendship_type') # right column auto-filter links
    ordering = ('-date_added',)
    date_hierarchy = 'date_added'
    fields=('target_status','friendship_type','lineup_initialization_status','is_lineup_paid','is_results_paid','is_platonic_rating_paid','target_platonic_rating','lineup_initialization_date_started','date_invite_last_sent','date_target_signed_up','date_lineup_started','date_target_responded','date_lineup_finished','date_results_paid','date_messaging_expires','recommender_person_id','updated_flag')
class PlatonicRelationshipAdmin(admin.ModelAdmin):
    list_display = ( 'source_person','target_person','friendship_type','rating','date_added',) # what columns to display
    search_fields = ('source_person__last_name', 'target_person__last_name') # what the search box searches against
    list_filter = ('rating','friendship_type') # right column auto-filter links
    ordering = ('-date_added',)
    date_hierarchy = 'date_added'
    fields=('source_person','target_person','friendship_type','rating',)

class SetupRelationshipAdmin(admin.ModelAdmin):
    list_display = ( 'source_person','target_person','date_added',) # what columns to display
    search_fields = ('source_person__last_name', 'target_person__last_name') # what the search box searches against
    #list_filter = ('target_status') # right column auto-filter links
    ordering = ('-date_added',)
    date_hierarchy = 'date_added'
    fields=('date_notification_last_sent','date_lineup_started','date_lineup_finished','date_setup_completed','display_id','updated_flag')

class SetupRequestRelationshipAdmin(admin.ModelAdmin):
    list_display = ( 'source_person','target_person','date_added',) # what columns to display
    search_fields = ('source_person__last_name', 'target_person__last_name') # what the search box searches against
    ordering = ('-date_added',)
    date_hierarchy = 'date_added'
    fields=('updated_flag',)

class LineupMemberAdmin(admin.ModelAdmin):
    list_display = ('relationship','username','user','decision','position')
    search_fields=('username','relationship','user')
    list_filter=('decision',)
    fields=('username','user','position','decision')
    ordering = ('-relationship','position')
    raw_id_fields=('user',)
    
class SetupLineupMemberAdmin(admin.ModelAdmin):
    list_display = ('relationship','username','user','decision','position','lineup_member_attraction')
    search_fields=('username','relationship','user')
    list_filter=('decision','lineup_member_attraction')
    fields=('username','user','position','decision','lineup_member_attraction','date_last_notified')
    ordering = ('-relationship','-date_last_notified','position')
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
    list_display = ('relationship','is_for_crush','email','date_last_sent')
    search_fields = ('relationship','email')
    list_filter = ('date_last_sent',)
    ordering=('-date_last_sent','-is_for_crush','relationship','email')
    fields=('relationship','email', 'is_for_crush','date_last_sent')
    raw_id_fields=('relationship',)

admin.site.register(FacebookUser,FacebookUserAdmin)
admin.site.register(CrushRelationship,CrushRelationshipAdmin)
admin.site.register(PlatonicRelationship,PlatonicRelationshipAdmin)
admin.site.register(SetupRelationship,SetupRelationshipAdmin)
admin.site.register(SetupRequestRelationship,SetupRequestRelationshipAdmin)
admin.site.register(LineupMember,LineupMemberAdmin)
admin.site.register(SetupLineupMember,SetupLineupMemberAdmin)
admin.site.register(Purchase,PurchaseAdmin)
admin.site.register(InviteEmail,InviteEmailAdmin)