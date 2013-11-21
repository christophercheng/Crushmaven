# THIS FILE WAS WRITTEN TO ENCAPSULATE THE LINEUP INITIALIZATION PROCESS AS A MODULAR WEB SERVICE
# IT WAS NOT COMPLETED AND NEEDS TO BE RE-ENGINEERED


from django.http import HttpResponse,HttpResponseNotFound
from crush.utils import graph_api_fetch,fb_fetch
import json,re,thread
import urllib,random,time
from django.views.decorators.csrf import csrf_exempt
from threading import Lock
global_dict={} #keys will be relationship id
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)
# initialize_fof_crush receives a (post) request from crushmaven.com to create a lineup from the provided information
# it perform it's task to completion and then when it is done it will call a view function on crushmaven.com with the relationship id and a valid array of user ids or an error code
# if initialize_fof_crush is already being worked on by a previous request, it should just do nothin
# there needs to be a way to prevent getting stuck... some sort of timeout 

# initialize_fof_crush receives all of its data in the post dictionary
@csrf_exempt    
def initialize_fof_crush(request):
        global global_dict
        post_data=request.POST
        rel_id=post_data['rel_id']
        
        if rel_id in global_dict:
            return HttpResponse("0") # we are still working on a previous task
        
        global_dict[rel_id] = {}
        global_dict[rel_id]['access_token'] = post_data['access_token']
        global_dict[rel_id]['exclude_id_string'] = post_data['exclude_id_string']
        global_dict[rel_id]['admirer_id'] = post_data['admirer_id']
        global_dict[rel_id]['crush_id'] = post_data['crush_id']
        global_dict[rel_id]['admirer_gender'] = post_data['admirer_gender']
        global_dict[rel_id]['minimum_lineup_members'] = int(post_data['minimum_lineup_members'])
        global_dict[rel_id]['ideal_lineup_members'] = int(post_data['ideal_lineup_members'])

        crush_id = global_dict[rel_id]['crush_id']
        admirer_id=global_dict[rel_id]['admirer_id']
        exclude_id_string=global_dict[rel_id]['exclude_id_string']
        access_token = global_dict[rel_id]['access_token']
        minimum_lineup_members = global_dict[rel_id]['minimum_lineup_members']
        #ideal_lineup_members = global_dict[rel_id]['ideal_lineup_members']

        # set up the batch fql queries
        crush_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM+user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1=' + crush_id + ' AND NOT (uid2 IN (' + exclude_id_string + ')))"}'
        crush_app_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1=' + crush_id + ' AND NOT (uid2 IN (' + exclude_id_string + '))) AND is_app_user"}'
        mutual_friend_id_dict='{"method":"GET","name":"mutual-friends","relative_url":"' + crush_id +'/mutualfriends/' + admirer_id + '"}'
        mutual_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM user WHERE uid IN ({result=mutual-friends:$.data.*.id}) AND NOT (uid IN (' + exclude_id_string + '))"}'
        mutual_app_friend_dict='{"method":"GET","relative_url":"fql?q=SELECT uid,friend_count,sex FROM user WHERE uid IN ({result=mutual-friends:$.data.*.id}) AND NOT (uid IN (' + exclude_id_string + ')) AND is_app_user"}'
        
        # set up the post data
        post_dict = {}
        post_dict['access_token'] = access_token
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
            acceptable_id_array = try_api_mf_initialization(rel_id,mutual_app_friend_array)
            if len(acceptable_id_array)>minimum_lineup_members:
                return create_lineup(rel_id,acceptable_id_array)
        
        # METHOD 2: API 9 Friends from 9 Crush App Friends     
        if 'body' in fb_result[4] and 'data' in fb_result[4][u'body']:
            crush_app_friend_array=json.loads(fb_result[4][u'body'])['data']
            if len(crush_app_friend_array) >= minimum_lineup_members:
                random.shuffle(crush_app_friend_array)
                acceptable_id_array = try_api_cf_initialization(rel_id,crush_app_friend_array)
                if len(acceptable_id_array)>minimum_lineup_members:
                    return create_lineup(rel_id,acceptable_id_array)   
        
        # METHOD 3 & 4: NON-API MUTUAL FRIEND / NON-API 9 Friends from 9 Crush Friends
        if 'body' in fb_result[1] and 'data' in fb_result[1][u'body']:
            mutual_friend_array=json.loads(fb_result[1][u'body'])['data']
            #print "mutual_friend_array: " + str(len(mutual_friend_array)) + " : " + str(mutual_friend_array)
            # random.shuffle(mutual_friend_array) delay shuffling
            global_dict[rel_id]['mutual_friend_array']=mutual_friend_array
            if 'body' in fb_result[3] and 'data' in fb_result[3][u'body']:
                crush_friend_array=json.loads(fb_result[3][u'body'])['data']
                #random.shuffle(crush_friend_array) delay shuffling cause we may not need this yet
                global_dict[rel_id]['crush_friend_array']=crush_friend_array
                try_nonapi_mf_initialization(rel_id)
                return waiting_return(); #polling function that polls for about 90 seconds before giving up

        # if got here then we failed cause of bad facebook data fetch, so allow user to start it up again
        return HttpResponseNotFound("")

    #================================================================    
    # METHOD 1 ( FOF Initialization, Graph API) 
    # try to build an array with 9 friends from a single mutual friend
    # ================================================================

def try_api_mf_initialization(self,rel_id,mutual_app_friend_array):
    global global_dict
    crush_id = global_dict[rel_id]['crush_id']
    #admirer_id=global_dict[rel_id]['admirer_id']
    #exclude_id_string=global_dict[rel_id]['exclude_id_string']
    access_token = global_dict[rel_id]['access_token']
    minimum_lineup_members = global_dict[rel_id]['minimum_lineup_members']
    ideal_lineup_members = global_dict[rel_id]['ideal_lineup_members']
    admirer_gender = global_dict[rel_id]['admirer_gender']

    for mutual_friend in mutual_app_friend_array:
        if mutual_friend['friend_count'] < minimum_lineup_members:
            continue
        mfriend_id=str(mutual_friend['uid'])
        if mfriend_id not in global_dict[rel_id]: 
            global_dict[rel_id][mfriend_id]= Lock()
        global_dict[rel_id][mfriend_id].acquire() 
        # grab all friends of mutual app with admirer sex, friend sorted by friend count - via graph api
        fql_query = 'SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1=' + str(mutual_friend['uid']) + ' AND NOT (uid2 IN (' + g_init_dict[crush_id]['exclude_id_string'] + ')))) AND sex = "' + admirer_gender + '" ORDER BY friend_count DESC LIMIT ' + str(ideal_lineup_members)
        try:
            fql_query_results = graph_api_fetch(access_token,fql_query,expect_data=True,fql_query=True)
        except:
            global_dict[rel_id][mfriend_id].release()
            continue
        # if less than minimum lineup members, go on to next mutual friend
        if not fql_query_results or len(fql_query_results) < minimum_lineup_members:
            global_dict[rel_id][mfriend_id].release()
            continue 
        acceptable_id_array=[]
        for result in fql_query_results:
            acceptable_id_array.append(result['uid'])
            global_dict[rel_id]['exclude_id_string'] += "," + str(result['uid'])
        g_init_dict[rel_id][mfriend_id].release()
        # else add to lineup id array and setup in lineup
        return acceptable_id_array
    # if for loop ended without returning, then return False cause no lineup was created
    return []

#================================================================    
# METHOD 2 ( FOF Initialization, Graph API) 
# try to initialize lineup with 9 friends from 9 separate crush friends
# ================================================================

def try_api_cf_initialization(self,rel_id,crush_app_friend_array):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    #admirer_id=global_dict[rel_id]['admirer_id']
    exclude_id_string=global_dict[rel_id]['exclude_id_string']
    access_token = global_dict[rel_id]['access_token']
    minimum_lineup_members = global_dict[rel_id]['minimum_lineup_members']
    ideal_lineup_members = global_dict[rel_id]['ideal_lineup_members']
    admirer_gender = global_dict[rel_id]['admirer_gender'] 
    
    acceptable_id_array=[]
    # iterate through all crush app friends
    for friend in crush_app_friend_array:
        # get each crush app friend's friends sorted by friend_count and filtered by gender & exclude id list - limit result to 1
        fql_query = 'SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1=' + str(friend['uid']) + ' AND NOT (uid2 IN (' + exclude_id_string + ')))) AND sex = "' + admirer_gender + '" ORDER BY friend_count DESC LIMIT 1'
        try:
            fql_query_results = graph_api_fetch(access_token,fql_query,expect_data=True,fql_query=True)
        except:
            continue
        # if result < 0 skip rest of loop
        if len(fql_query_results) == 0:
            continue
        # else grab the result and add to acceptable id_array
        acceptable_id_array.append(fql_query_results[0]['uid'])
        exclude_id_string = exclude_id_string + ',' + str(fql_query_results[0]['uid'])
        # if acceptable id_array length == ideal lineup members then break out of loop entirely
        if len(acceptable_id_array) >= ideal_lineup_members:
            break
    # after loop, count the acceptable id_array_length, if greater than minimum lineup member setting, then call create_lineup
    if len(acceptable_id_array) >= minimum_lineup_members:
        for accepted_id in acceptable_id_array:
            g_init_dict[crush_id]['exclude_id_string'] += "," + str(accepted_id)
        return acceptable_id_array
    else:
        return []



#=====================================================================
# WAITING RETURN
# after call made to METHOD 3 below (try_nonapi_mf_initialization, things go a bit asynch
# at which point, waiting return is the only function which can return control back to the calling app

# Waiting return will loop for up to 90 (or other configurable amount of) seconds before returning an error
# Each loop will take one second (sleep for a second)
# after each loop, check to see if the initialization routines have completed (via global data check
# if initialization complete (either good to go or broken) then return with either HttpResponse or an Http Error code
def waiting_return(self,relationship):
    global g_init_dict;
    counter = 0
    crush_id=relationship['crush_id']
    rel_id_state=str(relationship['rel_id']) + '_initialization_state'
    while True: # this loop handles condition where user is annoyingly refreshing the admirer page while the initialization is in progress     
        #print "rel_id: " + str(relationship.id) + " counter: " + str(counter) + " initialization status: " + str(relationship.lineup_initialization_status)
        
        if not crush_id in g_init_dict or g_init_dict[crush_id][rel_id_state] == 2: # initialization was either a success or failed
            break
        elif counter >= 60: # if 25 seconds have passed then give up
            break
        time.sleep(1) # wait a second
        counter+=1
    
    
    return HttpResponseNotFound("5")

#================================================================    
# METHOD 3 ( FOF Initialization, NON API) 
# try to build an array with 9 friends from a single mutual friend
# ================================================================

def try_nonapi_mf_initialization(self,rel_id):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    
    if len(g_init_dict[crush_id][rel_id + '_mutual_friend_array']) > 0:
        # set some of the global variables
        random.shuffle(g_init_dict[crush_id][rel_id + '_mutual_friend_array'])
        process_mutual_friend(rel_id,0)
    
    else:
        try_nonapi_cf_initialization(rel_id)
        
#=================================================================    
# METHOD 3A - Process Mutual Friend
# ================================================================       
def process_mutual_friend(self,rel_id,mf_index):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    minimum_lineup_members = global_dict[rel_id]['minimum_lineup_members']

    mfriend=g_init_dict[crush_id][rel_id + '_mutual_friend_array'][mf_index]
    mfriend_id=str(mfriend['uid'])
    if mfriend_id not in g_init_dict[crush_id]: 
        g_init_dict[crush_id][mfriend_id]= Lock()
    g_init_dict[crush_id][mfriend_id].acquire()     
    g_init_dict[crush_id][rel_id + '_filtered_id_array']=[] # reset for each mutual friend processed
    logger.debug( "REL ID:" + rel_id + ": Method 3A (process_mutual_friend), mutual friend:" + mfriend_id + " at mf_index: " + str(mf_index) )
    num_friends = mfriend['friend_count']
    if num_friends < minimum_lineup_members or num_friends == None:
        finished_process_mutual_friend(rel_id,mf_index)
        return
    else:
        # build array of blocks to process (each block has up to 24 friends)
        max_q_block= (num_friends/24)+1
        q_block_array=[]
        for x in range(max_q_block):
            q_block_array.append(24*x)
        random.shuffle(q_block_array)
        # kick off process of a batch of q blocks

        process_batch_blocks(rel_id,mf_index,q_block_array,0)

        return # finished processing all mutual friends and did not find enough lineup members for each

#=================================================================    
# METHOD 3B - Process Batch Blocks
# request up to 5 blocks from facebook
# ================================================================      

def process_batch_blocks(self,rel_id,mf_index,q_block_array,q_start_index):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']

    # reset batch_blocks received and requested before we kickoff a new batch
    g_init_dict[crush_id][rel_id + '_batch_blocks_received']=0
    g_init_dict[crush_id][rel_id + '_batch_id_array']=[]
    logger.debug( "REL ID: " + rel_id + " Method 3B (process_batch_blocks), mutual friend: " + str(g_init_dict[crush_id][rel_id + '_mutual_friend_array'][mf_index]['uid']) + ", q_start_index: " + str(q_start_index) )
    last_fetch_index=q_start_index+5
    if last_fetch_index>len(q_block_array):
        last_fetch_index = len(q_block_array)
    g_init_dict[crush_id][rel_id + '_batch_blocks_requested']=last_fetch_index - q_start_index
    for x in range(q_start_index,last_fetch_index):
        thread.start_new_thread(fetch_block,(rel_id,mf_index,q_block_array,q_start_index,x)) #initialize lineup asynchronously            
        #self.fetch_block(rel_id,mf_index,q_block_array,q_start_index,x)

#=================================================================    
# METHOD 3C - Fetch Single Block
# ================================================================   

def fetch_block(self,rel_id,mf_index,q_block_array,q_start_index,q_index):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']

    try:
        fetch_response = fb_fetch(g_init_dict[crush_id][rel_id+'_mutual_friend_array'][mf_index]['uid'],q_block_array[q_index])
    except:
        fetch_block_finished(rel_id,mf_index,q_block_array,q_start_index, [])
        return
    extracted_id_list =  re.findall( 'user.php\?id=(.*?)\\\\">',fetch_response,re.MULTILINE )
    # remove duplicates in extracted_list
    extracted_id_list = list(set(extracted_id_list))
    logger.debug( "REL ID:" + rel_id + " Method 3C (fetch_block), mutual friend: " + str((g_init_dict[crush_id][rel_id+'_mutual_friend_array'])[mf_index]['uid'])  + ", q block: " + str(q_block_array[q_index]) + ", num extracted items: " + str(len(extracted_id_list)) )    
    fetch_block_finished(rel_id,mf_index,q_block_array,q_start_index,extracted_id_list)
    
#=================================================================    
# METHOD 3D - Fetch Block Finished
# fetch blocks check-in here, if all requested blocks have been check-in, then begin filtering of all fetch results
# ================================================================  

def fetch_block_finished(self,rel_id,mf_index,q_block_array,q_start_index,extracted_id_list):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    minimum_lineup_members = global_dict[rel_id]['minimum_lineup_members']
    ideal_lineup_members = global_dict[rel_id]['ideal_lineup_members']
    admirer_gender = global_dict[rel_id]['admirer_gender']
    
    g_init_dict[crush_id][rel_id+'_batch_id_array']+=extracted_id_list
    g_init_dict[crush_id][rel_id+'_batch_blocks_received']  += 1 # TODO replace this with F function to prevent race function

    if g_init_dict[crush_id][rel_id+'_batch_blocks_received'] < g_init_dict[crush_id][rel_id+'_batch_blocks_requested']:
        return

    if len(g_init_dict[crush_id][rel_id+'_batch_id_array'])==0:
        # this mutual friend probably has a privatized friend list
        finished_process_mutual_friend(rel_id,mf_index)
        return
    # all fetches have completed
    # filter batch id_array with gender   
    query_string = "SELECT uid FROM user WHERE uid IN ("
    query_string += ",".join(g_init_dict[crush_id][rel_id+'_batch_id_array'])
    query_string += ") AND NOT (uid IN (" + g_init_dict[crush_id]['exclude_id_string'] + ")) AND sex='" + admirer_gender + "'"
    try:
        filtered_batch_id_array = graph_api_fetch('',query_string,expect_data=True,fql_query=True)
    except:
        filtered_batch_id_array=[]
    logger.debug( "REL ID:" + rel_id +" Method 3D (fetch_block_finished), mutual friend: " + str(g_init_dict[crush_id][rel_id+'_mutual_friend_array'][mf_index]['uid']) + " - finished batch at q_start_index " + str(q_start_index) + " . Number filtered results: " + str(len(filtered_batch_id_array)) )
    g_init_dict[crush_id][rel_id+'_filtered_id_array'] += filtered_batch_id_array
    if len(g_init_dict[crush_id][rel_id+'_filtered_id_array']) >= ideal_lineup_members:
        acceptable_id_array=[]
        for item in g_init_dict[crush_id][rel_id+'_filtered_id_array']:
            g_init_dict[crush_id]['exclude_id_string'] += "," + str(item['uid'])
            acceptable_id_array.append(item['uid'])
            if len(acceptable_id_array) >= ideal_lineup_members:
                break
        #sort array
        acceptable_id_array.sort(key=int)
        g_init_dict[crush_id][str((g_init_dict[crush_id][rel_id+'_mutual_friend_array'])[mf_index]['uid'])].release()    
        create_lineup(rel_id,acceptable_id_array)
        return

    else:
        next_q_index = q_start_index + g_init_dict[crush_id][rel_id+'_batch_blocks_received']
        if next_q_index >= len(q_block_array):
            # done processing this mutual friend
            if len(g_init_dict[crush_id][rel_id+'_filtered_id_array']) >= minimum_lineup_members:
                # acceptable results from this mutual friend
                acceptable_id_array=[]
                for item in g_init_dict[crush_id][rel_id+'_filtered_id_array']:
                    g_init_dict[crush_id]['exclude_id_string'] += "," + str(item['uid']) 
                    acceptable_id_array.append(item['uid'])
                #sort array
                acceptable_id_array.sort(key=int)
                # return whole array cause we know it is > minimum and < ideal
                g_init_dict[crush_id][str((g_init_dict[crush_id][rel_id+'_mutual_friend_array'])[mf_index]['uid'])].release()
                create_lineup(rel_id,acceptable_id_array)
                return
            else:
                # no results to show for. try for next one
                finished_process_mutual_friend(rel_id,mf_index)
                return
        else: # process the next batch of q blocks
            process_batch_blocks(rel_id,mf_index,q_block_array,next_q_index)
            return
#=================================================================    
# METHOD 3E - FINISHED processing mutual friend
# determine what to do next
# ================================================================  

def finished_process_mutual_friend(self,rel_id,mf_index):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    # try to process next mutual friend
    g_init_dict[crush_id][str((g_init_dict[crush_id][rel_id+'_mutual_friend_array'])[mf_index]['uid'])].release()
    next_mf_index = mf_index + 1
    if next_mf_index < len(g_init_dict[crush_id][rel_id+'_mutual_friend_array']):
        process_mutual_friend(rel_id,next_mf_index)
    else:
        try_nonapi_cf_initialization(rel_id)
    # if no more mutual friends, then we'll have to switch to next lineup initialization process

#================================================================    
# METHOD 4 ( FOF Initialization, NON API) 
# # try to build an array with 9 friends from a 9 separate friend of crush 
# ================================================================        

def try_nonapi_cf_initialization(self,rel_id):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    minimum_lineup_members = global_dict[rel_id]['minimum_lineup_members']
    
    logger.debug( "TRY METHOD 4" )
    if len(g_init_dict[crush_id]['crush_friend_array']) < minimum_lineup_members:
        initialize_fail(rel_id,5)
        return
    else:
        g_init_dict[crush_id][rel_id+'_initialization_state']=0
        g_init_dict[crush_id][rel_id+'_filtered_id_array']=[]#scrap results to date
        random.shuffle(g_init_dict[crush_id]['crush_friend_array'])
        batch_fetch_friends(rel_id,0)

#================================================================    
# METHOD 4a - Subroutine A: Batch Fetch Handler - iteratively fetch 20 friends at given index
# ================================================================
def batch_fetch_friends(self,rel_id,cf_index):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    
    g_init_dict[crush_id][rel_id+'_batch_start_cf_index']=cf_index
    logger.debug( "Starting batch fetch at index: " + str(cf_index) )
    next_cf_index = cf_index + 18
    if next_cf_index > len(g_init_dict[crush_id]['crush_friend_array']):
        next_cf_index = len(g_init_dict[crush_id]['crush_friend_array'])
    g_init_dict[crush_id][rel_id+'_batch_friends_requested']= next_cf_index-cf_index # use this variable to determine if all requests have been retrieved and we can process final results
    g_init_dict[crush_id][rel_id+'_batch_friends_received'] = 0
    for x in range(cf_index,next_cf_index): # /iterate through next 18 friends
        # call a single person handler 
        thread.start_new_thread(start_single_friend_fetch,(rel_id,x)) #initialize lineup asynchronously            
        #self.start_single_friend_fetch(rel_id,x)     

# ================================================================    
# METHOD 4b - Subroutine B: Single Person Fetch Handler - build q block array and fire off processing for each block
# ================================================================
def start_single_friend_fetch(self,rel_id,cf_index):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    
    # calculate max q block by finding total friend count
    number_friends=g_init_dict[crush_id]['crush_friend_array'][cf_index]['friend_count']
    if number_friends==None or number_friends < 5:
        # skip this friend so continue on to next function and pass on variables
        finished_processing_friend(rel_id,cf_index)
        return
    
    max_q_block = (number_friends/24) + 1
    # build array of blocks to process
    q_block_array=[]
    for x in range(max_q_block):
        q_block_array.append(x*24)
    # randomize the array                         
    random.shuffle(q_block_array)
    # kick of processing of a batch of q blocks
    process_friend_block(rel_id,cf_index,q_block_array,0)

# ================================================================    
# METHOD 4c - Subroutine C: Single BLOCK Fetch Handler 
# ================================================================
def process_friend_block(self,rel_id,cf_index,q_block_array,q_index):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    
    if not crush_id in g_init_dict or g_init_dict[crush_id][rel_id+'_initialization_state']>0: 
        # other threads have already completed the job
        return
    crush_friend=g_init_dict[crush_id]['crush_friend_array'][cf_index]

    try:
        fetch_response = fb_fetch(crush_friend['uid'],q_block_array[q_index])
    except:
        get_another_friend_block(rel_id,cf_index,q_block_array,q_index)
        return

    extracted_id_list =  re.findall( 'user.php\?id=(.*?)\\\\">',fetch_response,re.MULTILINE )
    # remove duplicates in extracted_list
    extracted_id_list = list(set(extracted_id_list))
    if len(extracted_id_list)>0:
        filter_ids_by_admirer_conditions(rel_id,cf_index,q_block_array,q_index,extracted_id_list)
    else:
        #try another friend cause fetching more blocks from this friend will be worthless
        finished_processing_friend(rel_id,cf_index)

# ================================================================    
# METHOD 4d - Subroutine D: FILTER out user id's by admirer conditions 
# ================================================================    
def filter_ids_by_admirer_conditions(self,rel_id,cf_index,q_block_array,q_index,extracted_id_list):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    ideal_lineup_members = global_dict[rel_id]['ideal_lineup_members']
    admirer_gender = global_dict[rel_id]['admirer_gender']
    
    if not crush_id in g_init_dict or g_init_dict[crush_id][rel_id+'_initialization_state']>0: 
        # other threads have already completed the job
        return
    # filter batch id_array with gender   
    query_string = "SELECT uid FROM user WHERE uid IN ("
    query_string += ",".join(extracted_id_list)
    query_string += ") AND NOT (uid IN (" + str(g_init_dict[crush_id]['exclude_id_string']) + ")) AND sex='" + admirer_gender + "'"
    url = "https://graph.facebook.com/fql?q=" + query_string # don't need access token for this query             
    try:
        filtered_batch_id_array = graph_api_fetch('',url,expect_data=True,fql_query=True)
    except:
        get_another_friend_block(rel_id,cf_index,q_block_array,q_index)
        return
    if len(filtered_batch_id_array)>0:
        filtered_index=random.randint(0,len(filtered_batch_id_array)-1) # select a random friend from the filtered batch, not always the first one
        g_init_dict[crush_id][rel_id+'_filtered_id_array'].append(filtered_batch_id_array[filtered_index]['uid'])    
        g_init_dict[crush_id]['exclude_id_string'] = g_init_dict[crush_id]['exclude_id_string'] + ',' + str(filtered_batch_id_array[filtered_index]['uid'])
       
        if len(g_init_dict[crush_id][rel_id+'_filtered_id_array']) >= ideal_lineup_members:
            # we have enough lineup members so call final routine // if we get more ingore the others
            finalize_initialization(rel_id)
            return
    finished_processing_friend(rel_id,cf_index) #report in!
    return

# ================================================================    
# METHOD 4e - Subroutine E: Go back and fetch another block - all friends were of wrong sex
# ================================================================    
def get_another_friend_block(self,rel_id,cf_index,q_block_array,q_index):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    
    if not crush_id in g_init_dict or g_init_dict[crush_id][rel_id+'_initialization_state']>0: 
        # other threads have already completed the job
        return
    q_index = q_index + 1

    if q_index < len(q_block_array):
        process_friend_block(rel_id,cf_index,q_block_array,q_index) 
    else:
        finished_processing_friend(rel_id,cf_index)

# ================================================================    
# METHOD 4F - Subroutine F: Go WAY back and fetch another batch of friends 
# ================================================================    
def finished_processing_friend(self,rel_id,cf_index):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    minimum_lineup_members = global_dict[rel_id]['minimum_lineup_members']
    ideal_lineup_members = global_dict[rel_id]['ideal_lineup_members']
    
    if not crush_id in g_init_dict or g_init_dict[crush_id][rel_id+'_initialization_state']>0: 
        # other threads have already completed the job
        return
    g_init_dict[crush_id][rel_id+'_batch_friends_received'] += 1
    logger.debug( " - finished processing friend # " + str(g_init_dict[crush_id][rel_id+'_batch_friends_received']) + " at cf_index: " + str(cf_index) + " with number of ids: " + str(len(g_init_dict[crush_id][rel_id+'_filtered_id_array'])) )
    
    if g_init_dict[crush_id][rel_id+'_batch_friends_received'] == g_init_dict[crush_id][rel_id+'_batch_friends_requested']:
        if len(g_init_dict[crush_id][rel_id+'_filtered_id_array']) < ideal_lineup_members:
            cf_index = g_init_dict[crush_id][rel_id+'_batch_start_cf_index'] + g_init_dict[crush_id][rel_id+'_batch_friends_requested']
            
            if cf_index < len(g_init_dict[crush_id]['crush_friend_array']):
                batch_fetch_friends(rel_id,cf_index)
            else: #no more people to fetch
                print "no more friends to process"
                if len(g_init_dict[crush_id][rel_id+'_filtered_id_array']) >= minimum_lineup_members: 
                    # take what we got!
                    print "take what we got and call finalize initialization"
                    finalize_initialization(rel_id)
                else:
                    initialize_fail(rel_id,2)
                    return



# ================================================================    
# Method 4G: send matched id results back to server and launch lineup
# ================================================================
def finalize_initialization(self,rel_id):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    ideal_lineup_members = global_dict[rel_id]['ideal_lineup_members']
      
    if not crush_id in g_init_dict or g_init_dict[crush_id][rel_id+'_initialization_state']>0: 
        # other threads have already completed the job
        return
    logger.debug( "finalized initialization with ids: " + str(g_init_dict[crush_id][rel_id+'_filtered_id_array']) )
    #console.timeStamp("finished initialization")   
    create_lineup(rel_id,g_init_dict[crush_id][rel_id+'_filtered_id_array'][:ideal_lineup_members])


    # ================================================================    
    # Fail Handler - 2-4: user won't be able to try again, 5:user can try again later
    # ================================================================
def initialize_fail(self,rel_id,status=2):
        logger.debug( "REL_ID: " + str(rel_id) + " Initialize_fail called with status: " + str(status) )
        #relationship.lineup_initialization_status=status
        #relationship.save(update_fields=['lineup_initialization_status'])
        cleanup_initialization_memory(rel_id)
        return
    
def cleanup_initialization_memory(self,rel_id):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    
    g_init_dict[crush_id][rel_id + '_initialization_state']=2
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

# returns true if successful, false otherwise
    # called by either initialize_lineup above, or by admirer_views functions try_mf_initialization & try_cf_initialization (fof initialization)
def create_lineup(self,rel_id,acceptable_id_array):
    global g_init_dict
    crush_id = global_dict[rel_id]['crush_id']
    if g_init_dict[crush_id][rel_id+'_initialization_state']>0:
        return
    logger.debug( "REL ID:" + rel_id + "create_lineup: " + str(acceptable_id_array) )
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
        #LineupMember.objects.create(position=len(acceptable_id_array),username=relationship.source_person.username,relationship=relationship,decision=None)
        pass
    #print "number lineup members: " + str(relationship.lineupmember_set.count())

    #relationship.lineup_initialization_status=1
    #relationship.save(update_fields=['lineup_initialization_status'])
    cleanup_initialization_memory(rel_id)
    #print "rel_id: " + str(relationship.id) + " saved initialization status: " + str(relationship.lineup_initialization_status)
