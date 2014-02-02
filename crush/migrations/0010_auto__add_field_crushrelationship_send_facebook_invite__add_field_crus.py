# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'CrushRelationship.send_facebook_invite'
        db.add_column(u'crush_crushrelationship', 'send_facebook_invite',
                      self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'CrushRelationship.date_facebook_invite_last_sent'
        db.add_column(u'crush_crushrelationship', 'date_facebook_invite_last_sent',
                      self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'CrushRelationship.send_facebook_invite'
        db.delete_column(u'crush_crushrelationship', 'send_facebook_invite')

        # Deleting field 'CrushRelationship.date_facebook_invite_last_sent'
        db.delete_column(u'crush_crushrelationship', 'date_facebook_invite_last_sent')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'crush.crushrelationship': {
            'Meta': {'object_name': 'CrushRelationship'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_facebook_invite_last_sent': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_invite_last_sent': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_lineup_expires': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_lineup_finished': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_lineup_started': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_messaging_expires': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_results_paid': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_source_last_notified': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_target_responded': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_target_signed_up': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'display_id': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '60'}),
            'friendship_type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_lineup_paid': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_platonic_rating_paid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_results_paid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lineup_auto_completed': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'lineup_initialization_date_started': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'lineup_initialization_status': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'send_facebook_invite': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'source_person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'crush_crushrelationship_set_from_source'", 'to': "orm['crush.FacebookUser']"}),
            'target_person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'crush_crushrelationship_set_from_target'", 'to': "orm['crush.FacebookUser']"}),
            'target_platonic_rating': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'target_status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'updated_flag': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'crush.facebookuser': {
            'Meta': {'object_name': 'FacebookUser'},
            'access_token': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'bNotify_crush_signup_reminder': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'bNotify_lineup_expiration_warning': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'bNotify_new_admirer': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'crush_targets': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'admirer_set'", 'symmetrical': 'False', 'through': "orm['crush.CrushRelationship']", 'to': "orm['crush.FacebookUser']"}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_twitter_invite_last_sent': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'friends_that_invited_me': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'friends_that_invited_me_set'", 'blank': 'True', 'to': "orm['crush.FacebookUser']"}),
            'friends_with_admirers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'friends_with_admirers_set'", 'blank': 'True', 'to': "orm['crush.FacebookUser']"}),
            'gender': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '1', 'blank': 'True'}),
            'gender_pref': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_single': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_underage': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'just_friends_targets': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'platonic_friend_set'", 'symmetrical': 'False', 'through': "orm['crush.PlatonicRelationship']", 'to': "orm['crush.FacebookUser']"}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'processed_activated_friends_admirers': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'site_credits': ('django.db.models.fields.IntegerField', [], {'default': '100'}),
            'twitter_username': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'crush.inviteemail': {
            'Meta': {'object_name': 'InviteEmail'},
            'date_last_sent': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_for_crush': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'mf_recipient_fb_username': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'mf_recipient_first_name': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'relationship': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['crush.CrushRelationship']"})
        },
        'crush.lineupmember': {
            'Meta': {'ordering': "['position']", 'object_name': 'LineupMember'},
            'decision': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {}),
            'relationship': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['crush.CrushRelationship']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['crush.FacebookUser']", 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        'crush.pasttwitterusername': {
            'Meta': {'object_name': 'PastTwitterUsername'},
            'date_twitter_invite_last_sent': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'twitter_username': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['crush.FacebookUser']"})
        },
        'crush.platonicrelationship': {
            'Meta': {'object_name': 'PlatonicRelationship'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'friendship_type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rating': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'source_person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'crush_platonicrelationship_set_from_source'", 'to': "orm['crush.FacebookUser']"}),
            'target_person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'crush_platonicrelationship_set_from_target'", 'to': "orm['crush.FacebookUser']"}),
            'updated_flag': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'crush.purchase': {
            'Meta': {'object_name': 'Purchase'},
            'credit_total': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '7', 'decimal_places': '2'}),
            'purchased_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'purchaser': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['crush.FacebookUser']"}),
            'tx': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['crush']