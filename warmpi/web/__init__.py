import re

def is_mobile(ua):
    m = re.search('(android|avantgo|blackberry|bolt|boost|cricket|docomo|fone|hiptop|mini|mobi|palm|phone|pie|tablet|up\.browser|up\.link|webos|wos)', ua, re.I)
    if m is None:
        return False
    return True