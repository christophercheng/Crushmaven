# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Message'
        db.create_table(u'postman_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=120)),
            ('body', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'sent_messages', null=True, to=orm['crush.FacebookUser'])),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'received_messages', null=True, to=orm['crush.FacebookUser'])),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'next_messages', null=True, to=orm['postman.Message'])),
            ('thread', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'child_messages', null=True, to=orm['postman.Message'])),
            ('sent_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('read_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('replied_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('sender_archived', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('recipient_archived', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('sender_deleted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('recipient_deleted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('moderation_status', self.gf('django.db.models.fields.CharField')(default='p', max_length=1)),
            ('moderation_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'moderated_messages', null=True, to=orm['crush.FacebookUser'])),
            ('moderation_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('moderation_reason', self.gf('django.db.models.fields.CharField')(max_length=120, blank=True)),
        ))
        db.send_create_signal(u'postman', ['Message'])


    def backwards(self, orm):
        # Deleting model 'Message'
        db.delete_table(u'postman_message')


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
            'date_invite_last_sent': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_lineup_finished': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_lineup_started': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_messaging_expires': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_results_paid': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_target_responded': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_target_signed_up': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'display_id': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '60'}),
            'friendship_type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_lineup_paid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_platonic_rating_paid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_results_paid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lineup_initialization_date_started': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'lineup_initialization_status': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'recommender_person_id': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'source_person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'crush_crushrelationship_set_from_source'", 'to': "orm['crush.FacebookUser']"}),
            'target_person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'crush_crushrelationship_set_from_target'", 'to': "orm['crush.FacebookUser']"}),
            'target_platonic_rating': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'target_status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'updated_flag': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'crush.facebookuser': {
            'Meta': {'object_name': 'FacebookUser'},
            'access_token': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'age_pref_max': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'age_pref_min': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'bNotify_crush_responded': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'bNotify_crush_signup_reminder': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'bNotify_new_admirer': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'bNotify_setup_response_received': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'birthday_year': ('django.db.models.fields.IntegerField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'crush_targets': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'admirer_set'", 'symmetrical': 'False', 'through': "orm['crush.CrushRelationship']", 'to': "orm['crush.FacebookUser']"}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'friends_that_invited_me': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'friends_that_invited_me_set'", 'blank': 'True', 'to': "orm['crush.FacebookUser']"}),
            'friends_with_admirers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'friends_with_admirers_set'", 'blank': 'True', 'to': "orm['crush.FacebookUser']"}),
            'gender': ('django.db.models.fields.CharField', [], {'default': "u'M'", 'max_length': '1'}),
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
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
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
        u'postman.message': {
            'Meta': {'ordering': "[u'-sent_at', u'-id']", 'object_name': 'Message'},
            'body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderation_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'moderated_messages'", 'null': 'True', 'to': "orm['crush.FacebookUser']"}),
            'moderation_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'moderation_reason': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            'moderation_status': ('django.db.models.fields.CharField', [], {'default': "'p'", 'max_length': '1'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'next_messages'", 'null': 'True', 'to': u"orm['postman.Message']"}),
            'read_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'received_messages'", 'null': 'True', 'to': "orm['crush.FacebookUser']"}),
            'recipient_archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient_deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'replied_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'sent_messages'", 'null': 'True', 'to': "orm['crush.FacebookUser']"}),
            'sender_archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sender_deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sent_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'child_messages'", 'null': 'True', 'to': u"orm['postman.Message']"})
        }
    }

    complete_apps = ['postman']