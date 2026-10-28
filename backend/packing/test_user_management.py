from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase, Client
from rest_framework.test import APIClient
from .models import Audit
from .user_management import save_user, role_for


class UserManagementTests(TestCase):
    def setUp(self):
        self.admin=get_user_model().objects.create_superuser('admin-test',password='Synthetic-Password-928!')
        self.client=APIClient();self.client.force_authenticate(self.admin)

    def payload(self,username='new-user',role='operador'):
        return {'username':username,'first_name':'Test','last_name':'User','email':'','role':role,'is_active':True,'password':'Synthetic-Password-713!'}

    def user(self,username,role='operador'):
        return save_user(self.admin,self.payload(username,role))

    def test_create_operator_with_only_capture_release_and_consult(self):
        response=self.client.post('/api/users/',self.payload(),format='json')
        self.assertEqual(response.status_code,201,response.data)
        user=get_user_model().objects.get(pk=response.data['id'])
        self.assertTrue(user.check_password('Synthetic-Password-713!'))
        self.assertEqual(user.get_all_permissions(),{'packing.consult','packing.capture','packing.release'})
        self.assertFalse(user.is_staff);self.assertFalse(user.is_superuser)
        self.assertNotIn('password',response.data)

    def test_planer_has_all_operational_permissions_and_can_manage_operators(self):
        planer=self.user('planer','planer')
        self.assertTrue(planer.has_perm('packing.plan'));self.assertTrue(planer.has_perm('packing.release'))
        self.client.force_authenticate(planer)
        self.assertEqual(self.client.get('/api/users/').status_code,200)
        self.assertEqual(self.client.post('/api/users/',self.payload('operator-two'),format='json').status_code,201)
        self.assertEqual(self.client.post('/api/users/',self.payload('bad-admin','admin'),format='json').status_code,403)
        self.assertEqual(self.client.patch(f'/api/users/{self.admin.pk}/',{'first_name':'Changed'},format='json').status_code,403)
        self.assertFalse(planer.is_staff)

    def test_operator_cannot_manage_accounts_or_planning(self):
        operator=self.user('operator')
        self.client.force_authenticate(operator)
        self.assertEqual(self.client.get('/api/users/').status_code,403)
        self.assertEqual(self.client.post('/api/users/',self.payload('nope'),format='json').status_code,403)
        self.assertEqual(self.client.patch(f'/api/users/{operator.pk}/',{'role':'admin'},format='json').status_code,403)
        self.assertEqual(self.client.post('/api/employees/',{'payroll':'1','name':'Nope'},format='json').status_code,403)

    def test_role_change_removes_old_permissions(self):
        planer=self.user('planer','planer')
        planer.user_permissions.add(Permission.objects.get(codename='plan'))
        updated=save_user(self.admin,{'role':'operador'},planer.pk)
        self.assertFalse(updated.has_perm('packing.plan'))
        self.assertTrue(updated.has_perm('packing.capture'));self.assertTrue(updated.has_perm('packing.release'))

    def test_disable_and_reset_password_preserve_user_and_role(self):
        operator=self.user('operator')
        result=self.client.patch(f'/api/users/{operator.pk}/',{'is_active':False,'password':'Changed-Secret-758!'},format='json')
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual(result.data['role'],'operador')
        operator.refresh_from_db()
        self.assertFalse(operator.is_active);self.assertTrue(operator.check_password('Changed-Secret-758!'))
        self.assertEqual(Audit.objects.filter(kind='user_update',object_id=str(operator.pk)).count(),1)
        self.assertNotIn('Changed-Secret',str(Audit.objects.last().data))

    def test_self_deactivation_or_role_change_is_rejected(self):
        for payload in [{'is_active':False},{'role':'operador'}]:
            response=self.client.patch(f'/api/users/{self.admin.pk}/',payload,format='json')
            self.assertEqual(response.status_code,400)
        self.admin.refresh_from_db();self.assertTrue(self.admin.is_active);self.assertTrue(self.admin.is_superuser)

    def test_duplicate_username_bad_role_and_weak_password(self):
        self.user('Taken')
        for payload in [self.payload('taken'),{**self.payload('weak'),'password':'12345678'},{**self.payload('invalid'),'role':'unknown'}]:
            self.assertEqual(self.client.post('/api/users/',payload,format='json').status_code,400)

    def test_staff_cannot_promote_without_operational_management_permission(self):
        user=get_user_model().objects.create_user('staff-only',is_staff=True)
        self.client.force_authenticate(user)
        self.assertEqual(self.client.get('/api/users/').status_code,403)

    def test_real_session_rechecks_access_after_deactivation(self):
        operator=self.user('operator')
        session_client=Client();session_client.force_login(operator)
        save_user(self.admin,{'is_active':False},operator.pk)
        self.assertFalse(session_client.get('/api/session/').json()['authenticated'])

    def test_own_password_change_keeps_session_and_password_out_of_audit(self):
        session_client=Client();session_client.force_login(self.admin)
        response=session_client.patch(f'/api/users/{self.admin.pk}/',data={'password':'Changed-Admin-897!'},content_type='application/json')
        self.assertEqual(response.status_code,200,response.content)
        self.assertTrue(session_client.get('/api/session/').json()['authenticated'])
        self.assertNotIn('Changed-Admin',str(Audit.objects.last().data))

    def test_management_requires_login_and_csrf(self):
        client=Client(enforce_csrf_checks=True)
        self.assertIn(client.get('/api/users/').status_code,[401,403])
        client.force_login(self.admin)
        self.assertEqual(client.post('/api/users/',self.payload()).status_code,403)

    def test_migrated_groups_have_expected_permissions(self):
        for name,permissions in [('Operador',{'consult','capture','release'}),('Planer',{'consult','capture','plan','release'})]:
            self.assertEqual(set(Group.objects.get(name=name).permissions.values_list('codename',flat=True)),permissions)
