import re
import cherrypy

def is_mobile(ua):
    m = re.search('(android|avantgo|blackberry|bolt|boost|cricket|docomo|fone|hiptop|mini|mobi|palm|phone|pie|tablet|up\.browser|up\.link|webos|wos)', ua, re.I)
    if m is None:
        return False
    return True


def no_cache(func):
    """Decorator that sends headers that instruct browsers and proxies not to cache.

    From: http://www.thesamet.com/blog/2006/07/14/making-ie-cache-less/
    """
    def newfunc(*args, **kwargs):
        cherrypy.response.headers['Expires'] = 'Sun, 19 Nov 1978 05:00:00 GMT'
        cherrypy.response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'
        cherrypy.response.headers['Pragma'] = 'no-cache'
        return func(*args, **kwargs)
    return newfunc