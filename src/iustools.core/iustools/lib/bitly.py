
import re
import json
from urllib2 import urlopen

from cement.core.namespace import get_config
from cement.core.log import get_logger

log = get_logger(__name__)
config = get_config()

# FIX ME: Need to convert this to python-bitly... maybe
# http://code.google.com/p/python-bitly/
def shorten_url(long_url):
    """
    Shorten a URL using bit.ly.
    """
    if not config['bitly_enabled']:
        log.debug('bit.ly shortening service is not enabled, skipping.')
        return long_url

    bitly_url = "%s?format=json&longUrl=%s&login=%s&apiKey=%s" % (
        config['bitly_baseurl'],
        unicode(long_url),
        config['bitly_user'],
        config['bitly_apikey'],
        )
    bitly_url = re.sub('\+', '%2b', bitly_url)
    res = urlopen(bitly_url)

    try:
        data = json.loads(res.read())
        url = data['data']['url']
        return url
    except TypeError, e:
        log.warn("Unable shorten URL with bit.ly - possibly an invalid config.")
        return long_url