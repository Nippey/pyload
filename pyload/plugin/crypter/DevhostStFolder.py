# -*- coding: utf-8 -*-
#
# Test links:
# http://d-h.st/users/shine/?fld_id=37263#files

import re

from urlparse import urljoin

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class DevhostStFolder(SimpleCrypter):
    __name    = "DevhostStFolder"
    __type    = "crypter"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?d-h\.st/users/(?P<USER>\w+)(/\?fld_id=(?P<ID>\d+))?'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """d-h.st folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zapp-brannigan", "fuerst.reinje@web.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    LINK_PATTERN = r'(?:/> |;">)<a href="(.+?)"(?!>Back to \w+<)'
    OFFLINE_PATTERN = r'"/cHP">test\.png<'


    def getFileInfo(self):
        if re.search(self.OFFLINE_PATTERN, self.html):
            self.offline()

        try:
            id = re.match(self.__pattern, self.pyfile.url).group('ID')
            if id == "0":
                raise

            p = r'href="(.+?)">Back to \w+<'
            m = re.search(p, self.html)
            html = self.load(urljoin("http://d-h.st", m.group(1)),
                             cookies=False)

            p = '\?fld_id=%s.*?">(.+?)<' % id
            m = re.search(p, html)
            name = folder = m.group(1)

        except Exception, e:
            self.logDebug(e)
            name = folder = re.match(self.__pattern, self.pyfile.url).group('USER')

        return {'name': name, 'folder': folder}


    def getLinks(self):
        return [urljoin("http://d-h.st", link) for link in re.findall(self.LINK_PATTERN, self.html)]