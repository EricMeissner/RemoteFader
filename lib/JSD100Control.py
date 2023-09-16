#!/usr/bin/env python3
#This class deals with communicating with the JSD100Control

import JSD60Control

ERROR_PREFIX='⚠'
SOCKET_TIMEOUT=250

PORT = 10001

class JSD100Control(JSD60Control.JSD60Control):
    def __init__(self, host):
        super().__init__(host)
        self.API_PREFIX='jsd100'
