import json
from plistlib import load
import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from utils import Utils

tools = Utils(__file__)

def upload_dashboard(dashboard):
    _url = tools.root_url + '/api/config/v1/dashboards/' + dashboard['id']
    #del dashboard['id']
    dasboard_payload = json.dumps(dashboard)
    if not tools.dry_run:
        res = tools.make_request(_url, payload=dasboard_payload, method='PUT')
        tools.logger.debug(res.text)

def load_dashboards():
    path = './'
    #onlyfiles = [f for f in os.listdir(path) if (os.path.isfile(os.path.join(path, f) and f.split('.')[1] == 'json'))]
    onlyfiles = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    dashboards = [d for d in onlyfiles if d.split('.')[1] == 'json']
    for d in dashboards:
        d_file = open(d, 'r')
        #d_string = d_file.read()
        #print(d_string)
        d_json = json.load(d_file)
        upload_dashboard(d_json)

def main():
    load_dashboards()

if __name__ == '__main__':
    main()