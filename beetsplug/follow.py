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
    """Decorates/wraps functions that make authenticated HTTP requests to Muspy.

    This ensures there is a user ID and that the password manager has been fed Muspy auth
    credentials from the config before a function is called. It raises a UI error if otherwise.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        password_is_unmanaged = password_mgr.find_user_password(None, MUSPY_API) == (None, None)
        if password_is_unmanaged:
            try:
                email = config['follow']['email'].get()
                password = config['follow']['password'].get()
                password_mgr.add_password(None, MUSPY_API, email, password)
                # Password manager doesn't need userid, but API calls will.
                config['follow']['userid'].get()
            except confit.NotFoundError as e:
                msg = '%s. Please see %s' % (e, PLUGIN_HOME + '#muspy-configuration')
                raise ui.UserError(msg)
        return func(*args, **kwargs)
    return wrapper


class FollowPlugin(BeetsPlugin):
    """Get notifications about new releases from album artists in your library.

    Uses the Muspy.com API to follow or unfollow artists automatically upon album import or removal,
    or via commands.
    """
    def __init__(self):
        super(FollowPlugin, self).__init__()

        self.config['email'].redact = True
        self.config['password'].redact = True
        self.config['userid'].redact = True

        self.config.add({'auto': False})

        if self.config['auto']:
            def auto_config():
                self.register_listener('item_removed', self.track_removed_artists)
                self.register_listener('cli_exit', self.unfollow_removed_artists)
                self.import_stages = [self.imported]
            credentials_required(auto_config)()

        self.added_artists = set()
        self.removed_artists = OrderedDict()

    def imported(self, session, task):
        self.follow_album_artists(task.imported_items())

    def commands(self):
        follow_cmd = ui.Subcommand('follow', help='Follow album artist of each item in query')
        unfollow_cmd = ui.Subcommand('unfollow', help='Unfollow album artist of each item in query')

        @credentials_required
        def follow(lib, opts, args):
            """Follow album artist of each item in query."""
            items = lib.items(ui.decargs(args))
            self.follow_album_artists(items)
        follow_cmd.func = follow

        @credentials_required
        def unfollow(lib, opts, args):
            """Unfollow album artist of each item in query."""
            items = lib.items(ui.decargs(args))
            for artist in self.get_album_artists(items):
                self.unfollow_artist(*artist)
        unfollow_cmd.func = unfollow

        return [follow_cmd, unfollow_cmd]

    def get_album_artists(self, items):
        """Find the set of album artists belonging to the list of items and return it sorted."""
        albums = set([item.get_album() for item in items])
        return sorted(set([(album.get('mb_albumartistid'), album.albumartist)
                           for album in albums if album is not None]))

    def follow_album_artists(self, items):
        for artist in self.get_album_artists(items):
            self.follow_artist(*artist)

    def follow_artist(self, artist_id, artist_name):
        """Make a PUT request to Muspy with an artist ID and store that ID if successful."""
        if artist_id in self.added_artists:
            return
        endpoint = '/'.join(('artists', self.config['userid'].get(), artist_id))
        request = Request(MUSPY_API + endpoint)
        request.get_method = lambda: 'PUT'
        try:
            opener.open(request)
            log.info('Followed %s' % artist_name)
            self.added_artists.add(artist_id)
        except URLError as e:
            log.error('Unable to follow %s. %s' % (artist_name, e))

    def unfollow_artist(self, artist_id, artist_name):
        """Make a DELETE request to Muspy with an artist ID."""
        endpoint = '/'.join(('artists', self.config['userid'].get(), artist_id))
        request = Request(MUSPY_API + endpoint)
        request.get_method = lambda: 'DELETE'
        try:
            opener.open(request)
            log.info('Unfollowed %s' % artist_name)
        except URLError as e:
            log.error('Unable to unfollow %s. %s' % (artist_name, e))

    def track_removed_artists(self, item):
        """Store an item's album artist if the artist has not been encountered yet."""
        artist_id = item.get('mb_albumartistid')
        if artist_id and artist_id not in self.removed_artists:
            self.removed_artists[artist_id] = item.albumartist

    def unfollow_removed_artists(self, lib):
        """Unfollow album artists who no longer have albums present in the library.

        Iterate through removed artists and query for the artist ID in album artists.
        If there are no results, unfollow the artist.
        """
        for artist_id, artist_name in self.removed_artists.items():
            query = dbcore.MatchQuery('mb_albumartistid', artist_id)
            if not lib.items(query).get():
                self.unfollow_artist(artist_id, artist_name)
