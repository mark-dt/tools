import requests
import json

# supress SSL warnings
#import urllib3
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import utils


def get_all_hosts():
    '''
    Fetch Hosts (active for the last 7 days) with necessary information
 
    Returns:
        Json list of hosts containing tags and Management Zones
    '''
    url = utils.ROOT_URL + '/api/v2/entities'
    host_list = []
    parameters = {'pageSize': 500,
                  #'entitySelector': 'type("HOST"),isMonitoringCandidate("false"),state("RUNNING")',
                  'entitySelector': 'type("HOST"),isMonitoringCandidate("false")',
                  # 'fields': '+properties.customHostMetadata,+managementZones',
                  'fields': '+tags,+managementZones',
                  'from': '-1w',
                  'to': 'now'}
    res = utils.make_request(url, parameters, 'GET')
    res_json = json.loads(res.text)
    host_list.extend(res_json['entities'])
    while 'nextPageKey' in res_json:
        parameters = {'nextPageKey': res_json['nextPageKey']}
        res = utils.make_request(url, parameters, 'GET')
        res_json = json.loads(res.text)
        host_list.extend(res_json['entities'])

    return host_list


def get_latest_oa():
    os_type = ['windows', 'unix']
    # TODO: check for all...
    url = utils.ROOT_URL + '/api/v1/deployment/installer/agent/unix/default/latest/metainfo'
    header = {
        "Authorization": "Api-TOKEN " + utils.PAAS,
        "Content-Type": "application/json"
    }
    res = requests.get(url, headers=header,)
    res_json = json.loads(res.text)
    return res_json

def get_all_oa_versions():
    os_type = ['windows', 'unix']
    # TODO: check for all...
    url = utils.ROOT_URL + '/api/v1/deployment/installer/agent/versions/unix/default'
    header = {
        "Authorization": "Api-TOKEN " + utils.PAAS,
        "Content-Type": "application/json"
    }
    res = requests.get(url, headers=header,)
    res_json = json.loads(res.text)
    versions = res_json['availableVersions'].sort()
    return res_json['availableVersions']

def get_oa_update_conf(host_id):
    
    url = utils.ROOT_URL + f'/api/config/v1/hosts/{host_id}/autoupdate'
    res = utils.make_request(url, method='GET')
    res_json = json.loads(res.text)

def update_oa(host_id, oa_version):
    url = utils.ROOT_URL + f'/api/config/v1/hosts/{host_id}/autoupdate/validator'
    data = {
        'setting': 'DISABLED',
        'version': oa_version
    }
    _payload = json.dumps(data)
    print(_payload)
    res = utils.make_request(url, payload=_payload, method='POST')
    print(res.text)


def main():
    utils.init(__file__)
    host_list = get_all_hosts()
    latest = get_latest_oa()
    all_oa = get_all_oa_versions()
    print(all_oa)
    exit()
    for host in host_list:
        host_id = host['entityId']
        get_oa_update_conf(host_id)
        #update_oa(host_id, latest['latestAgentVersion'])


if __name__ == '__main__':
    main()