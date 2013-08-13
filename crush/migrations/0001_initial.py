# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'InviteEmail'
        db.create_table(u'crush_inviteemail', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('relationship', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['crush.CrushRelationship'])),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('date_last_sent', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('is_for_crush', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('crush', ['InviteEmail'])

        # Adding model 'Purchase'
        db.create_table(u'crush_purchase', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('credit_total', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('price', self.gf('django.db.models.fields.DecimalField')(max_digits=7, decimal_places=2)),
            ('purchaser', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['crush.FacebookUser'])),
            ('purchased_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('tx', self.gf('django.db.models.fields.CharField')(max_length=250, null=True, blank=True)),
        ))
        db.send_create_signal('crush', ['Purchase'])

        # Adding model 'FacebookUser'
        db.create_table(u'crush_facebookuser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_superuser', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('access_token', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(default=u'U', max_length=1)),
            ('gender_pref', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('is_single', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('matchmaker_preference', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('is_underage', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('birthday_year', self.gf('django.db.models.fields.IntegerField')(max_length=4, null=True, blank=True)),
            ('age_pref_min', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('age_pref_max', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('site_credits', self.gf('django.db.models.fields.IntegerField')(default=100)),
            ('bNotify_crush_signup_reminder', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('bNotify_crush_responded', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('bNotify_new_admirer', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('bNotify_setup_response_received', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('processed_activated_friends_admirers', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal('crush', ['FacebookUser'])

        # Adding M2M table for field groups on 'FacebookUser'
        m2m_table_name = db.shorten_name(u'crush_facebookuser_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('facebookuser', models.ForeignKey(orm['crush.facebookuser'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['facebookuser_id', 'group_id'])

        # Adding M2M table for field user_permissions on 'FacebookUser'
        m2m_table_name = db.shorten_name(u'crush_facebookuser_user_permissions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('facebookuser', models.ForeignKey(orm['crush.facebookuser'], null=False)),
            ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
        ))
        db.create_unique(m2m_table_name, ['facebookuser_id', 'permission_id'])

        # Adding M2M table for field friends_with_admirers on 'FacebookUser'
        m2m_table_name = db.shorten_name(u'crush_facebookuser_friends_with_admirers')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_facebookuser', models.ForeignKey(orm['crush.facebookuser'], null=False)),
            ('to_facebookuser', models.ForeignKey(orm['crush.facebookuser'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_facebookuser_id', 'to_facebookuser_id'])

        # Adding M2M table for field friends_that_invited_me on 'FacebookUser'
        m2m_table_name = db.shorten_name(u'crush_facebookuser_friends_that_invited_me')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_facebookuser', models.ForeignKey(orm['crush.facebookuser'], null=False)),
            ('to_facebookuser', models.ForeignKey(orm['crush.facebookuser'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_facebookuser_id', 'to_facebookuser_id'])

        # Adding model 'PlatonicRelationship'
        db.create_table(u'crush_platonicrelationship', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('source_person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='crush_platonicrelationship_set_from_source', to=orm['crush.FacebookUser'])),
            ('target_person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='crush_platonicrelationship_set_from_target', to=orm['crush.FacebookUser'])),
            ('friendship_type', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=1)),
            ('updated_flag', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('rating', self.gf('django.db.models.fields.IntegerField')(default=None, max_length=1, null=True, blank=True)),
        ))
        db.send_create_signal('crush', ['PlatonicRelationship'])

        # Adding model 'CrushRelationship'
        db.create_table(u'crush_crushrelationship', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('source_person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='crush_crushrelationship_set_from_source', to=orm['crush.FacebookUser'])),
            ('target_person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='crush_crushrelationship_set_from_target', to=orm['crush.FacebookUser'])),
            ('friendship_type', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=1)),
            ('updated_flag', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('target_status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('target_platonic_rating', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('is_results_paid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('date_messaging_expires', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
            ('is_platonic_rating_paid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('date_invite_last_sent', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('lineup_initialization_status', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('lineup_initialization_date_started', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('is_lineup_paid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('date_lineup_started', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('date_lineup_finished', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('date_target_signed_up', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('date_target_responded', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('date_results_paid', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('display_id', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=60)),
            ('recommender_person_id', self.gf('django.db.models.fields.CharField')(default=None, max_length=30, null=True, blank=True)),
        ))
        db.send_create_signal('crush', ['CrushRelationship'])

        # Adding model 'SetupRelationship'
        db.create_table(u'crush_setuprelationship', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('source_person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='crush_setuprelationship_set_from_source', to=orm['crush.FacebookUser'])),
            ('target_person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='crush_setuprelationship_set_from_target', to=orm['crush.FacebookUser'])),
            ('friendship_type', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=1)),
            ('updated_flag', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('date_notification_last_sent', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('date_lineup_started', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('date_lineup_finished', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('date_setup_completed', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('display_id', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=60)),
        ))
        db.send_create_signal('crush', ['SetupRelationship'])

        # Adding model 'SetupRequestRelationship'
        db.create_table(u'crush_setuprequestrelationship', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('source_person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='crush_setuprequestrelationship_set_from_source', to=orm['crush.FacebookUser'])),
            ('target_person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='crush_setuprequestrelationship_set_from_target', to=orm['crush.FacebookUser'])),
            ('friendship_type', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=1)),
            ('updated_flag', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('crush', ['SetupRequestRelationship'])

        # Adding model 'LineupMember'
        db.create_table(u'crush_lineupmember', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['crush.FacebookUser'], null=True, blank=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('position', self.gf('django.db.models.fields.IntegerField')()),
            ('decision', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('relationship', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['crush.CrushRelationship'], null=True, blank=True)),
        ))
        db.send_create_signal('crush', ['LineupMember'])

        # Adding model 'SetupLineupMember'
        db.create_table(u'crush_setuplineupmember', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['crush.FacebookUser'], null=True, blank=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('position', self.gf('django.db.models.fields.IntegerField')()),
            ('decision', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('relationship', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['crush.SetupRelationship'], null=True, blank=True)),
            ('date_last_notified', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('lineup_member_attraction', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal('crush', ['SetupLineupMember'])


    def backwards(self, orm):
        # Deleting model 'InviteEmail'
        db.delete_table(u'crush_inviteemail')

        # Deleting model 'Purchase'
        db.delete_table(u'crush_purchase')

        # Deleting model 'FacebookUser'
        db.delete_table(u'crush_facebookuser')

        # Removing M2M table for field groups on 'FacebookUser'
        db.delete_table(db.shorten_name(u'crush_facebookuser_groups'))

        # Removing M2M table for field user_permissions on 'FacebookUser'
        db.delete_table(db.shorten_name(u'crush_facebookuser_user_permissions'))

        # Removing M2M table for field friends_with_admirers on 'FacebookUser'
        db.delete_table(db.shorten_name(u'crush_facebookuser_friends_with_admirers'))

        # Removing M2M table for field friends_that_invited_me on 'FacebookUser'
        db.delete_table(db.shorten_name(u'crush_facebookuser_friends_that_invited_me'))

        # Deleting model 'PlatonicRelationship'
        db.delete_table(u'crush_platonicrelationship')

        # Deleting model 'CrushRelationship'
        db.delete_table(u'crush_crushrelationship')

        # Deleting model 'SetupRelationship'
        db.delete_table(u'crush_setuprelationship')

        # Deleting model 'SetupRequestRelationship'
        db.delete_table(u'crush_setuprequestrelationship')

        # Deleting model 'LineupMember'
        db.delete_table(u'crush_lineupmember')

        # Deleting model 'SetupLineupMember'
        db.delete_table(u'crush_setuplineupmember')


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
            'gender': ('django.db.models.fields.CharField', [], {'default': "u'U'", 'max_length': '1'}),
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
            'matchmaker_preference': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'processed_activated_friends_admirers': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'site_credits': ('django.db.models.fields.IntegerField', [], {'default': '100'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'crush.inviteemail': {
            'Meta': {'object_name': 'InviteEmail'},
            'date_last_sent': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_for_crush': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
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
        },
        'crush.setuplineupmember': {
            'Meta': {'ordering': "['position']", 'object_name': 'SetupLineupMember'},
            'date_last_notified': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'decision': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lineup_member_attraction': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {}),
            'relationship': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['crush.SetupRelationship']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['crush.FacebookUser']", 'null': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        'crush.setuprelationship': {
            'Meta': {'object_name': 'SetupRelationship'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_lineup_finished': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_lineup_started': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_notification_last_sent': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'date_setup_completed': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'display_id': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '60'}),
            'friendship_type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source_person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'crush_setuprelationship_set_from_source'", 'to': "orm['crush.FacebookUser']"}),
            'target_person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'crush_setuprelationship_set_from_target'", 'to': "orm['crush.FacebookUser']"}),
            'updated_flag': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'crush.setuprequestrelationship': {
            'Meta': {'object_name': 'SetupRequestRelationship'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'friendship_type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source_person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'crush_setuprequestrelationship_set_from_source'", 'to': "orm['crush.FacebookUser']"}),
            'target_person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'crush_setuprequestrelationship_set_from_target'", 'to': "orm['crush.FacebookUser']"}),
            'updated_flag': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        }
    }

    complete_apps = ['crush']