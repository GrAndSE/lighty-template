'''Methods for context accessing
'''
from functools import reduce


def get_field(obj, field):
    if hasattr(obj, field):
        return getattr(obj, field)
    elif hasattr(obj, '__getitem__') and hasattr(obj, '__contains__'):
        return obj[field]
    raise Exception('Could not get %s from %s' % (field, obj))


def resolve(var_name, context):
    if '.' in var_name:
        fields = var_name.split('.')
        return reduce(get_field, fields[1:], context.get(fields[0], None))
    return context.get(var_name, None)
