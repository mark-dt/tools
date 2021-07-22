#!/usr/bin/env python3
"""
Get Host units for hosts with a specific tag
Example (in your terminal):
    $ python3 get_hu_by_tag.py -env <TENANT_URL> -t <DT_TOKEN> (-tag "key(:value)")
Author: Mark Bley
Date:   22.07.2021
Version: 0.1
libs: argparse, json, requests, urllib3
"""
import logging
import json
import requests
import argparse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT_URL = ''
TOKEN = ''
HEADER = ''
TAG = ''

def make_request(URL=None, parameters=None, method=None, payload=None,):
    try:
        if method == 'GET':
            res = requests.get(URL, headers=HEADER,
                               verify=False, params=parameters, timeout=10)
        elif method == 'POST':
            res = requests.post(URL, data=payload,
                                headers=HEADER, verify=False,
                                params=parameters)
        elif method == 'PUT':
            res = requests.put(URL, data=payload, headers=HEADER,
                               verify=False, params=parameters, timeout=10)
    except Exception as excep:
        logging.error(excep)
        exit(-1)
    if res.status_code > 399:
        logging.error(res.text)
        exit(-1)
    return res


def cmdline_args():
    '''parse arguments'''
    # Make parser object
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-env', '--environment', required=True,
                        type=str, help='Environment')
    parser.add_argument('-t', '--token', required=True,
                        type=str, help='DT TOken')
    parser.add_argument('-c', '--config', type=str, help='Path to config')
    parser.add_argument('-tag', '--tag', type=str, help='Tag to check for')
    return parser.parse_args()


def init():
    '''initialize parameters'''
    global ROOT_URL, TOKEN, HEADER, TAG
    args = cmdline_args()
    env = args.environment
    ROOT_URL = env[:-1] if env[-1] == '/' else env
    TAG = args.tag
    TOKEN = args.token
    '''
    config_path = args.config
    if config_path != '':
        config = configparser.ConfigParser()
        config.read(config_path)
        if env == '1':
            ROOT_URL = config['ENV_1']['URL']
            TOKEN = config['ENV_1']['TOKEN']
        else:
            print('Invalid Environment')
            exit(-1)
    '''
    HEADER = {
        "Authorization": "Api-TOKEN " + TOKEN,
        "Content-Type": "application/json"
    }
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            # logging.FileHandler("get_hu.log"),
            logging.StreamHandler()
        ]
    )


def get_all_hosts():
    '''returns json list with all hosts'''
    url = ROOT_URL + '/api/v2/entities'
    host_list = []
    # just get all entities in case of empty tag value
    entity_selector = 'type("HOST"),state("RUNNING"),tag("{}")'.format(
        TAG) if TAG != None else 'type("HOST"),state("RUNNING")'
    parameters = {'pageSize': 500,
                  'entitySelector': entity_selector,
                  # 'fields': '+properties.customHostMetadata,+managementZones',
                  'from': '-1w',
                  'to': 'now'}
    res = make_request(url, parameters, 'GET')
    res_json = json.loads(res.text)
    host_list.extend(res_json['entities'])
    while 'nextPageKey' in res_json:
        parameters = {'nextPageKey': res_json['nextPageKey']}
        res = make_request(url, parameters, 'GET')
        res_json = json.loads(res.text)
        host_list.extend(res_json['entities'])
    return host_list


def get_hu(host_id):
    url = ROOT_URL + '/api/v1/entity/infrastructure/hosts/' + host_id
    res = make_request(URL=url, method='GET')
    res_json = json.loads(res.text)
    return int(res_json['consumedHostUnits'])


def main():
    init()
    host_list = get_all_hosts()
    total_hu = 0
    for host in host_list:
        total_hu += get_hu(host['entityId'])
    logging.info('Total Host Units consumentd: %s', total_hu)


if __name__ == '__main__':
    main()
