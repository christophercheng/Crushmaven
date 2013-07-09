from django.db import models
import urllib, json
from django.conf import settings
from  crush.models.relationship_models import CrushRelationship
import random
import re,thread,time
from threading import Lock
from crush.models.globals import g_init_dict
from crush.utils import graph_api_fetch,fb_fetch

def comma_delimit_list(array):
    myString = ",".join(array)
    return myString

class LineupMemberManager(models.Manager):
    class Meta:
    # this allows the models to be broken into separate model files
        app_label = 'crush'

    # returns true if successful, false otherwise
    def initialize_lineup(self,relationship):
        global g_init_dict
        print "Initializing relationship for admirer: " + relationship.source_person.first_name + " " + relationship.source_person.last_name
        
        crush_id=relationship.target_person.username

        if 'exclude_id_string' not in g_init_dict[crush_id]:
            g_init_dict[crush_id]['exclude_id_string'] = comma_delimit_list(LineupMember.objects.get_exclude_id_array(relationship))
        rel_id=str(relationship.id)
        g_init_dict[crush_id][rel_id + '_initialization_state']=0
        
        if relationship.friendship_type==0:
            self.initialize_friend_crush(relationship)
        elif relationship.friendship_type==1:
            self.initialize_friend_of_friend_crush(relationship)      
        else:
            self.initialize_nonfriend_crush(relationship)

    #================================================================    
    #  FRIENDSHIP TYPE 0: FRIEND INITIALIZATION 
    #  build lineup from friends of the crush (target)
    # ================================================================

    def initialize_friend_crush(self,relationship):
        global g_init_dict
        rel_id=str(relationship.id)
        crush_id=relationship.target_person.username
        
        print "REL ID: " + rel_id + " Initialize friend crush"
        admirer_gender= u'male' if relationship.source_person.gender == u'M'  else u'female'
        acceptable_id_array=[]
        
        try:
            # prevent any other friend crush relationships from processing at same time with this 'crush' lock
            if crush_id not in g_init_dict[crush_id]:
                g_init_dict[crush_id][crush_id] = Lock()
            g_init_dict[crush_id][crush_id].acquire() 
            #print "REL ID: " + rel_id + " inside lock"
            
                        # get up to 3 admirers from most recent friends added in the last 250 posts)
            fb_query_string = "SELECT description, description_tags, created_time FROM stream WHERE source_id = me()  AND type = 8 LIMIT 100"
            friend_posts = graph_api_fetch(relationship.target_person.access_token,fb_query_string,True,True)
            new_friend_array=[]
            for feed in friend_posts:
                group_post = feed['description_tags']
                for key in group_post.keys():
                    if key != '0':
                        new_friend_array.append(str(group_post[key][0]['id']))
            if len(new_friend_array) > 0:
                random.shuffle(new_friend_array)
                # filter id's of users with same gender as admirer   
                query_string = "SELECT uid FROM user WHERE uid IN ("
                query_string += ",".join(new_friend_array)
                query_string += ") AND NOT (uid IN ('" + g_init_dict[crush_id]['exclude_id_string'] + "') ) AND sex='" + admirer_gender + "' LIMIT 3"
        
                new_friend_array = graph_api_fetch('',query_string,expect_data=True,fql_query=True)
                for new_friend in new_friend_array:
                    id = str(new_friend[u'uid'])
                    acceptable_id_array.append(id)
                    g_init_dict[crush_id]['exclude_id_string'] += "," + id
        except Exception as e:
            print str(e)
            pass # we're still good, just won't have any recent friends i list
        try:
            num_members_needed = 9 - len(acceptable_id_array) 
            fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (SELECT uid FROM family where profile_id=me())) AND NOT (uid2 IN (" + g_init_dict[crush_id]['exclude_id_string'] + "))) ) AND sex = '" + admirer_gender + "'  ORDER BY friend_count DESC LIMIT " + str(num_members_needed)
            data = graph_api_fetch(relationship.target_person.access_token,fql_query,expect_data=True,fql_query=True)

        except Exception as e:
            g_init_dict[crush_id][crush_id].release()
            print "Friend Crush FQL Exception: " + str(e)
            self.initialize_fail(relationship,5)
            return
        if not data or len(data) < settings.MINIMUM_LINEUP_MEMBERS:
            g_init_dict[crush_id][crush_id].release()
            self.initialize_fail(relationship,3)
            return
        
        for item in data:
            g_init_dict[crush_id]['exclude_id_string'] += "," + str(item['uid'])
            acceptable_id_array.append(item['uid'])
            
        random.shuffle(acceptable_id_array)
        
        print "REL ID: " + rel_id + " lineup results: " + str(acceptable_id_array)
        g_init_dict[crush_id][crush_id].release()     
        self.create_lineup(relationship,acceptable_id_array)
        
    #================================================================    
    # FRIENDSHIP TYPE 2: NON-FRIEND INITIALIZATION 
    # build lineup from friends of the admirer (source)
    # very similar to FRIEND INITIALIZATION except the lineup is built from the admirer's friend list instead of crush's
    # ================================================================

    def initialize_nonfriend_crush(self,relationship):
        global g_init_dict
        print "Initialize non friend crush"
        admirer_id=relationship.source_person.username
        crush_id=relationship.target_person.username
        admirer_gender= u'male' if relationship.source_person.gender == u'M'  else u'female'
        acceptable_id_array=[]
        
        try:
            fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = " + admirer_id + " AND NOT (uid2 IN (" + g_init_dict[crush_id]['exclude_id_string'] + ")) )) AND sex = '" + admirer_gender + "'  ORDER BY friend_count DESC LIMIT 9"
            data = graph_api_fetch(relationship.source_person.access_token,fql_query,expect_data=True,fql_query=True)
        except:
            print "Key or Value Error on Fql Query Fetch read!"
            self.initialize_fail(relationship,5)
            return
        
        if not data or len(data) < settings.MINIMUM_LINEUP_MEMBERS:
            print "NON FRIEND - not enough friends"
            self.initialize_fail(relationship,2)
            return
        
        for item in data:
            g_init_dict[crush_id]['exclude_id_string'] += "," + str(item['uid'])
            acceptable_id_array.append(item['uid'])

        print "json data results for admirer: " + relationship.source_person.first_name + " " + relationship.source_person.last_name + " : " + str(acceptable_id_array)
        self.create_lineup(relationship,acceptable_id_array)

    #================================================================    
    # FRIENDSHIP TYPE 1: FRIEND-OF-FRIEND INITIALIZATION 
    # build lineup of other friends-of-friends
    # can be implemented by one of 4 methods (api mutual friend, api 9-fof's, non-api mutual friend, non-api 9-fof's)
    # ================================================================

    def initialize_friend_of_friend_crush(self,relationship):
        global g_init_dict
        crush_id=relationship.target_person.username
        rel_id=str(relationship.id)
        exclude_id_string=g_init_dict[crush_id]['exclude_id_string']
        
        # set up the batch fql queries
        crush_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM+user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1=' + crush_id + ' AND NOT (uid2 IN (' + exclude_id_string + ')))"}'
        crush_app_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1=' + crush_id + ' AND NOT (uid2 IN (' + exclude_id_string + '))) AND is_app_user"}'
        mutual_friend_id_dict='{"method":"GET","name":"mutual-friends","relative_url":"' + crush_id +'/mutualfriends/' + relationship.source_person.username + '"}'
        mutual_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM user WHERE uid IN ({result=mutual-friends:$.data.*.id}) AND NOT (uid IN (' + exclude_id_string + '))"}'
        mutual_app_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM user WHERE uid IN ({result=mutual-friends:$.data.*.id}) AND NOT (uid IN (' + exclude_id_string + ')) AND is_app_user"}'
        
        # set up the post data
        post_dict = {}
        post_dict['access_token'] = relationship.target_person.access_token
        post_dict['batch'] = '[' + mutual_friend_id_dict + ',' + mutual_friend_dict + ',' + mutual_app_friend_dict + ',' + crush_friend_dict + ',' + crush_app_friend_dict  + ']'
        post_dict=urllib.urlencode(post_dict)    
        
        # run the actual fql batch query, try it a second time if it fails
        url='https://graph.facebook.com'
        mutual_app_friend_array=[]
        num_fetch_tries=0 # try to grab data from facebook two times if necessary. sometimes it does not return data       
        while (num_fetch_tries < 2):    
            fb_result = urllib.urlopen(url,post_dict)
            fb_result = json.load(fb_result)
        
            if len(fb_result)>4 and 'body' in fb_result[2] and 'data' in fb_result[2][u'body']:
                mutual_app_friend_array=json.loads(fb_result[2][u'body'])['data']
                random.shuffle(mutual_app_friend_array)
                break # get out of while loop - we've done our job here, move on
            time.sleep(.5)
            num_fetch_tries+=1
        
        # METHOD 1: API MUTUAL APP FRIEND
        if len(mutual_app_friend_array)>0:
            acceptable_id_array = self.try_api_mf_initialization(relationship,mutual_app_friend_array)
            if len(acceptable_id_array)>settings.MINIMUM_LINEUP_MEMBERS:
                self.create_lineup(relationship, acceptable_id_array)
                return
        
        # METHOD 2: API 9 Friends from 9 Crush App Friends     
        if 'body' in fb_result[4] and 'data' in fb_result[4][u'body']:
            crush_app_friend_array=json.loads(fb_result[4][u'body'])['data']
            if len(crush_app_friend_array) >= settings.MINIMUM_LINEUP_MEMBERS:
                random.shuffle(crush_app_friend_array)
                acceptable_id_array = self.try_api_cf_initialization(relationship,crush_app_friend_array)
                if len(acceptable_id_array)>settings.MINIMUM_LINEUP_MEMBERS:
                    self.create_lineup(relationship,acceptable_id_array)   
                    return
        
        # METHOD 3 & 4: NON-API MUTUAL FRIEND / NON-API 9 Friends from 9 Crush Friends
        if 'body' in fb_result[1] and 'data' in fb_result[1][u'body']:
            mutual_friend_array=json.loads(fb_result[1][u'body'])['data']
            #print "mutual_friend_array: " + str(len(mutual_friend_array)) + " : " + str(mutual_friend_array)
            # random.shuffle(mutual_friend_array) delay shuffling
            g_init_dict[crush_id][rel_id + '_mutual_friend_array']=mutual_friend_array
            if 'body' in fb_result[3] and 'data' in fb_result[3][u'body']:
                crush_friend_array=json.loads(fb_result[3][u'body'])['data']
                #random.shuffle(crush_friend_array) delay shuffling cause we may not need this yet
                g_init_dict[crush_id]['crush_friend_array']=crush_friend_array
                self.try_nonapi_mf_initialization(relationship)
                return

        # if got here then we failed cause of bad facebook data fetch, so allow user to start it up again
        self.initialize_fail(relationship,5)

    #================================================================    
    # METHOD 1 ( FOF Initialization, Graph API) 
    # try to build an array with 9 friends from a single mutual friend
    # ================================================================

    def try_api_mf_initialization(self,relationship,mutual_app_friend_array):
        global g_init_dict
        crush_id=relationship.target_person.username
        for mutual_friend in mutual_app_friend_array:
            if mutual_friend['friend_count'] <settings.MINIMUM_LINEUP_MEMBERS:
                continue
            mfriend_id=str(mutual_friend['uid'])
            if mfriend_id not in g_init_dict[crush_id]: 
                g_init_dict[crush_id][mfriend_id]= Lock()
            g_init_dict[crush_id][mfriend_id].acquire() 
            # grab all friends of mutual app with admirer sex, friend sorted by friend count - via graph api
            fql_query = 'SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1=' + str(mutual_friend['uid']) + ' AND NOT (uid2 IN (' + g_init_dict[crush_id]['exclude_id_string'] + ')))) AND sex = "' + relationship.source_person.get_fb_gender() + '" ORDER BY friend_count DESC LIMIT ' + str(settings.IDEAL_LINEUP_MEMBERS)
            try:
                fql_query_results = graph_api_fetch(relationship.target_person.access_token,fql_query,expect_data=True,fql_query=True)
            except:
                g_init_dict[crush_id][mfriend_id].release()
                continue
            # if less than minimum lineup members, go on to next mutual friend
            if not fql_query_results or len(fql_query_results) < settings.MINIMUM_LINEUP_MEMBERS:
                g_init_dict[crush_id][mfriend_id].release()
                continue 
            acceptable_id_array=[]
            for result in fql_query_results:
                acceptable_id_array.append(result['uid'])
                g_init_dict[crush_id]['exclude_id_string'] += "," + str(result['uid'])
            g_init_dict[crush_id][mfriend_id].release()
            # else add to lineup id array and setup in lineup
            return acceptable_id_array
        # if for loop ended without returning, then return False cause no lineup was created
        return []

    #================================================================    
    # METHOD 2 ( FOF Initialization, Graph API) 
    # try to initialize lineup with 9 friends from 9 separate crush friends
    # ================================================================

    def try_api_cf_initialization(self,relationship,crush_app_friend_array):
        global g_init_dict
        crush_id=relationship.target_person.username
        exclude_id_string=g_init_dict[crush_id]['exclude_id_string']
        acceptable_id_array=[]
        # iterate through all crush app friends
        for friend in crush_app_friend_array:
            # get each crush app friend's friends sorted by friend_count and filtered by gender & exclude id list - limit result to 1
            fql_query = 'SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1=' + str(friend['uid']) + ' AND NOT (uid2 IN (' + exclude_id_string + ')))) AND sex = "' + relationship.source_person.get_fb_gender() + '" ORDER BY friend_count DESC LIMIT 1'
            try:
                fql_query_results = graph_api_fetch(relationship.target_person.access_token,fql_query,expect_data=True,fql_query=True)
            except:
                continue
            # if result < 0 skip rest of loop
            if len(fql_query_results) == 0:
                continue
            # else grab the result and add to acceptable id_array
            acceptable_id_array.append(fql_query_results[0]['uid'])
            exclude_id_string = exclude_id_string + ',' + str(fql_query_results[0]['uid'])
            # if acceptable id_array length == ideal lineup members then break out of loop entirely
            if len(acceptable_id_array) >= settings.IDEAL_LINEUP_MEMBERS:
                break
        # after loop, count the acceptable id_array_length, if greater than minimum lineup member setting, then call create_lineup
        if len(acceptable_id_array) >= settings.MINIMUM_LINEUP_MEMBERS:
            for accepted_id in acceptable_id_array:
                g_init_dict[crush_id]['exclude_id_string'] += "," + str(accepted_id)
            return acceptable_id_array
        else:
            return []

    #================================================================    
    # METHOD 3 ( FOF Initialization, NON API) 
    # try to build an array with 9 friends from a single mutual friend
    # ================================================================

    def try_nonapi_mf_initialization(self,relationship):
        global g_init_dict
        crush_id=relationship.target_person.username
        rel_id=str(relationship.id)
        if len(g_init_dict[crush_id][rel_id + '_mutual_friend_array']) > 0:
            # set some of the global variables
            random.shuffle(g_init_dict[crush_id][rel_id + '_mutual_friend_array'])
            self.process_mutual_friend(relationship,0)
        
        else:
            self.try_nonapi_cf_initialization(relationship)
            
    #=================================================================    
    # METHOD 3A - Process Mutual Friend
    # ================================================================       
    def process_mutual_friend(self,relationship,mf_index):
        global g_init_dict
        rel_id=str(relationship.id)
        crush_id=relationship.target_person.username
        mfriend=g_init_dict[crush_id][rel_id + '_mutual_friend_array'][mf_index]
        mfriend_id=str(mfriend['uid'])
        if mfriend_id not in g_init_dict[crush_id]: 
            g_init_dict[crush_id][mfriend_id]= Lock()
        g_init_dict[crush_id][mfriend_id].acquire()     
        g_init_dict[crush_id][rel_id + '_filtered_id_array']=[] # reset for each mutual friend processed
        print "REL ID:" + rel_id + ": Method 3A (process_mutual_friend), mutual friend:" + mfriend_id + " at mf_index: " + str(mf_index)
        num_friends = mfriend['friend_count']
        if num_friends < settings.MINIMUM_LINEUP_MEMBERS or num_friends == None:
            self.finished_process_mutual_friend(relationship,mf_index)
            return
        else:
            # build array of blocks to process (each block has up to 24 friends)
            max_q_block= (num_friends/24)+1
            q_block_array=[]
            for x in range(max_q_block):
                q_block_array.append(24*x)
            random.shuffle(q_block_array)
            # kick off process of a batch of q blocks
  
            self.process_batch_blocks(relationship,mf_index,q_block_array,0)

            return # finished processing all mutual friends and did not find enough lineup members for each
    
    #=================================================================    
    # METHOD 3B - Process Batch Blocks
    # request up to 5 blocks from facebook
    # ================================================================      

    def process_batch_blocks(self,relationship,mf_index,q_block_array,q_start_index):
        global g_init_dict
        rel_id=str(relationship.id)
        crush_id=relationship.target_person.username
        # reset batch_blocks received and requested before we kickoff a new batch
        g_init_dict[crush_id][rel_id + '_batch_blocks_received']=0
        g_init_dict[crush_id][rel_id + '_batch_id_array']=[]
        print "REL ID: " + rel_id + " Method 3B (process_batch_blocks), mutual friend: " + str(g_init_dict[crush_id][rel_id + '_mutual_friend_array'][mf_index]['uid']) + ", q_start_index: " + str(q_start_index)
        last_fetch_index=q_start_index+5
        if last_fetch_index>len(q_block_array):
            last_fetch_index = len(q_block_array)
        g_init_dict[crush_id][rel_id + '_batch_blocks_requested']=last_fetch_index - q_start_index
        for x in range(q_start_index,last_fetch_index):
            thread.start_new_thread(self.fetch_block,(relationship,mf_index,q_block_array,q_start_index,x)) #initialize lineup asynchronously            
            #self.fetch_block(rel_id,mf_index,q_block_array,q_start_index,x)

    #=================================================================    
    # METHOD 3C - Fetch Single Block
    # ================================================================   

    def fetch_block(self,relationship,mf_index,q_block_array,q_start_index,q_index):
        global g_init_dict
        crush_id=relationship.target_person.username
        rel_id=str(relationship.id)
        try:
            fetch_response = fb_fetch(g_init_dict[crush_id][rel_id+'_mutual_friend_array'][mf_index]['uid'],q_block_array[q_index])
        except:
            LineupMember.objects.fetch_block_finished(relationship,mf_index,q_block_array,q_start_index, [])
            return
        extracted_id_list =  re.findall( 'user.php\?id=(.*?)\\\\">',fetch_response,re.MULTILINE )
        # remove duplicates in extracted_list
        extracted_id_list = list(set(extracted_id_list))
        print "REL ID:" + rel_id + " Method 3C (fetch_block), mutual friend: " + str((g_init_dict[crush_id][rel_id+'_mutual_friend_array'])[mf_index]['uid'])  + ", q block: " + str(q_block_array[q_index]) + ", num extracted items: " + str(len(extracted_id_list))     
        LineupMember.objects.fetch_block_finished(relationship,mf_index,q_block_array,q_start_index,extracted_id_list)
        
    #=================================================================    
    # METHOD 3D - Fetch Block Finished
    # fetch blocks check-in here, if all requested blocks have been check-in, then begin filtering of all fetch results
    # ================================================================  

    def fetch_block_finished(self,relationship,mf_index,q_block_array,q_start_index,extracted_id_list):
        global g_init_dict
        crush_id=relationship.target_person.username
        rel_id=str(relationship.id)
        g_init_dict[crush_id][rel_id+'_batch_id_array']+=extracted_id_list
        g_init_dict[crush_id][rel_id+'_batch_blocks_received']  += 1 # TODO replace this with F function to prevent race function

        if g_init_dict[crush_id][rel_id+'_batch_blocks_received'] < g_init_dict[crush_id][rel_id+'_batch_blocks_requested']:
            return

        if len(g_init_dict[crush_id][rel_id+'_batch_id_array'])==0:
            # this mutual friend probably has a privatized friend list
            self.finished_process_mutual_friend(relationship,mf_index)
            return
        # all fetches have completed
        # filter batch id_array with gender   
        query_string = "SELECT uid FROM user WHERE uid IN ("
        query_string += ",".join(g_init_dict[crush_id][rel_id+'_batch_id_array'])
        query_string += ") AND NOT (uid IN (" + g_init_dict[crush_id]['exclude_id_string'] + ")) AND sex='" + relationship.source_person.get_fb_gender() + "'"
        try:
            filtered_batch_id_array = graph_api_fetch('',query_string,expect_data=True,fql_query=True)
        except:
            filtered_batch_id_array=[]
        print "REL ID:" + rel_id +" Method 3D (fetch_block_finished), mutual friend: " + str(g_init_dict[crush_id][rel_id+'_mutual_friend_array'][mf_index]['uid']) + " - finished batch at q_start_index " + str(q_start_index) + " . Number filtered results: " + str(len(filtered_batch_id_array))
        g_init_dict[crush_id][rel_id+'_filtered_id_array'] += filtered_batch_id_array
        if len(g_init_dict[crush_id][rel_id+'_filtered_id_array']) >= settings.IDEAL_LINEUP_MEMBERS:
            acceptable_id_array=[]
            for item in g_init_dict[crush_id][rel_id+'_filtered_id_array']:
                g_init_dict[crush_id]['exclude_id_string'] += "," + str(item['uid'])
                acceptable_id_array.append(item['uid'])
                if len(acceptable_id_array) >= settings.IDEAL_LINEUP_MEMBERS:
                    break
            #sort array
            acceptable_id_array.sort(key=int)
            g_init_dict[crush_id][str((g_init_dict[crush_id][rel_id+'_mutual_friend_array'])[mf_index]['uid'])].release()    
            self.create_lineup(relationship,acceptable_id_array[:int(settings.IDEAL_LINEUP_MEMBERS)])
            return
        else:
            next_q_index = q_start_index + g_init_dict[crush_id][rel_id+'_batch_blocks_received']
            if next_q_index >= len(q_block_array):
                # done processing this mutual friend
                if len(g_init_dict[crush_id][rel_id+'_filtered_id_array']) >= settings.MINIMUM_LINEUP_MEMBERS:
                    # acceptable results from this mutual friend
                    acceptable_id_array=[]
                    for item in g_init_dict[crush_id][rel_id+'_filtered_id_array']:
                        g_init_dict[crush_id]['exclude_id_string'] += "," + str(item['uid']) 
                        acceptable_id_array.append(item['uid'])
                    #sort array
                    acceptable_id_array.sort(key=int)
                    # return whole array cause we know it is > minimum and < ideal
                    g_init_dict[crush_id][str((g_init_dict[crush_id][rel_id+'_mutual_friend_array'])[mf_index]['uid'])].release()
                    self.create_lineup(relationship,acceptable_id_array)
                    return
                else:
                    # no results to show for. try for next one
                    self.finished_process_mutual_friend(relationship,mf_index)
                    return
            else: # process the next batch of q blocks
                self.process_batch_blocks(relationship,mf_index,q_block_array,next_q_index)
                return
    #=================================================================    
    # METHOD 3E - FINISHED processing mutual friend
    # determine what to do next
    # ================================================================  

    def finished_process_mutual_friend(self,relationship,mf_index):
        global g_init_dict
        rel_id=str(relationship.id)
        crush_id=relationship.target_person.username
        # try to process next mutual friend
        g_init_dict[crush_id][str((g_init_dict[crush_id][rel_id+'_mutual_friend_array'])[mf_index]['uid'])].release()
        next_mf_index = mf_index + 1
        if next_mf_index < len(g_init_dict[crush_id][rel_id+'_mutual_friend_array']):
            self.process_mutual_friend(relationship,next_mf_index)
        else:
            self.try_nonapi_cf_initialization(relationship)
        # if no more mutual friends, then we'll have to switch to next lineup initialization process
 
    #================================================================    
    # METHOD 4 ( FOF Initialization, NON API) 
    # # try to build an array with 9 friends from a 9 separate friend of crush 
    # ================================================================        

    def try_nonapi_cf_initialization(self,relationship):
        global g_init_dict
        rel_id=str(relationship.id)
        crush_id=relationship.target_person.username
        
        print "TRY METHOD 4"
        if len(g_init_dict[crush_id]['crush_friend_array']) < settings.MINIMUM_LINEUP_MEMBERS:
            self.initialize_fail(relationship,2)
            return
        else:
            g_init_dict[crush_id][rel_id+'_initialization_state']=0
            g_init_dict[crush_id][rel_id+'_filtered_id_array']=[]#scrap results to date
            random.shuffle(g_init_dict[crush_id]['crush_friend_array'])
            self.batch_fetch_friends(relationship,0)
    
    #================================================================    
    # METHOD 4a - Subroutine A: Batch Fetch Handler - iteratively fetch 20 friends at given index
    # ================================================================
    def batch_fetch_friends(self,relationship,cf_index):
        global g_init_dict
        rel_id=str(relationship.id)
        crush_id=relationship.target_person.username
        
        g_init_dict[crush_id][rel_id+'_batch_start_cf_index']=cf_index
        print "Starting batch fetch at index: " + str(cf_index)
        next_cf_index = cf_index + 18
        if next_cf_index > len(g_init_dict[crush_id]['crush_friend_array']):
            next_cf_index = len(g_init_dict[crush_id]['crush_friend_array'])
        g_init_dict[crush_id][rel_id+'_batch_friends_requested']= next_cf_index-cf_index # use this variable to determine if all requests have been retrieved and we can process final results
        g_init_dict[crush_id][rel_id+'_batch_friends_received'] = 0
        for x in range(cf_index,next_cf_index): # /iterate through next 18 friends
            # call a single person handler 
            thread.start_new_thread(self.start_single_friend_fetch,(relationship,x)) #initialize lineup asynchronously            
            #self.start_single_friend_fetch(rel_id,x)     

    # ================================================================    
    # METHOD 4b - Subroutine B: Single Person Fetch Handler - build q block array and fire off processing for each block
    # ================================================================
    def start_single_friend_fetch(self,relationship,cf_index):
        global g_init_dict
        crush_id=relationship.target_person.username
        
        # calculate max q block by finding total friend count
        number_friends=g_init_dict[crush_id]['crush_friend_array'][cf_index]['friend_count']
        if number_friends==None or number_friends < 5:
            # skip this friend so continue on to next function and pass on variables
            self.finished_processing_friend(relationship,cf_index)
            return
        
        max_q_block = (number_friends/24) + 1
        # build array of blocks to process
        q_block_array=[]
        for x in range(max_q_block):
            q_block_array.append(x*24)
        # randomize the array                         
        random.shuffle(q_block_array)
        # kick of processing of a batch of q blocks
        self.process_friend_block(relationship,cf_index,q_block_array,0)
    
    # ================================================================    
    # METHOD 4c - Subroutine C: Single BLOCK Fetch Handler 
    # ================================================================
    def process_friend_block(self,relationship,cf_index,q_block_array,q_index):
        global g_init_dict
        rel_id=str(relationship.id)
        crush_id=relationship.target_person.username
        
        if not crush_id in g_init_dict or g_init_dict[crush_id][rel_id+'_initialization_state']>0: 
            # other threads have already completed the job
            return
        crush_friend=g_init_dict[crush_id]['crush_friend_array'][cf_index]

        try:
            fetch_response = fb_fetch(crush_friend['uid'],q_block_array[q_index])
        except:
            self.get_another_friend_block(relationship,cf_index,q_block_array,q_index)
            return

        extracted_id_list =  re.findall( 'user.php\?id=(.*?)\\\\">',fetch_response,re.MULTILINE )
        # remove duplicates in extracted_list
        extracted_id_list = list(set(extracted_id_list))
        if len(extracted_id_list)>0:
            self.filter_ids_by_admirer_conditions(relationship,cf_index,q_block_array,q_index,extracted_id_list)
        else:
            #try another friend cause fetching more blocks from this friend will be worthless
            self.finished_processing_friend(relationship,cf_index)
    
    # ================================================================    
    # METHOD 4d - Subroutine D: FILTER out user id's by admirer conditions 
    # ================================================================    
    def filter_ids_by_admirer_conditions(self,relationship,cf_index,q_block_array,q_index,extracted_id_list):
        global g_init_dict
        rel_id=str(relationship.id)
        crush_id=relationship.target_person.username
        
        if not crush_id in g_init_dict or g_init_dict[crush_id][rel_id+'_initialization_state']>0: 
            # other threads have already completed the job
            return
        # filter batch id_array with gender   
        query_string = "SELECT uid FROM user WHERE uid IN ("
        query_string += ",".join(extracted_id_list)
        query_string += ") AND NOT (uid IN (" + str(g_init_dict[crush_id]['exclude_id_string']) + ")) AND sex='" + relationship.source_person.get_fb_gender() + "'"
        url = "https://graph.facebook.com/fql?q=" + query_string # don't need access token for this query             
        try:
            filtered_batch_id_array = graph_api_fetch('',query_string,expect_data=True,fql_query=True)
        except:
            self.get_another_friend_block(relationship,cf_index,q_block_array,q_index)
            return
        if len(filtered_batch_id_array)>0:
            filtered_index=random.randint(0,len(filtered_batch_id_array)-1) # select a random friend from the filtered batch, not always the first one
            g_init_dict[crush_id][rel_id+'_filtered_id_array'].append(filtered_batch_id_array[filtered_index]['uid'])    
            g_init_dict[crush_id]['exclude_id_string'] = g_init_dict[crush_id]['exclude_id_string'] + ',' + str(filtered_batch_id_array[filtered_index]['uid'])
           
            if len(g_init_dict[crush_id][rel_id+'_filtered_id_array']) >= settings.IDEAL_LINEUP_MEMBERS:
                # we have enough lineup members so call final routine // if we get more ingore the others
                self.finalize_initialization(relationship)
                return
        self.finished_processing_friend(relationship,cf_index) #report in!
        return
    
    # ================================================================    
    # METHOD 4e - Subroutine E: Go back and fetch another block - all friends were of wrong sex
    # ================================================================    
    def get_another_friend_block(self,relationship,cf_index,q_block_array,q_index):
        global g_init_dict
        rel_id=str(relationship.id)
        crush_id=relationship.target_person.username
        
        if not crush_id in g_init_dict or g_init_dict[crush_id][rel_id+'_initialization_state']>0: 
            # other threads have already completed the job
            return
        q_index = q_index + 1

        if q_index < len(q_block_array):
            self.process_friend_block(relationship,cf_index,q_block_array,q_index) 
        else:
            self.finished_processing_friend(relationship,cf_index)
    
    # ================================================================    
    # METHOD 4F - Subroutine F: Go WAY back and fetch another batch of friends 
    # ================================================================    
    def finished_processing_friend(self,relationship,cf_index):
        global g_init_dict
        rel_id=str(relationship.id)
        crush_id=relationship.target_person.username
        
        if not crush_id in g_init_dict or g_init_dict[crush_id][rel_id+'_initialization_state']>0: 
            # other threads have already completed the job
            return
        g_init_dict[crush_id][rel_id+'_batch_friends_received'] += 1
        print " - finished processing friend # " + str(g_init_dict[crush_id][rel_id+'_batch_friends_received']) + " at cf_index: " + str(cf_index) + " with number of ids: " + str(len(g_init_dict[crush_id][rel_id+'_filtered_id_array']))
        
        if g_init_dict[crush_id][rel_id+'_batch_friends_received'] == g_init_dict[crush_id][rel_id+'_batch_friends_requested']:
            if len(g_init_dict[crush_id][rel_id+'_filtered_id_array']) < settings.IDEAL_LINEUP_MEMBERS:
                cf_index = g_init_dict[crush_id][rel_id+'_batch_start_cf_index'] + g_init_dict[crush_id][rel_id+'_batch_friends_requested']
                
                if cf_index < len(g_init_dict[crush_id]['crush_friend_array']):
                    self.batch_fetch_friends(relationship,cf_index)
                else: #no more people to fetch
                    print "no more friends to process"
                    if len(g_init_dict[crush_id][rel_id+'_filtered_id_array']) >= settings.MINIMUM_LINEUP_MEMBERS: 
                        # take what we got!
                        print "take what we got and call finalize initialization"
                        self.finalize_initialization(relationship)
                    else:
                        self.initialize_fail(relationship,2)


    
    # ================================================================    
    # Method 4G: send matched id results back to server and launch lineup
    # ================================================================
    def finalize_initialization(self,relationship):
        global g_init_dict
        rel_id=str(relationship.id)
        crush_id=relationship.target_person.username
        
        if not crush_id in g_init_dict or g_init_dict[crush_id][rel_id+'_initialization_state']>0: 
            # other threads have already completed the job
            return
        print "finalized initialization with ids: " + str(g_init_dict[crush_id][rel_id+'_filtered_id_array'])
        #console.timeStamp("finished initialization")   
        self.create_lineup(relationship,g_init_dict[crush_id][rel_id+'_filtered_id_array'][:int(settings.IDEAL_LINEUP_MEMBERS)])

    # build a comma delimited list of usernames that should not be fetched from facebook
    # list consists of all of the crush's crushes, platonic friends & undecided lineup members (decided lineup members fall into previous lists)
    def get_exclude_id_array(self,relationship):
        exclude_facebook_id_array=[relationship.source_person.username] # the admirer will be manually inserted into lineup
        exclude_facebook_id_array.append(relationship.target_person.username) # don't put the crush themself in lineup, duh
        crush = relationship.target_person # crush is building lineup from his friend list
        crush_crushes= crush.crush_targets.all()
        crush_just_friends = crush.just_friends_targets.all()
        crush_progressing_admirer_rels = CrushRelationship.objects.progressing_admirers(crush)
        # loop through all their just_friends_targets and all their crush_targets and add their ids to a fql friendlist list
        for other_crush in crush_crushes:
            exclude_facebook_id_array.append(other_crush.username)
        for just_friend in crush_just_friends:
            exclude_facebook_id_array.append(just_friend.username)
        for rel in crush_progressing_admirer_rels:
            crush_undecided_lineup_members = rel.lineupmember_set.filter(decision=None)    
        for member in crush_undecided_lineup_members:
            exclude_facebook_id_array.append(member.username)
        return exclude_facebook_id_array

    # ================================================================    
    # Fail Handler - 2-4: user won't be able to try again, 5:user can try again later
    # ================================================================
    def initialize_fail(self,relationship,status=2):
        print "REL_ID: " + str(relationship.id) + " Initialize_fail called with status: " + str(status)
        relationship.lineup_initialization_status=status
        relationship.save(update_fields=['lineup_initialization_status'])
        self.cleanup_initialization_memory(relationship)
        return

    # returns true if successful, false otherwise
    # called by either initialize_lineup above, or by admirer_views functions try_mf_initialization & try_cf_initialization (fof initialization)
    def create_lineup(self,relationship,acceptable_id_array):
        global g_init_dict
        rel_id=str(relationship.id)
        crush_id=relationship.target_person.username
        if g_init_dict[crush_id][rel_id+'_initialization_state']>0:
            return
        print "REL ID:" + rel_id + "create_lineup: " + str(acceptable_id_array)
        g_init_dict[crush_id][rel_id+'_initialization_state']=1
        # determine where the admirer should randomly fall into the lineup
        # don't ever put member in last spot, cause there's a chance crush will skip making decision at end
        random_end = len(acceptable_id_array) - 1
        admirer_position=random.randint(0, random_end) # normally len(data) should be 9
        index = 0
        for lineup_id in acceptable_id_array:
            # if the current lineup position is where the admirer should go, then insert the admirer
            if index==admirer_position:
                LineupMember.objects.create(position=index,username = relationship.source_person.username,relationship=relationship,decision=None)
                #print "put crush in position: " + str(index) 
                index = index + 1            
            LineupMember.objects.create(position=index,username=lineup_id,relationship=relationship,decision=None)
            index = index + 1
        # the following condition (to put admirer in last position) should not occur, but just in case let's handle it    
        if len(acceptable_id_array)==admirer_position:
            LineupMember.objects.create(position=len(acceptable_id_array),username=relationship.source_person.username,relationship=relationship,decision=None)
      
        #print "number lineup members: " + str(relationship.lineupmember_set.count())

        relationship.lineup_initialization_status=1
        relationship.save(update_fields=['lineup_initialization_status'])
        self.cleanup_initialization_memory(relationship)
        #print "rel_id: " + str(relationship.id) + " saved initialization status: " + str(relationship.lineup_initialization_status)

    def cleanup_initialization_memory(self,relationship):
        global g_init_dict
        crush_id=relationship.target_person.username
        g_init_dict[crush_id][str(relationship.id) + '_initialization_state']=2
        g_init_dict[crush_id]['initialization_count']-=1
        if g_init_dict[crush_id]['initialization_count']==0:
            # wait 25 seconds for rest of threads to finish their work
            # after 25 seconds delete the main user key if another initialization routine has not been kickstarted
            time.sleep(25)
            try:
                if g_init_dict[crush_id]['initialization_count']==0:
                    del g_init_dict[crush_id]
            except:
                pass
class BasicLineupMember(models.Model):
    class Meta:
        abstract = True
        app_label='crush'
    
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
    decision = models.IntegerField(null=True, choices=DECISION_CHOICES, default=None,blank=True)
    
    def __unicode__(self):
        if self.user != None:
            return '(' + str(self.relationship) + ') ' + self.username + ': ' + self.user.first_name + ' ' + self.user.last_name 
        else:
            return '(' + str(self.relationship) + ') ' + self.username   
            
# details about each crush's secret admirer lineup (SAL)
class LineupMember(BasicLineupMember):
    
    class Meta:
        # this allows the models to be broken into separate model files
        app_label = 'crush'
        
    objects = LineupMemberManager()   
        
    # each lineup has many lineup members (10 by default) and each lineup member has only one lineup it belongs to (similar to blog entry)
    relationship = models.ForeignKey('CrushRelationship',null=True,blank=True,default=None)
    

# details about each crush's secret admirer lineup (SAL)
class SetupLineupMember(BasicLineupMember):
    
    class Meta:
        # this allows the models to be broken into separate model files
        app_label = 'crush'

    # if relationship is not a typical crush relationship , then it is a setup relationship
    relationship = models.ForeignKey('SetupRelationship',null=True,blank=True,default=None)
    date_last_notified = models.DateTimeField(null=True,default=None,blank=True);
    lineup_member_attraction = models.NullBooleanField(null=True,blank=True,default=None)
    
    # return None if unknown
    # return True if match
    # return False if no match
    def is_attraction_mutual(self):
        if self.lineup_member_attraction == True:
            return True
        elif self.lineup_member_attraction == False:
            return False
        elif self.decision > 0:
            return False
        else:
            return None
        