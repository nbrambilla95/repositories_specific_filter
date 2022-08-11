#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
import requests

DOCUMENTATION = r'''
---
module: repos_specific_filter
short_description: List repos with a specific filter
description:
- 
options:
  project_name:
    description: Name of the project
    -
  filter:
    description: It can be = webhooks, users, branches, permissions, none
    -
  key:
    description: Field in the JSON obtained
    -
  value:
    description: Value for the comparisson with the field on the JSON (key)
    -
  username:
    description: Bitbucket username
    -
  password:
    description: Bitbucket password
    -

author: "Nicolas Brambilla"
'''

EXAMPLES = r'''
- repos_specific_filter:
    project: "PROJECT_NAME"
    filter: "webhooks"
    key: "url"
    value: "some_webhook_to_compare"
    username: "user@gmail.com"
    password: "pass"
'''

RETURN = r'''# '''


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            project_name=dict(type='str', required=True),
            filter_input=dict(default='none', choices=[
                'none', 'webhooks', 'permissions/users', 'branches']),
            key=dict(type='str'),
            value=dict(type='str'),
            username=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
        ),
        supports_check_mode=True,

        required_if=[
            ('filter_input', 'webhooks', ['key', 'value']),
            ('filter_input', 'permissions/users', ['key', 'value']),
            ('filter_input', 'branches', ['key', 'value']),
        ]
    )

    params = {
        'project_name': module.params['project_name'],
        'filter_input': module.params['filter_input'],
        'key': module.params['key'],
        'value': module.params['value'],
        'username': module.params['username'],
        'password': module.params['password']
    }

    basicAuthCredentials = (params['username'], params['password'])
    bitbucket_url = f'https://bitbucket.com/rest/api/1.0/projects/{params["project_name"]}/repos'
    query = {'key': params['key'], 'value': params['value']}
    start_page = 0
    is_last_page = False
    bad_status = [403, 404]
    limit = 100
    filter_exists = []
    result_repo_list = []
    filter = params['filter_input']
    result = dict(
        output=''
    )

    while not is_last_page:
        response_bitbucket = requests.get(bitbucket_url, params={
                                          'start': start_page, 'limit': limit}, auth=basicAuthCredentials)
        if response_bitbucket.status_code == 401:
            module.fail_json(
                msg=f'Request to {bitbucket_url} FAILED: Status obtained {response_bitbucket.status_code} wrong user/password')
        if response_bitbucket.status_code in bad_status:
            module.fail_json(
                msg=f'Request to {bitbucket_url} FAILED: Status obtained {response_bitbucket.status_code} trying to obtain info from the project {params["project_name"]}')
        is_last_page = response_bitbucket.json()["isLastPage"]
        if not is_last_page:
            start_page = response_bitbucket.json()["nextPageStart"]
        result_repo_list = result_repo_list + \
            [x['name'] for x in response_bitbucket.json()["values"]]

    if params["filter_input"] == 'none':
        result["output"] = result_repo_list
        module.exit_json(**result)

    for repo in result_repo_list:
        bitbucket_url_filter = f"https://bitbucket.com/rest/api/1.0/projects/{params['project_name']}/repos/{repo}/{filter}"
        response_filter = requests.get(
            bitbucket_url_filter, auth=basicAuthCredentials)
        if response_filter.status_code in bad_status:
            module.fail_json(
                msg=f'Request to {bitbucket_url_filter} FAILED: Status obtained {response_filter.status_code} trying to obtain info from the project {params["project_name"]}')
        filter_exists = filter_exists + \
            [repo for params["filter_input"] in response_filter.json()['values'] if params["filter_input"][query.get("key")]
             == query.get("value")]

    result["output"] = filter_exists
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
