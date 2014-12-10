# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class CyberlockerCh(DeadHoster):
    __name    = "CyberlockerCh"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?cyberlocker\.ch/\w+'

    __description = """Cyberlocker.ch hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(CyberlockerCh)