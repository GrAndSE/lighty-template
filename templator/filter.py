"""Package provides template filters management
"""
import collections


class FilterManager(object):
    """Class used for filters manipulations
    """
    __slots__ = ('apply', 'filters', 'is_filter_exists', )

    _managers = None

    def __init__(self):
        """Create new tag managet instance
        """
        cls = self.__class__
        if not cls._managers:
            cls._managers = collections.deque()
        super(FilterManager, self).__init__()
        self.filters = {}
        cls._managers.append(self)

    @classmethod
    def create_manager(cls):
        '''Create new FilterManager
        '''
        cls()

    @classmethod
    def destroy_manager(cls):
        '''Delete filter manager
        '''
        cls._managers.pop()

    @classmethod
    def current(cls):
        '''Get current manager
        '''
        return cls._managers[-1]

    @classmethod
    def default(cls):
        '''Get default manager
        '''
        return cls._managers[0]

    @classmethod
    def get_filter(cls, name):
        """Check is filter exists
        """
        if name in cls.current().filters:
            return cls.current().filters[name]
        elif name in cls.default().filters:
            return cls.default().filters[name]
        raise LookupError("Filter '%s' is not registered" % name)

    @classmethod
    def register(cls, filter):
        '''Register filter in manager
        '''
        cls.current().filters[filter.__name__] = filter

    @classmethod
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

FilterManager.create_manager()
