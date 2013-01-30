from django.db import models
import random, urllib, json
from django.conf import settings
from  crush.models.relationship_models import CrushRelationship
from crush.models.user_models import FacebookUser

class LineupMemberManager(models.Manager):
    class Meta:
    # this allows the models to be broken into separate model files
        app_label = 'crush'
    
    # build a comma delimited list of usernames that should not be fetched from facebook
        # list consists of all crushes, all platonic friends, all undecided lineup members (decided lineup members fall into previous lists)
    def get_exclude_ids(self,relationship):
        exclude_facebook_ids=""
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
            exclude_facebook_ids = exclude_facebook_ids + "'" + crush.username + "',"
        for just_friend in builder_just_friends:
            exclude_facebook_ids = exclude_facebook_ids + "'" + just_friend.username + "',"
        for rel in builder_incomplete_admirer_rels:
            builder_undecided_lineup_members = rel.lineupmember_set.filter(decision=None)    
        for member in builder_undecided_lineup_members:
            exclude_facebook_ids = exclude_facebook_ids + "'" + member.username + "',"
        # list all friends usernames who do not have a family relationship with me and are of a certain gender limited to top 9 results
        if relationship.friendship_type != 1: 
            # don't fetch the admirer (they will get inserted manually)
            if exclude_facebook_ids == "":
                exclude_facebook_ids = "'" + str(relationship.source_person.username) + "'"
            else:
                exclude_facebook_ids = exclude_facebook_ids + "'" + str(relationship.source_person.username) + "'"
        else: 
            if exclude_facebook_ids != "": # remove the trailing comma
                exclude_facebook_ids = exclude_facebook_ids[:-1]
        return exclude_facebook_ids

 
    def get_acceptable_ids(self,relationship,exclude_facebook_ids):
        admirer_gender= 'Male' if relationship.source_person.gender == 'M'  else 'Female'
        try:
            if relationship.friendship_type == 0: # the crush can build the lineup from his/her friend list  
                fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (SELECT uid FROM family where profile_id=me())) AND NOT (uid2 IN (" + exclude_facebook_ids + "))) ) AND sex = '" + admirer_gender + "'  ORDER BY friend_count DESC LIMIT 9"
                fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,relationship.target_person.access_token))
                data = json.load(fql_query_results)['data'] 
            elif relationship.friendship_type > 0: # the admirer must build the lineup from his friend list
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
        # the complicated scenario: get ids of 9 friends of the mutual friends, if that fails, grab from next mutual friend
        # if all mutual friends fail, then grab 1 friend-of-friend from 9 random friends of crush
        return data
    
    # returns true if successful, false otherwise
    def initialize_lineup(self,relationship):
        print "initializing relationship for admirer: " + relationship.source_person.first_name + " " + relationship.source_person.last_name

        exclude_facebook_ids=self.get_exclude_ids(relationship)
        acceptable_id_array=self.get_acceptable_ids(relationship,exclude_facebook_ids)
        
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
        admirer_position=random.randint(0, len(acceptable_id_array)-1) # normally len(data) should be 9
        index = 0
        for fql_user in acceptable_id_array:
            print "iteration execution"
            # if the current lineup position is where the admirer should go, then insert the admirer
            if index==admirer_position:
                LineupMember.objects.create(position=index,username = relationship.source_person.username,relationship=relationship,decision=None)
                print "put crush in position: " + str(index) 
                index = index + 1            
            LineupMember.objects.create(position=index,username=fql_user['uid'],relationship=relationship,decision=None)
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