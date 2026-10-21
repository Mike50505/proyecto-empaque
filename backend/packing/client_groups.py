"""Canonical customer groups backed by exact Universo Ramos customer names."""
import re
from django.db.models import Q


CLIENT_GROUPS = ('DAIKIN', 'LENNOX 1', 'MESA MTY', 'RHEEM')


def _key(value):
    return re.sub(r'\s+', ' ', str(value or '').strip()).casefold()


_ALIASES = {
    'daikin': 'DAIKIN',
    'lennox 1': 'LENNOX 1',
    'mesa mty / brazeway': 'MESA MTY',
    'mesa mty / carrier': 'MESA MTY',
    'mesa mty / carrier a': 'MESA MTY',
    'mesa mty / carrier d': 'MESA MTY',
    'mesa mty / lennox 2': 'MESA MTY',
    'mesa mty / trane': 'MESA MTY',
    'rheem cip-3501': 'RHEEM',
    'rheem falcon': 'RHEEM',
    'rheem niples': 'RHEEM',
    'rheem transferencia': 'RHEEM',
}

_GROUP_MEMBERS = {
    'DAIKIN': ('DAIKIN',),
    'LENNOX 1': ('LENNOX 1',),
    'MESA MTY': ('MESA MTY', 'MESA MTY / BRAZEWAY', 'MESA MTY / CARRIER', 'MESA MTY / CARRIER A', 'MESA MTY / CARRIER D', 'MESA MTY / LENNOX 2', 'MESA MTY / TRANE'),
    'RHEEM': ('RHEEM', 'RHEEM CIP-3501', 'RHEEM FALCON', 'RHEEM NIPLES', 'RHEEM TRANSFERENCIA'),
}


def client_group(value):
    """Return the displayed group for a known official customer, else its clean name."""
    clean = re.sub(r'\s+', ' ', str(value or '').strip())
    return _ALIASES.get(_key(clean), clean)


def client_aliases(value):
    group = client_group(value)
    members = _GROUP_MEMBERS.get(group)
    return tuple(members) if members else (str(value or '').strip(),)


def client_filter(field, value):
    query = Q(pk__in=[])  # An empty disjunction stays safely false.
    for alias in client_aliases(value):
        query |= Q(**{field + '__iexact': alias})
    return query
