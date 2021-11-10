import logging
import requests
import argparse
import configparser
import json

# supress SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


HEADER = {}
DRY_RUN = True
PAAS = ''

def make_request(url, parameters=None, method=None, payload=None, paas=None):
    '''makes post or get request request'''
    tmp_auth = HEADER['Authorization']
    if paas != None:
        HEADER['Authorization'] = "Api-TOKEN " + paas

    try:
        if method == 'POST':
            res = requests.post(url, data=payload, headers=HEADER,
                                verify=False, params=parameters, timeout=10)
        elif method == 'GET':
            res = requests.get(url, headers=HEADER,
                               verify=False, params=parameters, timeout=10)
        elif method == 'PUT':
            res = requests.put(url, data=payload, headers=HEADER,
                                verify=False, params=parameters, timeout=10)
        elif method == 'DELETE':
            res = requests.delete(url, data=payload, headers=HEADER,
                                verify=False, params=parameters, timeout=10)
        else:
            print('Unkown Method')
            logging.error('Unkown Request Method')
            exit(-1)
    except requests.exceptions.RequestException as exception:
        logging.error(exception)
        raise SystemExit(exception)
    if res.status_code > 399:
        print(res.text)
        logging.error(res.text)
        exit(-1)
    
    HEADER['Authorization'] = tmp_auth
    return res


def cmdline_args():
    '''parse arguments'''
    # Make parser object
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-c', '--config', type=str, help='Path to config',
                        default='./config.ini')
    parser.add_argument('-d', '--dry-run', action='store_true',
                        help='Run without changing anything')
    return parser.parse_args()

def init():
    '''initialize parameters'''
    global ROOT_URL, HEADER, DRY_RUN, PAAS
    parameters = {}
    args = cmdline_args()
    config_path = args.config
    config = configparser.ConfigParser()
    config.read(config_path)

    DRY_RUN = not args.dry_run

    params = {}
    params['DRY_RUN'] = DRY_RUN

    token = config['ENV']['token']
    ROOT_URL = config['ENV']['url']
    PAAS = config['ENV']['paas']
    HEADER = {
        "Authorization": "Api-TOKEN " + token,
        "Content-Type": "application/json"
    }

    logging.basicConfig(
    # level=logging.DEBUG,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/purge-tenant.log"),
        logging.StreamHandler()
    ]
)
    if DRY_RUN:
        logging.info('DRY RUN')


def get_oa_updater(host_id):
    _url = ROOT_URL + '/api/config/v1/hosts/{}/autoupdate'.format(host_id)
    res = make_request(url=_url, method='GET')
    data = json.loads(res.text)
    #print(res.text)
    return data

def get_all_hosts():
    '''returns json list with all hosts'''
    url = ROOT_URL + '/api/v2/entities'
    host_list = []
    # just get all entities in case of empty tag value
    #entity_selector = 'type("HOST"),isMonitoringCandidate("true")'
    #entity_selector = 'type("HOST")'
    #entity_selector = 'type("HOST"),state("RUNNING"),tag("{}")'.format(TAG) if TAG != '' else 'type("HOST"),state("RUNNING")'
    parameters = {'pageSize': 500,
                  'entitySelector': 'type("HOST"),state("RUNNING")',
                  'fields': '+properties.installerVersion',
                  'from': '-1w',
                  'to': 'now'}
    # 'from': '2021-08-01T05:57:01.123+01:00',
    # 'from': '-7d',
    # 'to': '2021-08-30T05:57:01.123+01:00'}
    res = make_request(url, parameters, 'GET')
    res_json = json.loads(res.text)
    host_list.extend(res_json['entities'])
    while 'nextPageKey' in res_json:
        parameters = {'nextPageKey': res_json['nextPageKey']}
        res = make_request(url, parameters, 'GET')
        res_json = json.loads(res.text)
        host_list.extend(res_json['entities'])
    return host_list

def get_available_oa_versions():
    _url = ROOT_URL + '/api/v1/deployment/installer/agent/versions/unix/default'
    res = make_request(url=_url, method='GET', paas=PAAS)
    data = json.loads(res.text)
    return sorted(data['availableVersions'])

def update_oa(config):
    _url = ROOT_URL + '/api/config/v1/hosts/{}/autoupdate'.format(config['id'])
    _payload = json.dumps(config)
    res = make_request(url=_url, method='GET', payload=_payload)
    data = json.loads(res.text)
    #print(res.text)
    return data


def main():
    init()
    host_list = get_all_hosts()
    oa_versions = get_available_oa_versions()
    #print(oa_versions)
    for host in host_list:
        host_version =host['properties']['installerVersion']
        if host_version in oa_versions:

            config = get_oa_updater(host['entityId'])
            print(config)
            # TODO: just update to latest )
            config['version'] = oa_versions[-1]
            print(config)
            #update_oa(config)
            print(host_version)


if __name__ == '__main__':
    main()
