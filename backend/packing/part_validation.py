"""Operational identities come from the synchronized Universo Ramos catalog."""
from rest_framework.exceptions import ValidationError
from .models import Part
from .client_groups import client_group


def customer_key(value):
    return str(value or '').strip().casefold()


def validate_part_customer(part, client):
    if not part.universe_id or part.provisional:
        raise ValidationError(f'La pieza {part.number} no está validada en Universo Ramos. Sincroniza el catálogo; no se permiten piezas provisionales.')
    if not part.customer.strip():
        raise ValidationError(f'Universo no tiene un cliente confirmado para la pieza {part.number}. Sincroniza el catálogo antes de continuar.')
    if customer_key(client_group(part.customer))!=customer_key(client_group(client)):
        raise ValidationError(f'La pieza {part.number} pertenece a {part.customer} en Universo Ramos y no puede asignarse a {client}.')
    if part.attributes.get('active') is False:
        raise ValidationError(f'La pieza {part.number} está inactiva en Universo Ramos.')
    return part


def resolve_part(number, client, selected_id=None):
    candidates=list(Part.objects.filter(number__iexact=str(number).strip()))
    if selected_id is not None:
        selected=next((part for part in candidates if str(part.pk)==str(selected_id)),None)
        if selected is None:
            raise ValidationError('La pieza seleccionada no coincide con el número de parte del archivo.')
        return validate_part_customer(selected,client)
    matching=[part for part in candidates if customer_key(client_group(part.customer))==customer_key(client_group(client)) and part.universe_id and not part.provisional and part.attributes.get('active') is not False]
    if len(matching)==1: return matching[0]
    if len(matching)>1:
        raise ValidationError(f'La pieza {number} tiene varias identidades de Universo para {client}; selecciona la identidad correcta.')
    official=[part for part in candidates if part.universe_id and not part.provisional]
    if official:
        customers=', '.join(sorted({part.customer for part in official if part.customer}))
        if all(customer_key(client_group(part.customer))!=customer_key(client_group(client)) for part in official):
            raise ValidationError(f'La pieza {number} pertenece a {customers or "un cliente sin confirmar"} en Universo Ramos, no a {client}.')
        validate_part_customer(official[0],client)
    raise ValidationError(f'La pieza {number} no está disponible para {client} en el catálogo validado de Universo Ramos. Sincroniza el catálogo; no se permite crearla como provisional.')


def validate_program(program):
    for line in program.lines.select_related('part'):
        validate_part_customer(line.part,program.client)
