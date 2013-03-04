'''
Created on Feb 21, 2013

@author: Chris Work
'''
g_init_dict={}

# 1. { crush_target_username : {}, }

    # 1a. { crush_target_username : { 'initialization_count' : 1 } }
    # 1b. { crush_target_username : { 'exclude_id_string' : string } }
    # 1c. { crush_target_username : { 'crush_friend_array' : [] }  }
    # 1d. { crush_target_username : { 'processing_friend_username' : Lock()  }
    # 1e. { crush_target_username : { relationship.id + '_relationship' : relationship object }  }
    # 1f. { crush_target_username : { relatipnship.id + '_mutual_friend_array' : [] }  }
    
    # MUTUAL FRIEND NON_API PROCESSING
    # 1g. { crush_target_username : { relationship.id + '_filtered_id_array' : [] }  }    
    # 1h. { crush_target_username : { relationship.id + '_batch_blocks_requested' : int }  } 
    # 1i. { crush_target_username : { relationship.id + '_batch_blocks_received' : int }  } 
    
    # CRUSH FRIEND NON_API PROCESSING
    # 1j. { crush_target_username : { relationship.id + '_batch_start_cf_index' : int }  }
    # 1j. { crush_target_username : { relationship.id + '_batch_friends_requested' : int }  }
    # 1j. { crush_target_username : { relationship.id + '_batch_friends_received' : int }  }    
    # 1k. { crush_target_username : { relationship.id + '_initialization_state' : 0|1|2 }  }  

    
    # 1g: allow other threads to stop immediately when one thread has completed the initialization task already
    # 1g: also allow ajax_display_lineup_block to know when lineup has actually been completely created
    # state 0 : initialization not finished
    # state 1 : initialization finished but lineup creation not completed (threads can prematurely stop)
    # state 2 : initiazliation and lineup creation is complete

