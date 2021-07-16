#!/usr/bin/env python3
"""
Short description of the scripts functionality
Example (in your terminal):
    $ python3 export_problems.py --stage A
Author: Mark Bley
Date:   21.06.2021
Version: 0.1
libs: argparse, json, urllib3
"""
import time
import datetime
import json
import logging
import argparse
import configparser
import requests
# supress SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT_URL = ''
TOKEN = ''
HEADER = ''
DRY_RUN = ''


def cmdline_args():
    '''parse arguments'''
    # Make parser object
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-s', '--stage', required=True,
                        type=str, help='A oder E')
    parser.add_argument('-c', '--config', type=str, help='Path to config',
                        default='./config.ini')
    parser.add_argument('-d', '--dry-run', action='store_true',
                        help='Run without changing anything')
    return parser.parse_args()


def make_request(url, parameters=None, method=None, payload=None):
    '''makes post or get request request'''
    try:
        if method == 'POST':
            res = requests.post(url, data=payload, headers=HEADER,
                                verify=False, params=parameters)
        elif method == 'GET':
            res = requests.get(url, headers=HEADER,
                               verify=False, params=parameters)
        else:
            print('Unkown Method')
            exit(-1)
    except requests.exceptions.RequestException as exception:
        raise SystemExit(exception)
    if res.status_code > 399:
        print(res.text)
        exit(-1)
    return res


def init():
    '''initialize parameters'''
    global ROOT_URL, TOKEN, HEADER, DRY_RUN
    args = cmdline_args()
    config_path = args.config
    stage = args.stage
    DRY_RUN = args.dry_run
    config = configparser.ConfigParser()
    config.read(config_path)
    if stage == 'E':
        ROOT_URL = config['ENV-1']['URL']
        TOKEN = config['ENV-1']['TOKEN']
    elif stage == 'A':
        ROOT_URL = config['ENV-2']['URL']
        TOKEN = config['ENV-2']['TOKEN']
    else:
        print('Invalid Environment')
        exit(-1)
    HEADER = {
        "Authorization": "Api-TOKEN " + TOKEN,
        "Content-Type": "application/json"
    }
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs/template.log"),
            logging.StreamHandler()
        ]
    )


def get_problems():
    url = ROOT_URL + '/api/v2/problems'
    problem_list = []
    params = {
        'from': 'now-1w',
        'pageSize': 400
    }
    res = make_request(url, method='GET', parameters=params)
    res_json = json.loads(res.text)
    problem_list.extend(res_json['problems'])
    while 'nextPageKey' in res_json:
        parameters = {'nextPageKey': res_json['nextPageKey']}
        res = make_request(url, parameters, 'GET')
        res_json = json.loads(res.text)
        problem_list.extend(res_json['problems'])
    # print(res_json['result'])
    return problem_list


def main():
    '''main'''
    init()
    problem_list = get_problems()
    output = open('problem-feed.csv', 'w')
    output.write(
        'title; problemId; impactLevel; severityLevel; firstSeen; lastSeen; duration\n')
    # print(json.dumps(probs[333]))
    for problem in problem_list:
        problemId = problem['problemId']
        impactLevel = problem['impactLevel']
        severityLevel = problem['severityLevel']
        title = problem['title']
        # print(problem['problemId'])
        lastSeen = problem['endTime'] / 1000
        firstSeen = problem['startTime'] / 1000
        if lastSeen > 0:
            duration = (lastSeen - firstSeen)
            duration = str(datetime.timedelta(seconds=duration))
            lastSeen = datetime.datetime.fromtimestamp(lastSeen)
            lastSeen = lastSeen.strftime('%Y-%m-%d %H:%M:%S')
        else:
            #duration = -1
            now = time.time()
            duration = (now - firstSeen)
            duration = str(datetime.timedelta(seconds=duration))
            lastSeen = -1
        firstSeen = datetime.datetime.fromtimestamp(firstSeen)
        firstSeen = firstSeen.strftime('%Y-%m-%d %H:%M:%S')
        #firstSeen = datetime.utcfromtimestamp(firstSeen).strftime('%Y-%m-%d %H:%M:%S')
        #lastSeen = datetime.utcfromtimestamp(lastSeen).strftime('%Y-%m-%d %H:%M:%S')
        line = '{};{};{};{};{};{};{}\n'.format(
            title, problemId, impactLevel, severityLevel, firstSeen, lastSeen, duration)
        output.write(line)
    output.close()


if __name__ == '__main__':
    main()
