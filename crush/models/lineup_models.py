from django.db import models
import urllib, json,urllib2
from django.conf import settings
from  crush.models.relationship_models import CrushRelationship
from crush.models.user_models import FacebookUser   
from random import shuffle
import random
import re,time,thread

class LineupMemberManager(models.Manager):
    class Meta:
    # this allows the models to be broken into separate model files
        app_label = 'crush'

    g_relationship=None
    g_exclude_id_string=None
    g_mutual_friend_array=None
    g_crush_friend_array=None
    g_batch_blocks_requested=None
    g_batch_blocks_received=None
    g_filtered_id_array=None
    g_batch_id_array=None
    
    g_batch_friends_requested=None
    g_batch_friends_received=None

    #================================================================    
    # METHOD 4 -     # try to build an array with 9 friends from a single mutual friend (non-api)
    # ================================================================

    def try_nonapi_cf_initialization(self,relationship,exclude_id_string):
        global g_relationship,g_exclude_id_string,g_filtered_id_array,g_crush_friend_array
        if len(g_crush_friend_array) < settings.MINIMUM_LINEUP_MEMBERS:
            self.initialize_fail(2)
            return
        else:
            g_relationship=relationship
            g_exclude_id_string=exclude_id_string
            g_filtered_id_array=[]#scrap results to date
            random.shuffle(g_crush_friend_array)
            self.batch_fetch_friends(0)
    
    #================================================================    
    # METHOD 4 - Subroutine A: Batch Fetch Handler - iteratively fetch 20 friends at given index
    # ================================================================
    def batch_fetch_friends(self,cf_index):
        global g_batch_friends_requested,g_batch_friends_received
        print "Starting batch fetch at index: " + str(cf_index)
        next_cf_index = cf_index + 18
        if next_cf_index > len(g_crush_friend_array):
            next_cf_index = len(g_crush_friend_array)
        g_batch_friends_requested= next_cf_index-cf_index # use this variable to determine if all requests have been retrieved and we can process final results
        g_batch_friends_received = 0
        for x in range(cf_index,next_cf_index): # /iterate through next 18 friends
            # call a single person handler
            #self.start_single_friend_fetch(x)  
            thread.start_new_thread(self.start_single_friend_fetch,(x,)) #initialize lineup asynchronously            
                  

    # ================================================================    
    # METHOD 4 - Subroutine B: Single Person Fetch Handler - build q block array and fire off processing for each block
    # ================================================================
    def start_single_friend_fetch(self,cf_index):
        # create q block array
        q_block_num_array=[]
        # calculate max q block by finding total friend count
        number_friends=g_crush_friend_array[cf_index]['friend_count']
        if number_friends==None or number_friends < 5:
            # skip this friend so continue on to next function and pass on variables
            self.finished_processing_friend(cf_index)
            return
        
        max_q_block = (number_friends/24) + 1
        # build array of blocks to process
        q_block_array=[]
        for x in range(max_q_block):
            q_block_array.append(x*24)
        # randomize the array                         
        random.shuffle(q_block_array)
        # kick of processing of a batch of q blocks
        self.process_friend_block(cf_index,q_block_array,0)
    
    # ================================================================    
    # METHOD 4 - Subroutine C: Single BLOCK Fetch Handler 
    # ================================================================
    def process_friend_block(self,cf_index,q_block_array,q_index):
        if len(g_filtered_id_array) >= settings.IDEAL_LINEUP_MEMBERS: 
            # other threads have already completed the job
            return
        crush_friend=g_crush_friend_array[cf_index]
        fetch_url='https://www.facebook.com/ajax/browser/list/allfriends/?__a=0&start=' + str(q_block_array[q_index]) + '&uid=' + str(crush_friend['uid'])
        #console.log("FETCH block #",q_block_array[q_index]," for user object: ",window.crush_friend_array[process_f_index])
        opener = urllib2.build_opener()
        opener.addheaders.append(('Host', 'http://www.facebook.com'))
        opener.addheaders.append(('USER_AGENT', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'))
        opener.addheaders.append( ('Accept', '*/*') )
        try:
            fetch_response = urllib2.Request(fetch_url)
            fetch_response = opener.open(fetch_response)
            fetch_response = fetch_response.read()
        except:
            self.get_another_friend_block(cf_index,q_block_array,q_index)
            return

        extracted_id_list =  re.findall( 'user.php\?id=(.*?)\\\\">',fetch_response,re.MULTILINE )
        # remove duplicates in extracted_list
        extracted_id_list = list(set(extracted_id_list))
        if len(extracted_id_list)>0:
            self.filter_ids_by_admirer_conditions(cf_index,q_block_array,q_index,extracted_id_list)
        else:
            #try another friend cause fetching more blocks from this friend will be worthless
            self.finished_processing_friend(cf_index)
    
    # ================================================================    
    # METHOD 4 - Subroutine D: FILTER out user id's by admirer conditions 
    # ================================================================    
    def filter_ids_by_admirer_conditions(self,cf_index,q_block_array,q_index,extracted_id_list):
        global g_filtered_id_array,g_exclude_id_string
        if len(g_filtered_id_array) >= settings.IDEAL_LINEUP_MEMBERS: 
            # other threads have already completed the job
            return
        # filter batch id_array with gender   
        query_string = "SELECT uid FROM user WHERE uid IN ("
        query_string += ",".join(extracted_id_list)
        query_string += ") AND NOT (uid IN (" + str(g_exclude_id_string) + ")) AND sex='" + g_relationship.source_person.get_fb_gender() + "'"
        url = "https://graph.facebook.com/fql?q=" + query_string # don't need access token for this query             
        try:
            filtered_batch_id_array = urllib.urlopen(url)
            filtered_batch_id_array= json.load(filtered_batch_id_array)
            filtered_batch_id_array = filtered_batch_id_array['data']
            #print str(g_mutual_friend_array[mf_index]['uid']) + " - finished batch process. Result for q_start_index: " + str(q_start_index) + " : " + str(filtered_batch_id_array)
        except:
            self.get_another_friend_block(cf_index,q_block_array,q_index)
            return
          
        g_filtered_id_array.append(filtered_batch_id_array[0]['uid'])    
        #console.log("GOT A MEMBER from user#:",window.crush_friend_array[process_f_index]," current matched id array: ",window.matched_id_array);
        if len(g_filtered_id_array) >= settings.IDEAL_LINEUP_MEMBERS:
            # we have enough lineup members so call final routine // if we get more ingore the others
            self.finalize_initialization()
            return
        else:# update the exclude id string with the latest addition
            g_exclude_id_string = g_exclude_id_string + ',' + str(filtered_batch_id_array[0]['uid'])
            self.finished_processing_friend(cf_index) #report in!
            return
    
    # ================================================================    
    # METHOD 4 - Subroutine E: Go back and fetch another block - all friends were of wrong sex
    # ================================================================    
    def get_another_friend_block(self,cf_index,q_block_array,q_index):
        
        if len(g_filtered_id_array) >= settings.IDEAL_LINEUP_MEMBERS: 
            # other threads have already completed the job
            return
        q_index = q_index + 1
        #console.log("fetching another block for user ",window.crush_friend_array[process_f_index], "at",q_index)
        if q_index < len(q_block_array):
            self.process_friend_block(cf_index,q_block_array,q_index) 
        else:
            self.finished_processing_friend(cf_index)
    
    # ================================================================    
    # METHOD 4 - Subroutine F: Go WAY back and fetch another batch of friends 
    # ================================================================    
    def finished_processing_friend(self,cf_index):
        global g_batch_friends_received
        if len(g_filtered_id_array) >= settings.IDEAL_LINEUP_MEMBERS: 
            # other threads have already completed the job
            return
        g_batch_friends_received += 1
        print " - finished processing friend # " + str(g_batch_friends_received) + " with number of ids: " + str(len(g_filtered_id_array))
        #console.log("checking in: ",window.crush_friend_array[process_f_index],"# batch friends received:",window.batch_friends_received, "total sent:",window.batch_friends_requested, "matched id's:",window.matched_id_array)
        if g_batch_friends_received >= g_batch_friends_requested:
            cf_index = cf_index + g_batch_friends_requested
            if len(g_filtered_id_array) < settings.IDEAL_LINEUP_MEMBERS:
                if cf_index < len(g_crush_friend_array):
                    self.batch_fetch_friends(cf_index)
                else: #no more people to fetch
                    if len(g_filtered_id_array) >= settings.MINIMUM_LINEUP_MEMBERS: 
                        # take what we got!
                        self.finalize_initialization()
                    else:
                        self.initialize_fail(2)

    # ================================================================    
    # METHOD 4 - Subroutine: Fail Handler - 2-4: user won't be able to try again, 5:user can try again later
    # ================================================================
    def initialize_fail(self,status=2):
        global g_relationship
        g_relationship.lineup_initialization_status=status
        g_relationship.save(update_fields=['lineup_initialization_status'])
        return
    
    # ================================================================    
    # HELPER METHOD: send matched id results back to server and launch lineup
    # ================================================================
    def finalize_initialization(self):
        print "finalized initialization with ids: " + str(g_filtered_id_array)
        #console.timeStamp("finished initialization")   
        #self.create_lineup(g_relationship,filtered_id_array[:int(settings.IDEAL_LINEUP_MEMBERS)])
            

    
    # try to build an array with 9 friends from a single mutual friend (non-api)
    def try_nonapi_mf_initialization(self,relationship,exclude_id_string):
        global g_exclude_id_string,g_relationship,g_filtered_id_array

        if len(g_mutual_friend_array) > 0:
            random.shuffle(g_mutual_friend_array)
            self.process_mutual_friend(0)
        else:
            # set some of the global variables
            g_exclude_id_string=exclude_id_string
            g_relationship=relationship
            g_filtered_id_array=[]
            self.try_nonapi_cf_initialization()
       
    def process_mutual_friend(self,mf_index):
        global g_filtered_id_array
        g_filtered_id_array=[] # reset for each mutual friend processed
        mfriend=g_mutual_friend_array[mf_index]
        print "Process Mutual Friend: " + str(mfriend['uid'])
        num_friends = mfriend['friend_count']
        if num_friends < settings.MINIMUM_LINEUP_MEMBERS or num_friends == None:
            self.finished_process_mutual_friend(mf_index)
            return
        else:
            # build array of blocks to process (each block has up to 24 friends)
            max_q_block= (num_friends/24)+1
            q_block_array=[]
            for x in range(max_q_block):
                q_block_array.append(24*x)
            random.shuffle(q_block_array)
            # kick off process of a batch of q blocks
            self.process_batch_blocks(mf_index,q_block_array,0)
            return # finished processing all mutual friends and did not find enough lineup members for each
    
    # nonapi_mf_initialization routine
    # request up to 5 blocks from facebook
    def process_batch_blocks(self,mf_index,q_block_array,q_start_index):
        global g_batch_blocks_requested,g_batch_blocks_received, g_batch_id_array
        # reset batch_blocks received and requested before we kickoff a new batch
        g_batch_blocks_requested=0
        g_batch_blocks_received=0
        g_batch_id_array=[]
        print str(g_mutual_friend_array[mf_index]['uid']) + " - batch process 5 q_blocks starting at " + str(q_block_array[q_start_index])
        last_fetch_index=q_start_index+5
        if last_fetch_index>len(q_block_array):
            last_fetch_index = len(q_block_array)
        g_batch_blocks_requested=last_fetch_index - q_start_index
        for x in range(q_start_index,last_fetch_index):
            thread.start_new_thread(self.fetch_block,(mf_index,q_block_array,q_start_index,x)) #initialize lineup asynchronously            
            #self.fetch_block(mf_index,q_block_array,q_start_index,x)

    def fetch_block(self,mf_index,q_block_array,q_start_index,q_index):
        global g_mutual_friend_array
        print "process mutual friend: " + str(g_mutual_friend_array[mf_index]['uid']) + ", q block: " + str(q_block_array[q_index])   
        opener = urllib2.build_opener()
        opener.addheaders.append(('Host', 'http://www.facebook.com'))
        opener.addheaders.append(('USER_AGENT', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0'))
        opener.addheaders.append( ('Accept', '*/*') )
        fetch_url="https://www.facebook.com/ajax/browser/list/allfriends/?uid=" + str(g_mutual_friend_array[mf_index]['uid']) + "&__a=1&start=" + str(q_block_array[q_index])
        try:
            fetch_response = urllib2.Request(fetch_url)
            fetch_response = opener.open(fetch_response)
            fetch_response = fetch_response.read()
        except:
            LineupMember.objects.fetch_block_finished(mf_index,q_block_array,q_start_index, [])
            return
        extracted_id_list =  re.findall( 'user.php\?id=(.*?)\\\\">',fetch_response,re.MULTILINE )
        # remove duplicates in extracted_list
        extracted_id_list = list(set(extracted_id_list))
        print "extracted ids: " + str(extracted_id_list)
        LineupMember.objects.fetch_block_finished(mf_index,q_block_array,q_start_index,extracted_id_list)

    def fetch_block_finished(self,mf_index,q_block_array,q_start_index,extracted_id_list):
        global g_batch_blocks_requested,g_batch_blocks_received,g_batch_id_array,g_filtered_id_array
        g_batch_id_array+=extracted_id_list
        g_batch_blocks_received  += 1 # TODO replace this with F function to prevent race function

        if g_batch_blocks_received < g_batch_blocks_requested:
            return
        if len(g_batch_id_array)==0:
            # this mutual friend probably has a privatized friend list
            self.finished_process_mutual_friend(mf_index)
            return
        # all fetches have completed
        # filter batch id_array with gender   
        query_string = "SELECT uid FROM user WHERE uid IN ("
        query_string += ",".join(g_batch_id_array)
        query_string += ") AND NOT (uid IN (" + g_exclude_id_string + ")) AND sex='" + g_relationship.source_person.get_fb_gender() + "'"
        url = "https://graph.facebook.com/fql?q=" + query_string # don't need access token for this query             
        filtered_batch_id_array = urllib.urlopen(url)
        filtered_batch_id_array= json.load(filtered_batch_id_array)
        filtered_batch_id_array = filtered_batch_id_array['data']
        print str(g_mutual_friend_array[mf_index]['uid']) + " - finished batch process. Result for q_start_index: " + str(q_start_index) + " : " + str(filtered_batch_id_array)
        g_filtered_id_array += filtered_batch_id_array
        if len(g_filtered_id_array) >= settings.IDEAL_LINEUP_MEMBERS:
            acceptable_id_array=[]
            for item in g_filtered_id_array:
                acceptable_id_array.append(item['uid'])
            #sort array
            acceptable_id_array.sort(key=int)
            #self.create_lineup(g_relationship,acceptable_id_array[:int(settings.IDEAL_LINEUP_MEMBERS)])
            return
        else:
            next_q_index = q_start_index + g_batch_blocks_received
            if next_q_index >= len(q_block_array):
                # done processing this mutual friend
                if len(g_filtered_id_array) >= settings.MINIMUM_LINEUP_MEMBERS:
                    # acceptable results from this mutual friend
                    acceptable_id_array=[]
                    for item in g_filtered_id_array:
                        acceptable_id_array.append(item['uid'])
                        #sort array
                        acceptable_id_array.sort(key=int)
                        #self.create_lineup(g_relationship,acceptable_id_array) # return whole array cause we know it is > minimum and < ideal
                        return
                else:
                    # no results to show for. try for next one
                    return self.finished_process_mutual_friend(mf_index)
            else: # process the next batch of q blocks
                return self.process_batch_blocks(mf_index,q_block_array,next_q_index)

    def finished_process_mutual_friend(self,mf_index):
        # try to process next mutual friend
        next_mf_index = mf_index + 1
        if next_mf_index < len(g_mutual_friend_array):
            self.process_mutual_friend(next_mf_index)
        else:
            self.try_nonapi_cf_initialization()
        # if no more mutual friends, then we'll have to switch to next lineup initialization process

    # try to build an array with 9 friends from a single mutual friend
    # called by 
    def try_api_mf_initialization(self,mutual_app_friend_array,exclude_id_string,relationship):
        for mutual_friend in mutual_app_friend_array:
            if mutual_friend['friend_count'] <settings.MINIMUM_LINEUP_MEMBERS:
                continue
            # grab all friends of mutual app with admirer sex, friend sorted by friend count - via graph api
            fql_query = 'SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1=' + str(mutual_friend['uid']) + ' AND NOT (uid2 IN (' + exclude_id_string + ')))) AND sex = "' + relationship.source_person.get_fb_gender() + '" ORDER BY friend_count DESC LIMIT ' + str(settings.IDEAL_LINEUP_MEMBERS)
            fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,relationship.target_person.access_token))
            fql_query_results=json.load(fql_query_results)
            print fql_query_results
            fql_query_results = fql_query_results['data'] 
            # if less than minimum lineup members, go on to next mutual friend
            if len(fql_query_results) < settings.MINIMUM_LINEUP_MEMBERS:
                continue 
            acceptable_id_array=[]
            for result in fql_query_results:
                acceptable_id_array.append(result['uid'])
            # else add to lineup id array and setup in lineup
            return acceptable_id_array
        # if for loop ended without returning, then return False cause no lineup was created
        return []
    
    # try to initialize lineup with 9 friends from 9 separate crush friends
    # called by ajax_try_fof_initialization
    def try_api_cf_initialization(self,crush_app_friend_array,exclude_id_string,relationship):
        acceptable_id_array=[]
        # iterate through all crush app friends
        for friend in crush_app_friend_array:
            # get each crush app friend's friends sorted by friend_count and filtered by gender & exclude id list - limit result to 1
            fql_query = 'SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1=' + str(friend['uid']) + ' AND NOT (uid2 IN (' + exclude_id_string + ')))) AND sex = "' + relationship.source_person.get_fb_gender() + '" ORDER BY friend_count DESC LIMIT 1'
            fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,relationship.target_person.access_token))
            fql_query_results=json.load(fql_query_results)
            fql_query_results = fql_query_results['data'] 
            # if result < 0 skip rest of loop
            if len(fql_query_results) == 0:
                continue
            # else grab the result and add to acceptable id_array
            acceptable_id_array.append(fql_query_results[0]['uid'])
            exclude_id_string = exclude_id_string + ',' + fql_query_results[0]['uid']
            # if acceptable id_array length == ideal lineup members then break out of loop entirely
            if len(acceptable_id_array) >= settings.IDEAL_LINEUP_MEMBERS:
                break
        # after loop, count the acceptable id_array_length, if greater than minimum lineup member setting, then call create_lineup
        if len(acceptable_id_array) >= settings.MINIMUM_LINEUP_MEMBERS:
            return acceptable_id_array
        else:
            return []
      
    def initialize_friend_of_friend_crush(self,relationship,exclude_id_array):
        global g_relationship,g_exclude_id_string,g_mutual_friend_array,g_crush_friend_array

        exclude_id_string=LineupMember.objects.comma_delimit_list(exclude_id_array)
        post_dict = {}
        crush_username=relationship.target_person.username
        post_dict['access_token'] = relationship.target_person.access_token
        crush_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM+user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1=' + crush_username + ' AND NOT (uid2 IN (' + exclude_id_string + ')))"}'
        crush_app_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1=' + crush_username + ' AND NOT (uid2 IN (' + exclude_id_string + '))) AND is_app_user"}'
        mutual_friend_id_dict='{"method":"GET","name":"mutual-friends","relative_url":"' + crush_username +'/mutualfriends/' + relationship.source_person.username + '"}'
        mutual_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM user WHERE uid IN ({result=mutual-friends:$.data.*.id}) AND NOT (uid IN (' + exclude_id_string + '))"}'
        mutual_app_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM user WHERE uid IN ({result=mutual-friends:$.data.*.id}) AND NOT (uid IN (' + exclude_id_string + ')) AND is_app_user"}'
        
        post_dict['batch'] = '[' + mutual_friend_id_dict + ',' + mutual_friend_dict + ',' + mutual_app_friend_dict + ',' + crush_friend_dict + ',' + crush_app_friend_dict  + ']'
        post_dict=urllib.urlencode(post_dict)    
        url='https://graph.facebook.com'
        
        mutual_app_friend_array=[]
        num_fetch_tries=0 # try to grab data from facebook two times if necessary. sometimes it does not return data       
        while (num_fetch_tries < 2):    
            fb_result = urllib.urlopen(url,post_dict)
            fb_result = json.load(fb_result)
        
            if 'body' in fb_result[2] and 'data' in fb_result[2][u'body']:
                mutual_app_friend_array=json.loads(fb_result[2][u'body'])['data']
                random.shuffle(mutual_app_friend_array)
                num_fetch_tries=9
            num_fetch_tries+=1
        
        # METHOD 1: API MUTUAL APP FRIEND
        if len(mutual_app_friend_array)>0:
            acceptable_id_array = self.try_api_mf_initialization(mutual_app_friend_array,exclude_id_string,relationship)
            if len(acceptable_id_array)>settings.MINIMUM_LINEUP_MEMBERS:
                self.create_lineup(relationship, acceptable_id_array)
                return
        
        # METHOD 2: API 9 Friends from 9 Crush App Friends     
        if 'body' in fb_result[4] and 'data' in fb_result[4][u'body']:
            crush_app_friend_array=json.loads(fb_result[4][u'body'])['data']
            if len(crush_app_friend_array) >= settings.MINIMUM_LINEUP_MEMBERS:
                random.shuffle(crush_app_friend_array)
                acceptable_id_array = self.try_api_cf_initialization(crush_app_friend_array,exclude_id_string,relationship)
                if len(acceptable_id_array)>settings.MINIMUM_LINEUP_MEMBERS:
                    self.create_lineup(relationship,acceptable_id_array)   
                    return
        
        # METHOD 3 & 4: NON-API MUTUAL FRIEND / NON-API 9 Friends from 9 Crush Friends
        if 'body' in fb_result[1] and 'data' in fb_result[1][u'body']:
            g_mutual_friend_array=json.loads(fb_result[1][u'body'])['data']
            if 'body' in fb_result[3] and 'data' in fb_result[3][u'body']:
                g_crush_friend_array=json.loads(fb_result[3][u'body'])['data']
                #self.try_nonapi_mf_initialization(relationship,exclude_id_string)
                self.try_nonapi_cf_initialization(relationship,exclude_id_string)
                return

        # if got here then we failed cause of bad facebook data fetch, so allow user to start it up again
        relationship.lineup_initialization_status=5
        relationship.save(update_fields=['lineup_initialization_status'])
    
    def initialize_friend_or_nonfriend_crush(self,relationship,exclude_facebook_id_array):
        admirer_gender= u'male' if relationship.source_person.gender == u'M'  else u'female'
        exclude_facebook_ids=self.comma_delimit_list(exclude_facebook_id_array)
        acceptable_id_array=[]
        try:
            if relationship.friendship_type == 0: # the crush can build the lineup from his/her friend list  
                fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (SELECT uid FROM family where profile_id=me())) AND NOT (uid2 IN (" + exclude_facebook_ids + "))) ) AND sex = '" + admirer_gender + "'  ORDER BY friend_count DESC LIMIT 9"
                fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,relationship.target_person.access_token))
                data = json.load(fql_query_results)['data'] 
            elif relationship.friendship_type == 2: # the admirer must build the lineup from his friend list
                fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (" + exclude_facebook_ids + ")) )) AND sex = '" + admirer_gender + "'  ORDER BY friend_count DESC LIMIT 9"
                fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,relationship.source_person.access_token))
                data = json.load(fql_query_results)['data'] 
        except:
            print "Key or Value Error on Fql Query Fetch read!"
            relationship.lineup_initialization_status=5
            relationship.save(update_fields=['lineup_initialization_status'])
            return
        for item in data:
            acceptable_id_array.append(item['uid'])
            
        if len(acceptable_id_array) < settings.MINIMUM_LINEUP_MEMBERS:
            if relationship.friendship_type == 0:
                relationship.lineup_initialization_status=3
            else:
                relationship.lineup_initialization_status=2
            relationship.save(update_fields=['lineup_initialization_status'])
        else:      
            print "json data results for admirer: " + relationship.source_person.first_name + " " + relationship.source_person.last_name + " : " + str(acceptable_id_array)
            self.create_lineup(relationship,acceptable_id_array)

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
    
    def comma_delimit_list(self,array):
        myString = ",".join(array)
        return myString
    
    # returns true if successful, false otherwise
    def initialize_lineup(self,relationship):
        print "initializing relationship for admirer: " + relationship.source_person.first_name + " " + relationship.source_person.last_name
        exclude_facebook_id_array=self.get_exclude_id_array(relationship)
        if relationship.friendship_type==1:
            self.initialize_friend_of_friend_crush(relationship,exclude_facebook_id_array)
        else:
            self.initialize_friend_or_nonfriend_crush(relationship,exclude_facebook_id_array)      
        return

    # returns true if successful, false otherwise
    # called by either initialize_lineup above, or by admirer_views functions try_mf_initialization & try_cf_initialization (fof initialization)
    def create_lineup(self,relationship,acceptable_id_array):
        print "CREATING LINEUP WITH MEMBERS: " + str(acceptable_id_array)
        
        # determine where the admirer should randomly fall into the lineup
        # don't ever put member in last spot, cause there's a chance crush will skip making decision at end
        random_end = len(acceptable_id_array) - 1
        admirer_position=random.randint(0, random_end) # normally len(data) should be 9
        index = 0
        for lineup_id in acceptable_id_array:
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