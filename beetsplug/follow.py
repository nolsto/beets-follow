import logging
from collections import OrderedDict
from functools import wraps
try:
    from urllib.request import build_opener
    from urllib.request import HTTPBasicAuthHandler
    from urllib.request import HTTPPasswordMgrWithDefaultRealm
    from urllib.request import Request
    from urllib.error import URLError
except ImportError:
    from urllib2 import build_opener
    from urllib2 import HTTPBasicAuthHandler
    from urllib2 import HTTPPasswordMgrWithDefaultRealm
    from urllib2 import Request
    from urllib2 import URLError

from beets import config, dbcore, ui
from beets.plugins import BeetsPlugin
from beets.util import confit


PLUGIN_HOME = 'https://github.com/nolsto/beets-follow/'
MUSPY_API = 'https://muspy.com/api/1/'

log = logging.getLogger('beets')
password_mgr = HTTPPasswordMgrWithDefaultRealm()
opener = build_opener(HTTPBasicAuthHandler(password_mgr))


def credentials_required(func):
    """A wrapper to

    This ensures the password manager has been fed Muspy auth credentials from the config before a
    function is called.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        password_is_unmanaged = password_mgr.find_user_password(None, MUSPY_API) == (None, None)
        if password_is_unmanaged:
            try:
                email = config['follow']['email'].get()
                password = config['follow']['password'].get()
                password_mgr.add_password(None, MUSPY_API, email, password)
            except confit.NotFoundError as e:
                msg = '%s. Please see %s' % (e, PLUGIN_HOME + '#muspy-configuration')
                raise ui.UserError(msg)
        return func(*args, **kwargs)
    return wrapper


class FollowPlugin(BeetsPlugin):
    """TODO: Document plugin.
    """
    def __init__(self):
        super(FollowPlugin, self).__init__()

        self.added_artists = set()
        self.removed_artists = OrderedDict()

        self.userid = self.config['userid'].get()

        self.config.add({'auto': False})
        self.config['email'].redact = True
        self.config['password'].redact = True
        self.config['userid'].redact = True

        if self.config['auto']:
            self.register_listener('item_removed', self.track_removed_artists)
            self.register_listener('cli_exit', self.unfollow_removed_artists)
            self.import_stages = [self.imported]

    @credentials_required
    def imported(self, session, task):
        self.follow_album_artists(task.imported_items())

    def commands(self):
        follow_cmd = ui.Subcommand('follow', help='follow album artist')
        unfollow_cmd = ui.Subcommand('unfollow', help='unfollow album artist')

        @credentials_required
        def follow(lib, opts, args):
            items = lib.items(ui.decargs(args))
            self.follow_album_artists(items)
        follow_cmd.func = follow

        @credentials_required
        def unfollow(lib, opts, args):
            items = lib.items(ui.decargs(args))
            for artist in self.get_album_artists(items):
                self.unfollow_artist(*artist)
        unfollow_cmd.func = unfollow

        return [follow_cmd, unfollow_cmd]

    def get_album_artists(self, items):
        albums = set([item.get_album() for item in items])
        return sorted(set([(album.get('mb_albumartistid'), album.albumartist)
                           for album in albums if album is not None]))

    def follow_album_artists(self, items):
        """TODO: Add docstring for follow_album_artists."""
        for artist in self.get_album_artists(items):
            self.follow_artist(*artist)

    def follow_artist(self, artist_id, artist_name):
        """TODO: Add docstring for follow_artist."""
        if artist_id in self.added_artists:
            return
        endpoint = '/'.join(('artists', self.userid, artist_id))
        request = Request(MUSPY_API + endpoint)
        request.get_method = lambda: 'PUT'
        try:
            opener.open(request)
            log.info('Followed %s' % artist_name)
            self.added_artists.add(artist_id)
        except URLError as e:
            log.error('Unable to follow %s. %s' % (artist_name, e))

    def unfollow_artist(self, artist_id, artist_name):
        """TODO: Add docstring for unfollow_artist."""
        endpoint = '/'.join(('artists', self.userid, artist_id))
        request = Request(MUSPY_API + endpoint)
        request.get_method = lambda: 'DELETE'
        try:
            opener.open(request)
            log.info('Unfollowed %s' % artist_name)
        except URLError as e:
            log.error('Unable to unfollow %s. %s' % (artist_name, e))

    def track_removed_artists(self, item):
        """Store item's album artist if the artist has not been encountered yet."""
        artist_id = item.get('mb_albumartistid')
        if artist_id and artist_id not in self.removed_artists:
            self.removed_artists[artist_id] = item.albumartist

    @credentials_required
    def unfollow_removed_artists(self, lib):
        """Unfollow artists who no longer have albums present in the library.

        Iterate through removed artists and query for the artist id. If there are no results,
        unfollow the artist.
        """
        for artist_id, artist_name in self.removed_artists.items():
            query = dbcore.MatchQuery('mb_albumartistid', artist_id)
            if not lib.items(query).get():
                self.unfollow_artist(artist_id, artist_name)
