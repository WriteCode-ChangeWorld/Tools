# coding=utf-8
import os
import logging
import configparser


def get_config():
    # 读取配置文件
    run_env = 'production'
    if 'SERVICE_ENV' in os.environ:
        run_env = os.environ['SERVICE_ENV']
    print("Load config [%s]" % run_env)
    config_path = '{}/{}.ini'.format(os.path.split(os.path.abspath(__file__))[0], run_env)
    if os.path.isfile(config_path):
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')

        app_config = dict()
        for section in config.sections():
            app_config[section] = dict(config.items(section))

        app_config["RUN_ENV"] = run_env
        return app_config
    else:
        logging.error("Config not exist")
        exit()
