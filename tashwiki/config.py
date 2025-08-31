import os
from configparser import ConfigParser, Error


class Config:

    def __init__(self, config_file: str, config: ConfigParser):
        self.conf_file = config_file
        self.conf = config

    @classmethod
    def from_file(cls, file: str):
        if not os.path.exists(file):
            raise ValueError("Config file not found.")
        try:
            config_parser = ConfigParser()
            config_parser.read(file)
            return cls(file, config_parser)
        except Error:
            raise ValueError("Config file is invalid.")

    @property
    def site_author(self):
        return self.conf.get("site", "author")

    @property
    def site_name(self):
        return self.conf.get("site", "name")

    @property
    def site_baseurl(self):
        return self.conf.get("site", "baseurl")

    @property
    def site_source_dir(self):
        return self.conf.get("site", "source_dir", fallback="content")

    @property
    def site_output_dir(self):
        return self.conf.get("site", "output_dir", fallback="output")
