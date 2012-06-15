'''Methods for context accessing
'''
import functools


def get_field(obj, field):
    '''Get field from object or item from dictionary
    '''
    if hasattr(obj, field):
        return getattr(obj, field)
    elif hasattr(obj, '__getitem__') and hasattr(obj, '__contains__'):
        return obj[field]
    raise AttributeError('Could not get %s from %s' % (field, obj))


def resolve(var_name, context):
    '''Resolve a value for variable's name from context
    '''
    if '.' in var_name:
        fields = var_name.split('.')
        return functools.reduce(get_field, fields[1:],
                                context.get(fields[0], None))
    return context.get(var_name, None)
