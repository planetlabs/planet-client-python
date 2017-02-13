'''
Generate CLI reference ReST for Sphinx. Write the file cli/reference.rst

Ideally, this would be more tightly integrated with Sphinx (as an extension),
but this 'works' for now.
'''
from planet import scripts
from os import path

root = path.dirname(__file__)
dest = path.join(root, 'cli')


def h(text, type='-'):
    return '%s\n%s\n' % (text, type * len(text))


def cmd_ref(cmd):
    return 'cli-command-%s' % cmd.name


def help_block(e, cmd):
    ctx = scripts.click.Context(cmd)
    e.e('.. code-block:: none')
    e.write('    ' + ctx.get_help().replace('\n', '\n    '))
    e.e('')


def list_row(e, row):
    e.write('   * - %s\n' % row[0])
    for r in row[1:]:
        parts = [''] if not r else r.split('\n')
        e.write('     - %s\n' % parts[0])
        if len(parts) > 1:
            e.write('\n')
            e.write('       ``%s``' % ' '.join(parts[1:]))
            e.write('\n')


def param_block(e, cmd):
    params = [p for p in cmd.params
              if isinstance(p, scripts.click.core.Option)]
    if not params:
        return
    e.write('.. list-table:: Options\n')
    e.write('   :widths: 10 90\n')
    e.write('   :header-rows: 1\n\n')
    list_row(e, ('Name', 'Description'))
    for p in params:
        list_row(e, (p.name, p.help))


def generate_cli_reference(e):
    e.e('.. THIS IS A GENERATED FILE')
    e.e(h('CLI Reference', '='))

    e.e(h('General Options'))
    for p in scripts.cli.params:
        e.e('``--%s``\n   %s\n\n' % (p.name, p.help))

    e.e(h('Commands'))
    commands = sorted(scripts.cli.commands.values(),
                      lambda a, b: cmp(a.name, b.name))
    for cmd in commands:
        e.e(':ref:`%s` %s\n\n' % (cmd_ref(cmd), cmd.short_help))

    for cmd in commands:
        e.e('.. index:: %s' % cmd.name)
        e.e('.. _%s:\n' % cmd_ref(cmd))
        e.e(h(cmd.name, '.'))
        e.e(cmd.help)
        ctx = scripts.click.Context(cmd)
        ctx.info_name = cmd.name
        e.e(ctx.get_usage())
        param_block(e, cmd)


class E(object):
    def __init__(self, fp):
        self.fp = fp

    def write(self, t):
        self.fp.write(t)

    def e(self, l):
        self.fp.write('%s\n\n' % l)


if __name__ == '__main__':
    with open(path.join(dest, 'reference.rst'), 'w') as fp:
        generate_cli_reference(E(fp))
