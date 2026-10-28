from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError
from . import services as s

ROLE_PERMISSIONS = {
    'planer': ('Planer', ['consult', 'capture', 'plan', 'release']),
    'operador': ('Operador', ['consult', 'capture', 'release']),
}


def role_for(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'admin'
    groups = {group.name for group in user.groups.all()}
    if groups.intersection({'Planer', 'Planeación'}) or user.has_perm('packing.plan'):
        return 'planer'
    if groups.intersection({'Operador', 'Calidad'}) or user.has_perm('packing.capture') or user.has_perm('packing.release'):
        return 'operador'
    return None


def can_manage_users(user):
    return user.is_authenticated and user.is_active and (user.is_superuser or user.has_perm('packing.plan'))


def require_management(actor):
    if not can_manage_users(actor):
        raise PermissionDenied('No tienes permiso para administrar usuarios.')


def serialize_user(user, actor):
    return {
        'id': user.pk, 'username': user.username, 'first_name': user.first_name,
        'last_name': user.last_name, 'email': user.email, 'is_active': user.is_active,
        'role': role_for(user), 'is_self': user.pk == actor.pk,
        'can_edit': actor.is_superuser or not user.is_superuser,
    }


def ensure_group(role):
    name, codes = ROLE_PERMISSIONS[role]
    group, _ = Group.objects.get_or_create(name=name)
    group.permissions.set(Permission.objects.filter(content_type__app_label='packing', codename__in=codes))
    return group


@transaction.atomic
def save_user(actor, data, pk=None):
    require_management(actor)
    s.lock_ledger()
    User = get_user_model()
    if pk is None:
        user = User()
        before = None
    else:
        user = User.objects.select_for_update().get(pk=pk)
        before = serialize_user(user, actor)
        if user.is_superuser and not actor.is_superuser:
            raise PermissionDenied('Solo Admin puede modificar cuentas Admin.')
    role = data.get('role', role_for(user) if pk else 'operador')
    if role not in ['admin', *ROLE_PERMISSIONS]:
        raise ValidationError({'role': 'Selecciona Admin, Planer u Operador.'})
    if role == 'admin' and not actor.is_superuser:
        raise PermissionDenied('Solo Admin puede asignar el rol Admin.')
    active = data.get('is_active', user.is_active)
    if not isinstance(active, bool):
        raise ValidationError({'is_active': 'El estado debe ser activo o inactivo.'})
    if pk == actor.pk and (not active or role != role_for(actor)):
        raise ValidationError('No puedes desactivar tu propia cuenta ni cambiar tu propio rol.')
    if pk and user.is_active and user.is_superuser and (not active or role != 'admin'):
        if not User.objects.filter(is_active=True, is_superuser=True).exclude(pk=pk).exists():
            raise ValidationError('Debe permanecer al menos una cuenta Admin activa.')
    for field in ['username', 'first_name', 'last_name', 'email']:
        value = data.get(field, getattr(user, field, ''))
        if not isinstance(value, str):
            raise ValidationError({field: 'Introduce un texto válido.'})
        setattr(user, field, value.strip())
    if not user.username:
        raise ValidationError({'username': 'El usuario es obligatorio.'})
    if User.objects.filter(username__iexact=user.username).exclude(pk=pk).exists():
        raise ValidationError({'username': 'Este nombre de usuario ya existe.'})
    password = data.get('password', '')
    if not isinstance(password, str):
        raise ValidationError({'password': 'Introduce una contraseña válida.'})
    if not pk and not password:
        raise ValidationError({'password': 'La contraseña es obligatoria para crear la cuenta.'})
    user.is_active = active
    user.is_superuser = role == 'admin'
    user.is_staff = role == 'admin'
    try:
        user.full_clean(exclude=['password'])
        if password:
            validate_password(password, user)
            user.set_password(password)
    except DjangoValidationError as error:
        raise ValidationError(getattr(error, 'message_dict', None) or error.messages)
    user.save()
    user.groups.set([] if role == 'admin' else [ensure_group(role)])
    user.user_permissions.clear()
    for cache in ['_perm_cache', '_user_perm_cache', '_group_perm_cache']:
        user.__dict__.pop(cache, None)
    after = serialize_user(user, actor)
    s.audit(actor, 'user_create' if pk is None else 'user_update', user,
            'Administración de usuarios desde Empaques', before=before, after=after,
            password_changed=bool(password))
    return user
