import configparser
import os


def create_config(config_path=os.environ['YANGCATALOG_CONFIG_PATH']) -> configparser.ConfigParser:
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(config_path)
    return config
