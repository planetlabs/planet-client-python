import click
import time


@click.command()
@click.option('--count', default=1, help='Number of greetings.')
@click.option('--name', prompt='Your name',
              help='The person to greet.')
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for x in range(count):
        msg = 'Hello %s [%d]!' % (name, x)
        click.echo(msg, nl=False)
        time.sleep(.5)
        click.echo('\b' * len(msg), nl=False)


if __name__ == '__main__':
    hello()
