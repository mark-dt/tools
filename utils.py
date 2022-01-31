from concurrent.futures.process import _threads_wakeups
import configparser
import requests
import json
import logging
import argparse
import datetime
import os

ROOT_URL = ''
TOKEN = ''
PAAS = ''
HEADER = ''
DRY_RUN = ''

def cmdline_args():
    '''Parse arguments'''
    # Make parser object
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-e', '--environment', required=True,
                        type=str, help='DT env')
    parser.add_argument('-c', '--config', type=str, help='Path to config',
                        default='./config.ini')
    parser.add_argument('--log-level', type=str,
                        help='Set deubg output level: DEBUG, INFO, WARNING, ERROR',
                        default='INFO')
    parser.add_argument('--log-path', type=str, help='Path to log folder',
                        default='./')
    parser.add_argument('-d', '--dry-run', action='store_true',
                        help='Run without changing anything')
    return parser.parse_args()

def make_request(url, parameters=None, method=None, payload=None):
    '''
    Simplifies making requests

    Parameters:
        URL (str): endpoint for the API call
        parameters (dict): parameters for the POST/PUT requests
        method (str): type of request (POST, PUT, GET, DELETE)
        payload (str): json string of the object to be created/updated

    Returns:
        Request result
    '''
    
    verify_request = True
    try:
        if method == 'POST':
            res = requests.post(url, data=payload, headers=HEADER,
                                verify=verify_request, params=parameters, timeout=10)
        elif method == 'GET':
            res = requests.get(url, headers=HEADER,
                               verify=verify_request, params=parameters, timeout=10)
        elif method == 'PUT':
            res = requests.put(url, data=payload, headers=HEADER,
                               verify=verify_request, params=parameters, timeout=10)
        else:
            logging.error('Unkown Request Method %s', method)
            exit(-1)
    except Exception as exception:
        logging.error(exception)
        raise SystemExit(exception)
    if res.status_code > 399:
        logging.error(res.text)
    return res

def init(instance):
    '''
    Initialize logging, parses config file and creates header for requests
    '''
    global ROOT_URL, TOKEN, HEADER, DRY_RUN, PAAS
    args = cmdline_args()
    config_path = args.config
    env = args.environment
    # TODO: remove, only run in dry-run while developing
    DRY_RUN = not args.dry_run

    if args.log_level == 'DEBUG':
        log_level = logging.DEBUG
    elif args.log_level == 'INFO':
        log_level = logging.INFO
    elif args.log_level == 'WARNING':
        log_level = logging.WARNING
    elif args.log_level == 'ERROR':
        log_level = logging.ERROR
    else:
        log_level = logging.INFO

    log_file_name = instance.split('.')[0] + '.log'
    if args.log_path is not None:
        tmp_path = args.log_path
        if not os.path.isdir(tmp_path):
            print('{} [ERROR] Invalid log folder path: {}'.format(
                str(datetime.datetime.now())[:-3], tmp_path))
            exit(-1)
        log_path = os.path.join(tmp_path, log_file_name)
    else:
        log_path = log_file_name

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

    try:
        config = configparser.ConfigParser()
        config.read(config_path)
        #config_handle = open(config_path, 'r')
        #config = json.load(config_handle)
    except Exception as exeption:
        logging.error('[%s] Cannot open config %s', exeption, config_path)
        exit(-1)

    try:
        tmp_url = config[env]['URL']
        ROOT_URL = tmp_url[:-1] if tmp_url[-1] == '/' else tmp_url
        TOKEN = config[env]['token']
        if 'paas' in config[env]:
            PAAS = config[env]['paas']
    except Exception as exception:
        logging.error('[%s] Cannot read config %s', exception, config_path)
        exit(-1)

    HEADER = {
        "Authorization": "Api-TOKEN " + TOKEN,
        "Content-Type": "application/json"
    }

    if DRY_RUN:
        logging.info('Starting DRY_RUN')
