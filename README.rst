Artist Follow Plugin for Beets
==============================

Plugin for the music library manager,
`Beets <http://beets.radbox.org/>`__. Get notifications about new
releases from album artists in your Beets library using
`muspy <https://muspy.com/>`__.

Installation
------------

.. code:: sh

    pip install beets-follow

or

.. code:: sh

    git clone https://github.com/nolsto/beets-follow.git
    cd beets-follow
    python setup.py install

Configuration
-------------

Add ``follow`` to the
`plugins <http://beets.readthedocs.org/en/latest/plugins/index.html#using-plugins>`__
option in your Beets
`config.yaml <http://beets.readthedocs.org/en/latest/reference/config.html>`__.

.. code:: yaml

    plugins: follow

muspy Configuration
~~~~~~~~~~~~~~~~~~~

To use muspy's API, the follow plugin must be configured with the email
address and password you used to register with muspy. It will also need
your muspy User ID. If you do not know your User ID,

Sign in to muspy.com and click the Subscribe in a reader link (the RSS
icon in the subnavigation). Your user ID can be extracted from the
resulting URL: ``https://muspy.com/feed?id=<your userid>``

Add the following to your Beets config.yaml.

.. code:: yaml

    follow:
        email: <your email>
        password: <your password>
        userid: <your userid>

Options
~~~~~~~

Add the ``auto`` option to the follow section of your Beets config.yaml
to automatically follow an artist when an album of theirs is imported
into your library.

.. code:: yaml

    follow:
        auto: yes

Setting the ``auto`` option will also unfollow an artist after an album
removal if none of the artist's albums remain in your library.

Commands
--------

follow
~~~~~~

``beet follow [query]``

Query can be any string following Beets' `query string
syntax <http://beets.readthedocs.org/en/latest/reference/query.html>`__.

All matched items will have their album artist (if one exists) added to
muspy.

If no query is included, all album artists in your library will be added
to muspy.

unfollow
~~~~~~~~

``beet unfollow [query]``

Similar to follow, all matched items will have their album artist (if
one exists) removed from muspy.

If no query is included, all album artists in your library will be removed
from muspy.
