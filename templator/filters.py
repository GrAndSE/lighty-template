"""Package provides template filters management
"""


def register(filter_func):
    '''Mark for register filter in manager on module loading
    '''
    filter_func._template_filter = True
    return filter_func


class FilterManager(object):
    """Class used for filters manipulations
    """
    __slots__ = ('apply', 'filters', 'is_filter_exists', )

    default = None

    def __init__(self):
        """Create new tag managet instance
        """
        super(FilterManager, self).__init__()
        self.filters = {}
        if not self.__class__.default:
            self.__class__.default = self

    def get_filter(self, name):
        """Check is filter exists
        """
        if name in self.filters:
            return self.filters[name]
        elif name in self.__class__.default.filters:
            return self.__class__.default.filters[name]
        raise LookupError("Filter '%s' is not registered" % name)

    def apply(self, filter_name, value, args, arg_types, context):
        '''Apply filter to values
        '''
        filter_func = self.get_filter(filter_name)
        new_args = []
        i = 0
        while i < len(args):
            new_args.append(arg_types[i] and args[i] or context[args[i]])
            i += 1
        return filter_func(value, *new_args)

    def load(self, module_name):
        '''Load module into manager. Retrieve all the registered filters and
        put them into list.
        '''
        import importlib
        module = importlib.import_module(module_name)
        for member_name in dir(module):
            member = getattr(module, member_name)
            if callable(member) and hasattr(member, '_template_filter'):
                self.filters[member_name] = member

    def __deepcopy__(self, obj):
        '''Override deepcopy processing
        '''
        result = FilterManager()
        result.filters = self.filters.copy()
        return result

FilterManager()
