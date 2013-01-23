from django.db import models
import random, urllib, json
from django.conf import settings
from  crush.models.relationship_models import CrushRelationship
from crush.models.user_models import FacebookUser

class LineupManager(models.Manager):
    class Meta:
    # this allows the models to be broken into separate model files
        app_label = 'crush'
    # returns true if successful, false otherwise
    def initialize_lineup(self,relationship):
        print "initializing relationship for admirer: " + relationship.source_person.first_name + " " + relationship.source_person.last_name
        # get sex of admirer
        admirer_gender= 'Male' if relationship.source_person.gender == 'M'  else 'Female'
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
        if relationship.friendship_type == 0: # the crush can build the lineup from his/her friend list
            # if building from crush perspective, then exclude pulling from fb 
                # -the source person (they will get inserted manually)
                # anyone already on their crush list or their platonic friend list
            if exclude_facebook_ids == "":
                exclude_facebook_ids = "'" + str(relationship.source_person.username) + "'"
            else:
                exclude_facebook_ids = exclude_facebook_ids + "'" + str(relationship.source_person.username) + "'"
        
            fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (SELECT uid FROM family where profile_id=me())) AND NOT (uid2 IN (" + exclude_facebook_ids + "))) ) AND sex = '" + admirer_gender + "'  ORDER BY friend_count DESC LIMIT 9"
        else: # the admirer must build the lineup from his friend list
            if exclude_facebook_ids != "": # remove the trailing comma
                exclude_facebook_ids = exclude_facebook_ids[:-1]
            fql_query = "SELECT uid FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE (uid1 = me() AND NOT (uid2 IN (" + exclude_facebook_ids + ")) )) AND sex = '" + admirer_gender + "'  ORDER BY friend_count DESC LIMIT 9"
        print "fql_query string: " + str(fql_query)
        fql_query_results = urllib.urlopen('https://graph.facebook.com/fql?q=%s&access_token=%s' % (fql_query,builder_user.access_token))
        try:
            data = json.load(fql_query_results)['data']    
            if (len(data) < settings.MINIMUM_LINEUP_MEMBERS):
                if relationship.friendship_type == 0:
                    relationship.lineup_initialization_status=3
                else:
                    relationship.lineup_initialization_status=2
                relationship.save(update_fields=['lineup_initialization_status'])
                return      
            print "json data results for admirer: " + relationship.source_person.first_name + " " + relationship.source_person.last_name + " : " + str(data)
          
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
                LineupMembership.objects.create(position=index,lineup_member=relationship.source_person,relationship=relationship,decision=None)
                print "put crush in position: " + str(index) 
                index = index + 1            
                # create a lineup member with the given username      
             
            #pool.apply_async(create_new_lineup_user,[fql_user['uid'],builder_user.access_token,index,self],) 
            #create_new_lineup_user(fb_uid=fql_user['uid'],fb_access_token=builder_user.access_token,index=index,relationship=self)
            lineup_user = FacebookUser.objects.find_or_create_user(fb_id=fql_user['uid'],fb_access_token=builder_user.access_token,is_this_for_me=False)
            LineupMembership.objects.create(position=index,lineup_member=lineup_user,relationship=relationship,decision=None)
            
            index = index + 1
        # the following condition (to put admirer in last position) should not occur, but just in case let's handle it    
        if len(data)==admirer_position:
            LineupMembership.objects.create(position=len(data),lineup_member=relationship.source_person,relationship=relationship,decision=None)
      
        print "number lineup members: " + str(relationship.lineupmembership_set.count())
        
        # don't return until all lineup members have been completed (number of lineup memberships = len(data)+1
        relationship.lineup_initialization_status=1
        relationship.save(update_fields=['lineup_initialization_status'])
        
        return True

# details about each crush's secret admirer lineup (SAL)
class LineupMembership(models.Model):
    
    class Meta:
        # this allows the models to be broken into separate model files
        app_label = 'crush'
        
    objects = LineupManager()   
        
    # each lineup has many lineup members (10 by default) and each lineup member has only one lineup it belongs to (similar to blog entry)
    relationship = models.ForeignKey('CrushRelationship')
    lineup_member=models.ForeignKey('FacebookUser')
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