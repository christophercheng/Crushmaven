'''
Created on Jan 11, 2013

@author: Chris Work
'''
import random, urllib, json
from crush.models import LineupMembership, FacebookUser
from multiprocessing import Pool
import time

def initialize_all_lineups(user):
    print "initializing all incomplete lineups"
    uninitialized_rels=user.get_all_new_incomplete_admirer_relations().filter(is_lineup_initialized=False)
    for rel in uninitialized_rels:
        initialize_lineup(rel)

# returns true if successful, false otherwise

def initialize_lineup(self):
    print "initializing relationship for admirer: " + self.source_person.first_name + " " + self.source_person.last_name
    # get sex of admirer
    admirer_gender= 'Male' if self.source_person.gender == 'M'  else 'Female'
    if self.friendship_type == 0:
        builder_user = self.target_person # crush is building lineup from his friend list
        builder_crushes= builder_user.crush_targets.all()
        builder_just_friends = builder_user.just_friends_targets.all()
        builder_incomplete_admirer_rels = builder_user.get_all_incomplete_admirer_relations()
    else:
        builder_user = self.source_person # admirer is building lineup from his friend list
        builder_crushes= self.target_person.crush_targets.all()
        builder_just_friends = self.target_person.just_friends_targets.all()
        builder_incomplete_admirer_rels = self.target_person.get_all_incomplete_admirer_relations()
    exclude_facebook_ids=""

    # loop through all their just_friends_targets and all their crush_targets and add their ids to a fql friendlist list
    for crush in builder_crushes:
        exclude_facebook_ids = exclude_facebook_ids + "'" + crush.username + "',"
    for just_friend in builder_just_friends:
        exclude_facebook_ids = exclude_facebook_ids + "'" + just_friend.username + "',"
    
    for rel in builder_incomplete_admirer_rels:
        builder_undecided_lineup_memberships = rel.lineupmembership_set.filter(decision=None)    
    for membership in builder_undecided_lineup_memberships:
        exclude_facebook_ids = exclude_facebook_ids + "'" + membership.lineup_member.username + "',"
    # list all friends usernames who do not have a family relationship with me and are of a certain gender limited to top 9 results
    if self.friendship_type == 0: # the crush can build the lineup from his/her friend list
        # if building from crush perspective, then exclude pulling from fb 
            # -the source person (they will get inserted manually)
            # anyone already on their crush list or their platonic friend list
        if exclude_facebook_ids == "":
            exclude_facebook_ids = "'" + str(self.source_person.username) + "'"
        else:
            exclude_facebook_ids = exclude_facebook_ids + "'" + str(self.source_person.username) + "'"
    
        fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (SELECT uid FROM family where profile_id=me())) AND NOT (uid2 IN (" + exclude_facebook_ids + "))) ) AND sex = '" + admirer_gender + "'  ORDER BY friend_count DESC LIMIT 9"
    else: # the admirer must build the lineup from his friend list
        if exclude_facebook_ids != "": # remove the trailing comma
            exclude_facebook_ids = exclude_facebook_ids[:-1]
        fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (" + exclude_facebook_ids + ")) )) AND sex = '" + admirer_gender + "'  ORDER BY friend_count DESC LIMIT 9"
    print "fql_query string: " + str(fql_query)
    fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,builder_user.access_token))
    try:
        data = json.load(fql_query_results)['data']       
        if (len(data) == 0):
            if admirer_gender=='Male':
                data = [{u'username':u'zuck', 'uid':u'4'}]
            else:
                data = [{u'username':u'sheryl', 'uid':u'sheryl'}]
        print "json data results for admirer: " + self.source_person.first_name + " " + self.source_person.last_name + " : " + str(data)
      
    except ValueError:
        print "ValueError on Fql Query Fetch read!"
        return False
    except KeyError:
        print "KeyError on FQL Query Fetch read"
        return False
    # determine where the admirer should randomly fall into the lineup
    # don't ever put member in last spot, cause there's a chance crush will skip making decision at end
    admirer_position=random.randint(0, len(data)-1) # normally len(data) should be 9
    print "admirer_position: " + str(admirer_position)
    index = 0
    #number_members=len(data)+1
    #pool=Pool()
    for fql_user in data:
        print "iteration execution"
        # if the current lineup position is where the admirer should go, then insert the admirer
        if index==admirer_position:
            LineupMembership.objects.create(position=index,lineup_member=self.source_person,relationship=self,decision=None)
            print "put crush in position: " + str(index) 
            index = index + 1            
            # create a lineup member with the given username      
         
        #pool.apply_async(create_new_lineup_user,[fql_user['uid'],builder_user.access_token,index,self],) 
        #create_new_lineup_user(fb_uid=fql_user['uid'],fb_access_token=builder_user.access_token,index=index,relationship=self)
        lineup_user=FacebookUser.objects.find_or_create_user(fb_id=fql_user['uid'],fb_access_token=builder_user.access_token,is_this_for_me=False)
        LineupMembership.objects.create(position=index,lineup_member=lineup_user,relationship=self,decision=None)
        
        index = index + 1
    # the following condition (to put admirer in last position) should not occur, but just in case let's handle it    
    if len(data)==admirer_position:
        LineupMembership.objects.create(position=len(data),lineup_member=self.source_person,relationship=self,decision=None)
  
    print "number lineup members: " + str(self.lineupmembership_set.count())
    
    # don't return until all lineup members have been completed (number of lineup memberships = len(data)+1

    self.is_lineup_initialized = True
    self.save(update_fields=['number_unrated_lineup_members','is_lineup_initialized'])
    
    return True

# this can be used to asynchronously add a user and add them to a lineup
def create_new_lineup_user(fb_uid,fb_access_token,index,relationship):
    lineup_user=FacebookUser.objects.find_or_create_user(fb_id=fb_uid,fb_access_token=fb_access_token,is_this_for_me=False)
    LineupMembership.objects.create(position=index,lineup_member=lineup_user,relationship=relationship,decision=None)
    print str(relationship.admirer_display_id) + ": put friend " + lineup_user.first_name + " " + lineup_user.last_name + " in position: " + str(index)   