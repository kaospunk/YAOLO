#!/usr/bin/python3
import argparse
import math
import getpass
import json
import os
import random
import requests
import sys
import time
from lxml import html

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:52.0) Gecko/20100101 Firefox/52.0'}


def login(s, username, password):
    r = s.get('https://www.linkedin.com/', headers=headers)
    tree = html.fromstring(r.content)
    form = tree.find('.//form[@class="login-form "]')
    loginCsrfParam = form.find('.//input[@name="loginCsrfParam"]').value
    r = s.post('https://www.linkedin.com/uas/login-submit',
               data={
                    'session_key': username,
                    'session_password': password,
                    'isJsEnabled': 'false',
                    'loginCsrfParam': loginCsrfParam},
               headers=headers)


def search(s, args):
    url = 'https://www.linkedin.com/search/results/people/'
    if args.company:
        url += '?keywords=company%3A"{}"'.format(args.company)
    elif args.facet_ids:
        ids = "%22%2c%22".join(args.facet_ids.split(","))
        url += "?facetCurrentCompany=%5B%22{}%22%5D".format(ids)
    url += '&origin=GLOBAL_SEARCH_HEADER'
    if args.title:
        url += "&title={}".format(args.title)
    current_page = 1
    collected_users = 0
    total_users = 0
    output_file = None

    if not args.max_users:
        args.max_users = float('inf')

    while args.max_users > collected_users:
        time.sleep(random.randint(1, 5))
        r = s.get(url + '&page=' + str(current_page),  headers=headers)
        root = html.document_fromstring(r.text)
        codejson = root.xpath('//code[contains(text(),"GLOBAL_SEARCH_HEADER")]')
        for code_element in codejson:
            cont = json.loads(code_element.text)
            if 'included' in cont:
                for entry in cont['included']:
                    if "total" in entry:
                        total_users = entry["total"]
                    if entry['$type'] == 'com.linkedin.voyager.identity.shared.MiniProfile':
                        emp_name = []
                        if 'objectUrn' in entry:
                            linkedin_id = entry['objectUrn'].split(':')[3]
                            emp_name.append(linkedin_id)
                        if 'firstName' in entry:
                            emp_name.append(entry['firstName'])
                        else:
                            emp_name.append('')
                        if 'lastName' in entry:
                            emp_name.append(entry['lastName'])
                        else:
                            emp_name.append('')
                        if 'occupation' in entry:
                            emp_name.append(entry['occupation'])
                        else:
                            emp_name.append('')
                        if 'publicIdentifier' in entry:
                            emp_name.append('https://www.linkedin.com/in/' + entry['publicIdentifier'])
                        else:
                            emp_name.append('')
                        if args.output:
                            if output_file is None:
                                output_file = open(args.output, "w")
                            output_file.write(','.join(emp_name) + '\n')
                        else:
                            print(','.join(emp_name))
                        collected_users += 1

        current_page += 1
        if current_page > math.ceil(total_users / 10):
            break


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-m', dest='max_users', type=int,
                        default=float('inf'),
                        help='The maximum number of employees to enumerate (default: all)')

    parser.add_argument('-u', dest='username', required=True,
                        help='Account email to log in to LinkedIn with')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', dest='company',
                       help='The company name to scrape from LinkedIn')
    group.add_argument('-ids',
                       dest='facet_ids',
                       help='A comma separated list of company facet ids to scrape from LinkedIn')

    parser.add_argument('-t',
                        dest='title',
                        help='An optional keyword to search for in job titles')

    parser.add_argument('-o',
                        dest='output',
                        help='Name of a file to output results to')

    args = parser.parse_args()
    s = requests.Session()
    password = getpass.getpass(prompt='Provide LinkedIn Password: ')
    login(s, args.username, password)
    del password
    search(s, args)


if __name__ == '__main__':
    if sys.version_info < (3, 3):
        print('[-] Please run this script with a version of Python 3.3+')
        sys.exit(os.EX_SOFTWARE)
    main()
