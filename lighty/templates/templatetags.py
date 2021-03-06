"""Basic template tags library
"""
import collections
import copy
from functools import partial
import itertools

from .context import resolve
from .tag import tag_manager, parse_token
from .template import LazyTemplate, Template


def exec_with_context(func, context=None, context_diff=None):
    '''Execute function with context switching
    '''
    if not context:
        context = {}
    if not context_diff:
        context_diff = {}
    old_values = dict([(var_name,
                        context[var_name] if var_name in context else None)
                       for var_name in context_diff])
    context.update(context_diff)
    result = func(context)
    context.update(old_values)
    return result


def exec_block(block_contents, context):
    '''Helper function that can be used in block tags to execute inner template
    code on a specified context
    '''
    return "".join([command(context) for command in block_contents])


def get_parent_blocks(template):
    '''Get parent blocks
    '''
    if not hasattr(template.parent, 'blocks'):
        if isinstance(template.parent, LazyTemplate):
            template.parent.prepare()
            return get_parent_blocks(template)
        else:
            template.parent.blocks = {}
    return template.parent.blocks


def find_command(command, template):
    '''Find command in commands list
    '''
    if command in template.commands:
        return template.commands.index(command), template
    else:
        for cmd in template.commands:
            if isinstance(cmd, Template):
                index, tmpl = find_command(command, cmd)
                if index is not None:
                    return index, tmpl
    return None, template


def replace_command(template, command, replacement):
    '''Search for command in commands list and replace it with a new one
    '''
    index, tmpl = find_command(command, template)
    if index is None:
        template.commands.append(replacement)
    else:
        tmpl.commands[index] = replacement


def block(token, block_contents, template, loader):
    """Block tag. This tag provides method to modify chilren template for
    template inheritance.

    As example for base template called 'base.html'

    .. code-block:: html

        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            {% block head %}{% endblock %}
        </head>
        <body>
            {% block content %}Some contents{% endblock %}
        </body>
        </html>

    and extended template called 'extended.html'

    .. code-block:: html

        {% extend "base.html" %}
        {% block head %}<style></style>{% endblock %}
        {% block content %}<h1>Hello, world!</h1>{% endblock %}

    we can execute extended template with additional context::

        template = loader.get_template('extended.html')
        template({'title': 'Hello'})

    to get something similar to this:

    .. code-block:: html

        <!DOCTYPE html>
        <html>
        <head>
            <title>%s</title>
            <style></style>
        </head>
        <body>
            <h1>Hello, world!</h1>
        </body>
        </html>
    """
    # Create inner template for blocks
    tmpl = Template(name='blocks-' + token, loader=loader)
    tmpl.commands = block_contents

    # Add template block into list
    if not hasattr(template, 'blocks'):
        template.blocks = {}
    is_new = token not in template.blocks
    template.blocks[token] = tmpl

    # Add function that executes inner template into commands
    if is_new:
        return template.blocks[token]
    else:
        replace_command(template, template.parent.blocks[token], tmpl)
        return lambda context: ''

tag_manager.register(
        name='block',
        tag=block,
        is_block_tag=True,
        context_required=False,
        template_required=True,
        loader_required=True,
        is_lazy_tag=False
)


def extend(token, template, loader):
    """Tag used to create tamplates iheritance. To get more information about
    templates inheritance see :func:`block`.
    """
    tokens = parse_token(token)[0]
    template.parent = loader.get_template(tokens[0])
    if not hasattr(template, 'blocks'):
        template.blocks = get_parent_blocks(template).copy()
    else:
        template.blocks.update(get_parent_blocks(template).copy())
    template.commands.extend(copy.deepcopy(template.parent.commands))
    return None

tag_manager.register(
        name='extend',
        tag=extend,
        template_required=True,
        loader_required=True,
        is_lazy_tag=False
)


def include(token, context, loader):
    '''This tag includes another template inside current position

    Example:

    .. code-block:: html

        <html>
        <head>
            {% include "includes/stylesheets.html" %}
        </head>
        <body>
            {% include "includes/top_nav.html" %}
            {% block content %}{% endblock %}
        </body>
    '''
    tokens, _ = parse_token(token)
    template = loader.get_template(tokens[0])
    return exec_with_context(template, context, {})

tag_manager.register(
        name='include',
        tag=include,
        is_block_tag=False,
        is_lazy_tag=True,
        context_required=True,
        template_required=False,
        loader_required=True
)


def spaceless(token, block_contents, context):
    """This tag removes unused spaces

    Template::

        {% spaceless %}
            Some
                    text
        {% endspaceless %}

    will be rendered to::

        Some text
    """
    results = [command(context).split('\n') for command in block_contents]
    return "".join([line.lstrip() for line in itertools.chain(*results)])

tag_manager.register(
        name='spaceless',
        tag=spaceless,
        is_block_tag=True,
        context_required=True,
        template_required=False,
        loader_required=False,
        is_lazy_tag=True
)


def with_tag(token, block_contents, context):
    """With tag can be used to set the shorter name for variable used few times

    Example:

    .. code-block:: html

        {% with request.context.user.name as user_name %}
            <h1>{{ user_name }}'s profile</h1>
            <span>Hello, {{ user_name }}</span>
            <form action="update_profile" method="post">
                <label>Your name:</label>
                <input type="text" name="user_name" value="{{ user_name }}" />
                <input type="submit" value="Update profile" />
            </form>
        {% endwith %}
    """
    data_field, _, var_name = token.split(' ')
    value = resolve(data_field, context)
    return exec_with_context(partial(exec_block, block_contents), context,
                             {var_name: value})

tag_manager.register(
        name='with',
        tag=with_tag,
        is_block_tag=True,
        context_required=True,
        template_required=False,
        loader_required=False,
        is_lazy_tag=True
)


def if_tag(token, block_contents, context):
    """If tag can brings some logic into template. Now it's has very simple
    implementations that only checks is variable equivalent of True. There is
    no way to add additional logic like comparisions or boolean expressions.
    Hope I'll add this in future.

    Example::

        {% if user.is_authenticated %}Hello, {{ user.name }}!{% endif %}

    returns for user = {'is_authenticated': True, 'name': 'Peter'}::

        Hello, Peter!

    TODO:

        - add else
        - add conditions
    """
    if resolve(token, context):
        return exec_block(block_contents, context)
    return ''

tag_manager.register(
        name='if',
        tag=if_tag,
        is_block_tag=True,
        context_required=True,
        template_required=False,
        loader_required=False,
        is_lazy_tag=True
)


class Forloop(object):
    '''Class for executing block in loop with a context update
    '''

    def __init__(self, var_name, values, block_contents):
        self.var_name = var_name
        self.values = values
        self.block = block_contents
        self.counter0 = 0

    @property
    def total(self):
        '''Get number of iterations
        '''
        return len(self.values)

    @property
    def last(self):
        '''Check is current iteration last iteration
        '''
        return not self.counter0 < self.total

    @property
    def first(self):
        '''Check is current iteration first iteration
        '''
        return self.counter0 == 0

    @property
    def counter(self):
        '''Get the number of current iteration iteration starting from 1
        '''
        return self.counter0 + 1

    def __call__(self, context):
        '''Get all the iterations joined
        '''
        values = enumerate(self.values)
        return "".join([exec_block(self.block, context)
                        for self.counter0, context[self.var_name] in values])


def for_tag(token, block_contents, context):
    """For tag used to make loops over all the iterator-like objects.

    Example::

        {% for a in items %}{{ a }}{% endfor %}

    returns for items = [1, 2, 3]::

        123

    Also forloop variable will be added into scope. It contains few flags can
    be used to render customized templates:

    .. code-block:: html

        {% for a in items %}
            {% spaceless %}<span
                    {% if forloop.first %} class="first"{% endif %}
                    {% if forloop.last %} class="last"{% endif %}>
                {{ forloop.counter0 }}.
                {{ forloop.counter }} from {{ forloop.total }}
            </span>{% endspaceless %}
        {% endfor %}

    returns:

    .. code-block:: html

        <span class="first">0. 1 from 3</span>
        <span>1. 2 from 3</span>
        <span class="last">2. 3 from 3</span>

    """
    var_name, _, data_field = token.split(' ')
    values = resolve(data_field, context)
    # Check values
    if not isinstance(values, collections.Iterable):
        raise ValueError('%s: "%s" is not iterable' % (data_field, values))
    # execute inline forloop
    forloop = Forloop(var_name, values, block_contents)
    return exec_with_context(forloop, context, {'forloop': forloop})

tag_manager.register(
        name='for',
        tag=for_tag,
        is_block_tag=True,
        context_required=True,
        template_required=False,
        loader_required=False,
        is_lazy_tag=True
)
