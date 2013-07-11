from django.http import HttpResponse,HttpResponseForbidden
from crush.utils import graph_api_fetch
import json

def initialize_nf_crush(request,admirer_id,crush_id,admirer_gender,minimum_lineup_members):
        global g_init_dict
        print "Initialize non friend crush"
        get_data=request.GET
        access_token=get_data['access_token'] # relationship.source_person.access_token
        exclude_id_string=get_data['exclude_id_string'] #g_init_dict[crush_id]['exclude_id_string']
        response_data=[]
        try:
            fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = " + admirer_id + " AND NOT (uid2 IN (" + exclude_id_string+ ")) )) AND sex = '" + admirer_gender + "'  ORDER BY friend_count DESC LIMIT 9"
            data = graph_api_fetch(access_token,fql_query,expect_data=True,fql_query=True)
        except:
            print "Key or Value Error on Fql Query Fetch read!"
            return HttpResponseForbidden("5")

        
        if not data or len(data) < minimum_lineup_members:
            print "NON FRIEND - not enough friends"
            return HttpResponseForbidden("2")
        
        for item in data:
            response_data[item['uid']]

        return HttpResponse(json.dumps(response_data),content_type="application/json")