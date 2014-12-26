import logging
import urllib2

from functools import wraps

from beets import config, dbcore, ui
from beets.plugins import BeetsPlugin
from beets.util import confit


log = logging.getLogger('beets')

plugin_home = 'https://github.com/nolsto/beets-follow/'
muspy_api = 'https://muspy.com/api/1/'
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(password_mgr))

added_artists = {}
removed_artists = {}


def credentials_required(func):
    """Wrapper to ensure password manager has been fed muspy auth credentials
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not password_is_managed():
            manage_password()
        return func(*args, **kwargs)
    return wrapper


def password_is_managed():
    return password_mgr.find_user_password(None, muspy_api) != (None, None)


def manage_password():
    try:
        (email, password, userid) = get_credentials()
    except ui.UserError, e:
        raise
    else:
        password_mgr.add_password(None, muspy_api, email, password)


def get_credentials():
    try:
        email = config['follow']['email'].get()
        password = config['follow']['password'].get()
        userid = config['follow']['userid'].get()
    except confit.NotFoundError, e:
        err = '%s. Please see %s' % (e, plugin_home + '#muspy-configuration')
        raise ui.UserError(err)
    return (email, password, userid)


@credentials_required
def follow_artist(artistid, artist):
    userid = config['follow']['userid'].get()
    endpoint = '/'.join(('artists', userid, artistid))
    request = urllib2.Request(muspy_api + endpoint)
    request.get_method = lambda: 'PUT'
    try:
        response = opener.open(request)
    except urllib2.URLError, e:
        log.error('Unable to follow %s. %s' % (artist, e))
    else:
        log.info('Followed %s' % artist)


@credentials_required
def unfollow_artist(artistid, artist):
    userid = config['follow']['userid'].get()
    endpoint = '/'.join(('artists', userid, artistid))
    request = urllib2.Request(muspy_api + endpoint)
    request.get_method = lambda: 'DELETE'
    try:
        response = opener.open(request)
    except urllib2.URLError, e:
        log.error('Unable to unfollow %s. %s' % (artist, e))
    else:
        log.info('Unfollowed %s' % artist)


def follow_added_artist(lib, album):
    """Follow albums's artist. Store the artist if it has not been encountered yet
    """

    artistid = album.get('mb_albumartistid')
    if artistid and not artistid in added_artists:
        artist = album.albumartist
        added_artists[artistid] = artist
        follow_artist(artistid, artist)


def track_removed_artists(item):
    """Store item's album artist if the artist has not been encountered yet
    """

    artistid = item.get('mb_albumartistid')
    if artistid and not artistid in removed_artists:
        removed_artists[artistid] = item.albumartist


def unfollow_removed_artists(lib):
    """Unfollow artists who no longer have albums present in the library

    Iterate through removed artists.
    Query for the artist id. If no results, unfollow the artist.
    """

    for artistid, artist in removed_artists.iteritems():
        query = dbcore.MatchQuery('mb_albumartistid', artistid)
        if not lib.items(query).get():
            unfollow_artist(artistid, artist)


class FollowPlugin(BeetsPlugin):

    def __init__(self):
        super(FollowPlugin, self).__init__()

        self.config.add({'auto': False})

        if self.config['auto']:
            self.register_listener('album_imported', follow_added_artist)
            self.register_listener('item_removed', track_removed_artists)
            self.register_listener('cli_exit', unfollow_removed_artists)


    def commands(self):
        follow_cmd = ui.Subcommand('follow', help='follow album artist')
        unfollow_cmd = ui.Subcommand('unfollow', help='unfollow album artist')

        @credentials_required
        def follow(lib, opts, args):
            for item in lib.items(ui.decargs(args)):
                album = item.get_album()
                if album:
                    follow_added_artist(lib, album)
        follow_cmd.func = follow

        @credentials_required
        def unfollow(lib, opts, args):
            for item in lib.items(ui.decargs(args)):
                album = item.get_album()
                if album:
                    track_removed_artists(album)
            for artistid, artist in removed_artists.iteritems():
                unfollow_artist(artistid, artist)
        unfollow_cmd.func = unfollow

        return [follow_cmd, unfollow_cmd]
