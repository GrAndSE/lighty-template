""" Pakage provides method to working with templates """
import xml.sax
import StringIO
#try:
#    import cStringIO as StringIO
#except:
#    try:
#        import StringIO
#    except:
#        import io as StringIO

from loaders import TemplateLoader


class TagGroup(object):
    """Class representing tag number 
    """

    def __init__(self, name):
        """Init tag group element
        """
        super(TagGroup, self).__init__()
        self.name   = name
        self.childs = []

    def exec_cmd(self, context):
        for command in self.childs:
            yield command(context)

    def render(self, context):
        result = StringIO.StringIO()
        for cmd in self.exec_cmd(context):
            result.write(cmd)
        return result.getvalue()


class Template(xml.sax.ContentHandler, TagGroup):
    """ Class represents template """

    def __init__(self, loader=TemplateLoader(), name="unnamed"):
        """ Create new template instance """
        super(Template, self).__init__()
        self.loader = loader
        self.name   = name
        self.loader.register(name, self)

    @staticmethod
    def variable(name):
        def print_value(context):
            return context[name]
        return print_value

    @staticmethod
    def constant(value):
        def print_value(context):
            return value
        return print_value

    def startElement(self, name, attrs):
        print name, attrs

    def __str__(self):
        """Return string representation
        """
        return self.execute({})

    def parse(self, input):
        if isinstance(input, str):
            xml.sax.parseString(input, self)
        else:
            xml.sax.parse(input, self)
