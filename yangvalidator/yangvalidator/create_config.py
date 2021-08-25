import os
import configparser


def create_config(config_path=os.environ['YANGCATALOG_CONFIG_PATH']):
    config = configparser.ConfigParser()
    config._interpolation = configparser.ExtendedInterpolation()
    config.read(config_path)
    return config
