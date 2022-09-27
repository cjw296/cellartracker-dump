import csv
from collections import deque
from getpass import getpass
from io import StringIO
from pathlib import Path

import click
import httpx
import keyring
import rich

SERVICE = 'cellartracker-dump'


def credentials(service):
    username = keyring.get_password(service, 'username')
    password = keyring.get_password(service, 'password')
    if not (username and password):
        raise RuntimeError('login first!')
    return username, password


@click.group()
def cli():
    pass


@cli.command()
def login():
    username = input('username: ')
    password = getpass('password: ')
    keyring.set_password(SERVICE, 'username', username)
    keyring.set_password(SERVICE, 'password', password)


class Client:

    base_url = 'https://www.cellartracker.com'

    def __init__(self, username, password):
        self._httpx = httpx.Client()
        response = self._httpx.post(f'{self.base_url}/password.asp', data={
            'Referrer': '/default.asp',
            'szUser': username,
            'szPassword': password,
            'UseCookie': 'true',
        })
        if 'User' not in response.cookies:
            raise ValueError('authentication failed')

    def get_table(self, name, format='csv', **params):
        params['Table'] = name
        params.setdefault('Format', format)
        response = self._httpx.get(f'{self.base_url}/xlquery.asp', params=params)
        if response.status_code != 200 or b'<html>' in response.content:
            raise ValueError(f'{response.url} gave {response}:\n{response.content[:200]}')
        return response.text


@cli.command()
@click.argument('output', type=click.Path(exists=True))
@click.option('--show', default=False, is_flag=True)
def dump(output, show):
    root = Path(output).expanduser()
    client = Client(*credentials(SERVICE))
    for name, params in (
            ('List', {'Location': 1}),
            ('Inventory', {}),
            ('Notes', {}),
            ('PrivateNotes', {}),
            ('Purchase', {}),
            ('Pending', {}),
            ('Consumed', {}),
            ('Availability', {}),
            ('Tag', {}),
            ('ProReview', {}),
            ('Bottles', {}),
            ('FoodTags', {}),
    ):
        text = client.get_table(name, **params)
        reader = csv.DictReader(StringIO(text))
        if show:
            for row in reader:
                rich.print(row)
        else:
            # make sure DictReader can parse all the rows
            deque(reader, maxlen=0)
        path: Path = root / (name.lower()+'.csv')
        path.write_text(text)
        rich.print(f"Wrote {path}")


if __name__ == '__main__':
    cli()
