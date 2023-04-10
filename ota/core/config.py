# -*- coding: utf-8 -*-
#!/bin/python3

from collections import namedtuple
from datetime import datetime
import logging
import json
import os
import requests
import time
from pathlib import Path

Options = namedtuple("Options", ["url", "authenable", "authmethod"])

DEFAULT_OPTIONS = {
    "url": "http://127.0.0.1:8080",
    "authenable": False,
    "authmethod": False,
}


def read_from_json(path):
    with open(path, "r") as file:
        data = json.loads(file.read())

    return data


def save_to_json(path, data):
    with open(path, "w") as file:
        file.write(json.dumps(data))


class Config(object):
    options: Options = None

    def __init__(self, **kwargs):
        parts = [Path.home(), ".config", "ota.json"]
        self._path = os.path.join(*parts)

        if not os.path.exists(self._path):
            self.create_default()
        else:
            self.load()

    def create_default(self):
        self.options = Options(**DEFAULT_OPTIONS)
        data = self.options._asdict()
        print(data)

        save_to_json(self._path, data)

    def save(self):
        data = read_from_json(self._path)
        data.update(self.options._asdict())

        save_to_json(self._path, data)

    def load(self):

        if not os.path.exists(self._path):
            raise FileNotFoundError

        data = read_from_json(self._path)

        self.options = Options(**data)

    def set_value(self, name, value):
        self.options[name] = value