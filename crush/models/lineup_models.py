from django.db import models
import random, urllib, json
from django.conf import settings
from  crush.models.relationship_models import CrushRelationship
from crush.models.user_models import FacebookUser
from random import shuffle
from StringIO import StringIO    
import pycurl,re

class LineupMemberManager(models.Manager):
    class Meta:
    # this allows the models to be broken into separate model files
        app_label = 'crush'
    
    # need to retest!!!!
    def get_all_friends_data_array(self,crush,admirer_gender,exclude_facebook_id_array):
        exclude_facebook_ids=self.comma_delimit_list(exclude_facebook_id_array)
        '(uid1 = me() AND NOT (uid2 IN (" + exclude_facebook_ids + ")) )'
        fql_query = 'SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1="' + crush.username + '" AND NOT (uid2 IN (' + exclude_facebook_ids + ')))) AND sex = "' + admirer_gender + '"'
        fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,crush.access_token))
        fql_query_results = json.load(fql_query_results)['data'] 
        return fql_query_results
    
    def get_active_friends_id_array(self,crush,admirer_gender,exclude_facebook_id_array):
        friend_array = self.get_all_friends_data_array(crush,admirer_gender,exclude_facebook_id_array)
        # filter fql_query_results
        active_friend_array=[]
        for friend in friend_array:
            friend_username=friend['uid']
            try:    
                site_user = FacebookUser.objects.get(username=friend_username)
                if site_user.is_active:
                    active_friend_array.append(site_user)
            except FacebookUser.DoesNotExist:
                pass
        return active_friend_array
    
    # build a comma delimited list of usernames that should not be fetched from facebook
    # list consists of all crushes, all platonic friends, all undecided lineup members (decided lineup members fall into previous lists)
    def get_exclude_id_array(self,relationship):
        exclude_facebook_id_array=[]
        if relationship.friendship_type == 0:
            builder_user = relationship.target_person # crush is building lineup from his friend list
            builder_crushes= builder_user.crush_targets.all()
            builder_just_friends = builder_user.just_friends_targets.all()
            builder_incomplete_admirer_rels = CrushRelationship.objects.progressing_admirers(builder_user)
        else:
            builder_user = relationship.source_person # admirer is building lineup from his friend list
            builder_crushes= relationship.target_person.crush_targets.all()
            builder_just_friends = relationship.target_person.just_friends_targets.all()
            builder_incomplete_admirer_rels = CrushRelationship.objects.progressing_admirers(relationship.target_person)
        # loop through all their just_friends_targets and all their crush_targets and add their ids to a fql friendlist list
        for crush in builder_crushes:
            exclude_facebook_id_array.append(crush.username)
        for just_friend in builder_just_friends:
            exclude_facebook_id_array.append(just_friend.username)
        for rel in builder_incomplete_admirer_rels:
            builder_undecided_lineup_members = rel.lineupmember_set.filter(decision=None)    
        for member in builder_undecided_lineup_members:
            exclude_facebook_id_array.append(member.username)
        # list all friends usernames who do not have a family relationship with me and are of a certain gender limited to top 9 results
        if relationship.friendship_type != 1: 
            exclude_facebook_id_array.append(relationship.source_person.username)
        return exclude_facebook_id_array
    
    def comma_delimit_list(self,array):
        myString = ",".join(array)
        return myString

    def extract_friends_from_curl(self,fetched_raw_data): 
        extracted_list =  re.findall( 'user.php\?id=(.*?)\\\\">',fetched_raw_data,re.MULTILINE )
        # remove duplicates in extracted_list
        extracted_list = list(set(extracted_list))
        return extracted_list


    # call fb-browser-ajax-url and scrape friends and return as an array
    def get_scraped_friends_friendlist(self,current_user,friend_username,admirer_gender,exclude_facebook_id_array,number_friends_needed=settings.MINIMUM_LINEUP_MEMBERS):
        # fof_array=['1090','1020','1050','1023','1033','1024','1025','1030','1035']
        fof_id_array=[]
        friend_array=[]
        fetch_offset=0

        
        while True:
            fetch_url = "https://www.facebook.com/ajax/browser/list/allfriends/?__a=1&start=" + str(fetch_offset) + "&uid=" + str(friend_username)
            storage = StringIO()
            c = pycurl.Curl()
            c.setopt(pycurl.SSL_VERIFYPEER, 0)
            c.setopt(pycurl.SSL_VERIFYHOST, 0)
            c.setopt(c.URL, fetch_url)
            c.setopt(c.WRITEFUNCTION, storage.write)
            c.perform()
            c.close()
            fetched_raw_data=storage.getvalue() 
            friend_array=self.extract_friends_from_curl(fetched_raw_data)
            number_results = len(friend_array)
            if number_results == 0:
                
                return fof_id_array # curl has stopped returning results, either cause we've exhausted friend list or curl mechanism failed
                
            shuffle(friend_array)
            for friend in friend_array:
                if friend in exclude_facebook_id_array or friend in fof_id_array: # make sure that they are not on the exclude list
                    continue
                # see if they pass the lineup member requirements (just gender for now)
                fb_profile = urllib.urlopen('https://graph.facebook.com/' + str(friend) + '/?access_token=%s' % current_user.access_token)
                fb_profile = json.load(fb_profile)
                if fb_profile['gender'] == admirer_gender:
                    fof_id_array.append(friend)
                    if len(fof_id_array)==number_friends_needed:
                        return fof_id_array
            # if we've got to this point, then the fof_array has not been filled to expectation yet, and the previous curl function worked, so try it again with different offset
            fetch_offset=fetch_offset + number_results # 20 is the number of results retrieved by each curl facebook fetch
        return fof_id_array
    
        # call fb-browser-ajax-url and scrape friends and return as an array
    def get_api_friends_friendlist(self,friend_username,admirer_gender,exclude_facebook_id_array,number_friends_needed=settings.MINIMUM_LINEUP_MEMBERS):
        # fof_array=['1090','1020','1050','1023','1033','1024','1025','1030','1035']
        # check to see if there is an active site user with username=friend_username, if there is, filter his friend list, else just return empty array
        fof_id_array=[]
        friend_data_array=[]
        try:
            user=FacebookUser.objects.get(username=friend_username)
            if not user.is_active:
                return fof_id_array # we can't use graph api on any user that is not a active site user
            friend_data_array = self.get_all_friends_data_array(user,admirer_gender,exclude_facebook_id_array)
            shuffle(friend_data_array)
            for friend in friend_data_array:
                fof_id_array.append(friend['uid'])
                if len(fof_id_array)==number_friends_needed:
                        return fof_id_array
        except FacebookUser.DoesNotExist:
            return fof_id_array  # we can't use graph api on any user that is not a active site user
        return fof_id_array

    # the most complicated lineup initialization scenario:
    def get_acceptable_friendofriend_id_list(self,relationship,exclude_facebook_id_array):

        crush=relationship.target_person
        admirer=relationship.source_person
        admirer_gender= u'male' if admirer.gender == u'M'  else u'female'
        # PRE_STEP: get id's of all mutual friends
        mutual_friend_data = urllib.urlopen('https://graph.facebook.com/' + admirer.username + '/mutualfriends/' + crush.username + '/?access_token=%s' % crush.access_token)
        mutual_friend_data = json.load(mutual_friend_data)
        mutual_friend_data = mutual_friend_data['data']
        if len(mutual_friend_data) == 0:
            return
        fof_id_array=[]
        # STEP 1 (graph api): get ids of 9 friends from any mutual friends
        
        for mfriend in mutual_friend_data:
            mfriend_username=mfriend['id']
            fof_id_array = fof_id_array + self.get_api_friends_friendlist(mfriend_username,admirer_gender,exclude_facebook_id_array,int(9-len(fof_id_array)))
            if len(fof_id_array) > 8:
                return fof_id_array
            # repeat for another mutual friend if previous mutual friend did not generate enough id's
        
        # NEED TO TEST THIS CASE!    
        # STEP 2 (graph api), if necessary: get 9 (or remaining) ids of friends-of-friends from friends of admirers who are also active users
            # STEP 2a: grab all admirer friends and filter through the active users
        active_crush_friend_array = self.get_active_friends_id_array(crush,admirer_gender,[]) # don't send any exclude ids cause we want all friends regardless of sex
        shuffle(active_crush_friend_array) # shuffle the list so we don't always go after same friends of friends (don't make it too obvious)
        # STEP 2b: grab friends of those active friend users
        
        #update the excluded friend ids with the just-created lineup ids 
        exclude_facebook_id_array = exclude_facebook_id_array + fof_id_array
        for crush_friend in active_crush_friend_array:
            if crush_friend in mutual_friend_data:
                # make sure we haven't already processed this friend above
                continue
            fof_id_array = fof_id_array + self.get_api_friends_friendlist(crush_friend.username,admirer_gender,exclude_facebook_id_array,1) # note that we only get one friend of friend
            if len(fof_id_array) > 8:
                return fof_id_array
            
        # STEP 3 (cURL scrape), if necessary: go back and get ids of 9 friends from any mutual friends (who are not an active user processed earlier)
        
        #update the excluded friend ids with the just-created lineup ids 
        exclude_facebook_id_array = exclude_facebook_id_array + fof_id_array
        for mfriend in mutual_friend_data:
            
            # step 1: use curl scraping to get ids of 9 friends from one mutual friend (who is not an active user processed earlier)
            mfriend_username=mfriend['id']
            fof_id_array = fof_id_array + self.get_scraped_friends_friendlist(crush,mfriend_username,admirer_gender,exclude_facebook_id_array,int(9-len(fof_id_array)))
            if len(fof_id_array) > 8:
                return fof_id_array
        # STEP 4 (cURL scrape): if necessary, go back and grab 1 friend-of-friend from 9 (or remaining) random friends of crush 
        
        #update the excluded friend ids with the just-created lineup ids 
        exclude_facebook_id_array = exclude_facebook_id_array + fof_id_array
        
        crush_friend_array = self.get_all_friends(crush)
        shuffle(crush_friend_array) # shuffle the list so we don't always go after same friends of friends (don't make it too obvious)
        # STEP 4b: grab friends of those friend users
        for crush_friend in crush_friend_array:
            if crush_friend in mutual_friend_data or crush_friend in active_crush_friend_array:
                # make sure we haven't already processed this friend above
                continue
            fof_id_array = fof_id_array + self.get_scraped_friends_friendlist(crush,crush_friend.username,exclude_facebook_id_array,admirer_gender,1)
            if len(fof_id_array) > 8:
                return fof_id_array
        # if steps 1,2,3,4 all fail, then do nothing, and later, a catch-all task will try to accomplish the task through a scraper or manual means
        return fof_id_array # return what was created (if anything)
    
    def get_acceptable_friend_id_list(self,relationship,exclude_facebook_id_array):
        admirer_gender= u'male' if relationship.source_person.gender == u'M'  else u'female'
        exclude_facebook_ids=self.comma_delimit_list(exclude_facebook_id_array)
        friend_id_array=[]
        try:
            if relationship.friendship_type == 0: # the crush can build the lineup from his/her friend list  
                fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (SELECT uid FROM family where profile_id=me())) AND NOT (uid2 IN (" + exclude_facebook_ids + "))) ) AND sex = '" + admirer_gender + "'  ORDER BY friend_count DESC LIMIT 9"
                fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,relationship.target_person.access_token))
                data = json.load(fql_query_results)['data'] 
            elif relationship.friendship_type == 2: # the admirer must build the lineup from his friend list
                fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (" + exclude_facebook_ids + ")) )) AND sex = '" + admirer_gender + "'  ORDER BY friend_count DESC LIMIT 9"
                fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,relationship.source_person.access_token))
                data = json.load(fql_query_results)['data'] 
        except ValueError:
            print "ValueError on Fql Query Fetch read!"
            relationship.lineup_initialization_status=4
            relationship.save(update_fields=['lineup_initialization_status'])
            return 
        except KeyError:
            print "KeyError on FQL Query Fetch read"
            relationship.lineup_initialization_status=4
            relationship.save(update_fields=['lineup_initialization_status'])
            return
        for item in data:
            friend_id_array.append(item['uid'])
        return friend_id_array

    
    # returns true if successful, false otherwise
    def initialize_lineup(self,relationship):
        print "initializing relationship for admirer: " + relationship.source_person.first_name + " " + relationship.source_person.last_name

        exclude_facebook_id_array=self.get_exclude_id_array(relationship)
        if relationship.friendship_type==1:
            acceptable_id_array=self.get_acceptable_friendofriend_id_list(relationship,exclude_facebook_id_array)
        else:
            acceptable_id_array=self.get_acceptable_friend_id_list(relationship,exclude_facebook_id_array)
        
        if len(acceptable_id_array) < settings.MINIMUM_LINEUP_MEMBERS:
            if relationship.friendship_type == 0:
                relationship.lineup_initialization_status=3
            else:
                relationship.lineup_initialization_status=2
            relationship.save(update_fields=['lineup_initialization_status'])
            return      
        print "json data results for admirer: " + relationship.source_person.first_name + " " + relationship.source_person.last_name + " : " + str(acceptable_id_array)
        # determine where the admirer should randomly fall into the lineup
        # don't ever put member in last spot, cause there's a chance crush will skip making decision at end
        random_end = len(acceptable_id_array) - 1
        admirer_position=random.randint(0, random_end) # normally len(data) should be 9
        index = 0
        for lineup_id in acceptable_id_array:
            print "iteration execution"
            # if the current lineup position is where the admirer should go, then insert the admirer
            if index==admirer_position:
                LineupMember.objects.create(position=index,username = relationship.source_person.username,relationship=relationship,decision=None)
                print "put crush in position: " + str(index) 
                index = index + 1            
            LineupMember.objects.create(position=index,username=lineup_id,relationship=relationship,decision=None)
            index = index + 1
        # the following condition (to put admirer in last position) should not occur, but just in case let's handle it    
        if len(acceptable_id_array)==admirer_position:
            LineupMember.objects.create(position=len(acceptable_id_array),username=relationship.source_person.username,relationship=relationship,decision=None)
      
        print "number lineup members: " + str(relationship.lineupmember_set.count())

        relationship.lineup_initialization_status=1
        relationship.save(update_fields=['lineup_initialization_status'])
        
        return True

# details about each crush's secret admirer lineup (SAL)
class LineupMember(models.Model):
    
    class Meta:
        # this allows the models to be broken into separate model files
        app_label = 'crush'
        
    objects = LineupMemberManager()   
        
    # each lineup has many lineup members (10 by default) and each lineup member has only one lineup it belongs to (similar to blog entry)
    relationship = models.ForeignKey('CrushRelationship')
    user=models.ForeignKey('FacebookUser', null=True,blank=True,default=None)
    username = models.CharField(max_length=60) 
    position = models.IntegerField() # example x.y where x is id of lineup and y is position in lineup (0 through 9)
    

    DECISION_CHOICES = ( # platonic levels represent crush's rating of member's attractiveness
                           (0,'Crush'),
                           (1,'Platonic 1'),
                           (2,'Platonic 2'),
                           (3,'Platonic 3'),
                           (4,'Platonic 4'),
                           (5,'Platonic 5'),
                           )
    decision = models.IntegerField(null=True, choices=DECISION_CHOICES, default=None)
    comment = models.CharField(null=True,default=None,max_length=200)