# Artist Follow Plugin for Beets

Plugin for the music library manager, [Beets](http://beets.radbox.org/). Get notifications about new releases from artists in your Beets library using [muspy](https://muspy.com/).

## Installation

Download the plugin to a folder included in your Beets [pluginpath](http://beets.readthedocs.org/en/latest/reference/config.html#pluginpath).
```sh
wget https://raw.githubusercontent.com/nolsto/beets-follow/master/follow.py
```
or
```sh
curl -o follow.py https://raw.githubusercontent.com/nolsto/beets-follow/master/follow.py
```

## Configuration

Add `follow` to the [plugins](http://beets.readthedocs.org/en/latest/plugins/index.html#using-plugins) option in your Beets [config.yaml](http://beets.readthedocs.org/en/latest/reference/config.html).
```yaml
plugins: follow
```

### muspy Configuration

To use muspy's API, the follow plugin must be configured with the email address and password you used to register with muspy. It will also need your muspy User ID. If you do not know your User ID, either:

Run this script remotely in a shell
```sh
bash <(curl -fsSL https://gist.githubusercontent.com/nolsto/4f1680d095b744662f3c/raw/2ff1d7dd732899f72f5f6e211c0441420d515a98/get_muspy_userid.sh)
```
or clone this repository and run the script locally in a shell.
```sh
git clone https://github.com/nolsto/beets-follow.git
cd beets-follow
chmod +x get_muspy_userid.sh
./get_muspy_userid.sh
```

The script will output a snippet of YAML. Add it to your Beets config.yaml.
```yaml
follow:
    email: <your email>
    password: <your password>
    userid: <your userid>
```

### Options

Add the `auto` option to the follow section of your Beets config.yaml to automatically follow an artist when an album of theirs is imported into your library.
```yaml
follow:
    auto: yes
```

Setting the auto option will also unfollow an artist if all of their albums have been removed from your library.

## Commands

- follow

  ```beet follow [query]```
  
  Query can be any string following Beets' [query string syntax](http://beets.readthedocs.org/en/latest/reference/query.html).
  
  All matched items will have their album artist (if one exists) added to muspy.
  
  If no query is included, all artists in your library will be added to muspy.

- unfollow

  ```beet unfollow [query]```
  
  Similar to follow, all matched items will have their album artist (if one exists) removed from muspy.
  
  If no query is included, all artists in your library will be removed from muspy.
