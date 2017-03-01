'''
Generate CLI reference ReST for Sphinx. Write the file cli/reference.rst

Ideally, this would be more tightly integrated with Sphinx (as an extension),
but this 'works' for now.
'''
import click
from planet import scripts
from planet.scripts.types import metavar_docs
from os import path
import re

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
        for p in parts[1:]:
            e.write('\n       ' + p)
        e.write('\n')


def param_block(e, cmd):
    params = [p for p in cmd.params
              if isinstance(p, click.core.Option)]
    if not params:
        return
    e.write('.. list-table:: Options\n')
    e.write('   :widths: 10 80 10\n')
    e.write('   :header-rows: 1\n\n')
    list_row(e, ('Name', 'Description', 'Format'))
    for p in params:
        metavar = p.make_metavar()
        # @todo enable once metavar target generation in place
        if metavar in metavar_docs:
            target = metavar.replace(' ', '-').replace('...', '')
            link = ':ref:`cli-metavar-%s`' % (target.lower())
        else:
            link = metavar
        desc = p.help
        if p.default:
            desc = desc + '\nDEFAULT: `%s`' % p.default
        list_row(e, (p.name, desc, link))


def generate_cli_reference(e):
    e.e('.. THIS IS A GENERATED FILE')
    e.e(h('CLI Reference', '='))
    e.e('.. include:: _reference_forward.rst')

    general = [cmd for cmd in scripts.main.commands.values()
               if not hasattr(cmd, 'commands')]
    groups = [cmd for cmd in scripts.main.commands.values()
              if hasattr(cmd, 'commands')]

    e.e(h('Option Types Formatting'))
    seen = set()
    # hack - we only have one group
    for cmd in groups[0].commands.values():
        params = [p for p in cmd.params
                  if isinstance(p, click.core.Option)]
        for p in params:
            metavar = p.make_metavar()
            if metavar in metavar_docs and metavar not in seen:
                target = metavar.replace(' ', '-').replace('...', '')
                e.e('.. _cli-metavar-%s:\n' % target)
                e.e(h(metavar, '.'))
                cleaned, _ = re.subn('  +', '', metavar_docs[metavar])
                e.e(cleaned)
                seen.add(metavar)

    e.e(h('General Options'))
    for p in scripts.main.params:
        e.e('``--%s``\n   %s\n\n' % (p.name, p.help))

    generate_command_section(e, 'General Commands', general)
    generate_command_section(e, 'Data API', groups[0].commands.values())


def generate_command_section(e, title, commands):
    e.e(h(title))
    commands = list(sorted(commands,
                    lambda a, b: cmp(a.name, b.name)))
    for cmd in commands:
        e.e(':ref:`%s` %s\n\n' % (cmd_ref(cmd), cmd.short_help))

    for cmd in commands:
        e.e('.. index:: %s' % cmd.name)
        e.e('.. _%s:\n' % cmd_ref(cmd))
        e.e(h(cmd.name, '.'))
        e.e(cmd.help)
        ctx = click.Context(cmd)
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
