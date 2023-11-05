#!/usr/bin/python

# Copyright: (c) 2020, Sebastian Sdorra <s.sdorra@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
from ansible.module_utils.urls import open_url
from ansible.module_utils.basic import AnsibleModule
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: porkbun_record
short_description: Manage DNS records on Porkbun
description:
  - This module allows you to create, update, and delete DNS records on Porkbun using the Porkbun API.
options:
  state:
    description:
      - Whether the record should exist or not.
    choices: [ 'present', 'absent' ]
    default: 'present'
  domain:
    description:
      - The domain to add the DNS record to.
    required: true
    type: str
  record_type:
    description:
      - The type of DNS record to manage.
    choices: [ 'A', 'MX', 'CNAME', 'ALIAS', 'TXT', 'NS', 'AAAA', 'SRV', 'TLSA', 'CAA' ]
    required: true
    type: str
  name:
    description:
      - The name of the DNS record.
    required: true
    type: str
  content:
    description:
      - The content of the DNS record.
    required: true
    type: str
  ttl:
    description:
      - The time-to-live of the DNS record.
    default: 600
    type: int
  api_key:
    description:
      - The API key for the Porkbun API.
    required: true
    type: str
    no_log: true
  secret_api_key:
    description:
      - The secret API key for the Porkbun API.
    required: true
    type: str
    no_log: true
'''

EXAMPLES = r'''
# Create an A record
- porkbun_dns:
    state: present
    domain: example.com
    record_type: A
    name: www
    content: 192.0.2.1
    ttl: 3600
    api_key: your_api_key
    secret_api_key: your_secret_api_key

# Delete a TXT record
- porkbun_dns:
    state: absent
    domain: example.com
    record_type: TXT
    name: www
    content: "v=spf1 -all"
    api_key: your_api_key
    secret_api_key: your_secret_api_key

# Update an existing MX record
- porkbun_dns:
    state: present
    domain: example.com
    record_type: MX
    name: mail
    content: "10 mail.example.com."
    ttl: 7200
    api_key: your_api_key
    secret_api_key: your_secret_api_key
'''

RETURNS = r'''
changed:
  description: Whether or not the DNS record was changed
  returned: always
  type: bool
msg:
  description: A message describing what happened
  returned: always
  type: str
'''


class PorkbunAPI:
    API_URL = "https://porkbun.com/api/json/v3/dns"

    def __init__(self, api_key, secret_api_key):
        self.headers = {
            'Content-Type': 'application/json',
        }

        self.base_params = {
            'apikey': api_key,
            'secretapikey': secret_api_key
        }

    def get_records(self, domain):
        response = open_url(f'{self.API_URL}/retrieve/{domain}',
                            method="POST", headers=self.headers, data=json.dumps(self.base_params))
        result = json.loads(response.read())
        return result['records']

    def get_record(self, domain, record_type, name):
        records = self.get_records(domain)
        target_record_name = f'{name}.{domain}' if name else domain
        for record in records:
            if record['type'] == record_type and record['name'] == target_record_name:
                return record
        return None

    def create_record(self, domain, record_type, name, content, ttl):
        data = {
            **self.base_params,
            'type': record_type,
            'name': name,
            'content': content,
            'ttl': ttl
        }
        response = open_url(f'{self.API_URL}/create/{domain}',
                            method='POST', headers=self.headers, data=json.dumps(data))
        return json.loads(response.read())

    def update_record(self, domain, record_type, name, content, ttl):
        data = {
            **self.base_params,
            'content': content,
            'ttl': ttl
        }
        response = open_url(f'{self.API_URL}/editByNameType/{domain}/{record_type}/{name}',
                            method='POST', headers=self.headers, data=json.dumps(data))
        return json.loads(response.read())

    def delete_record(self, domain, record_id):
        response = open_url(f'{self.API_URL}/delete/{domain}/{record_id}',
                            method='POST', headers=self.headers, data=json.dumps(self.base_params))
        return json.loads(response.read())


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            domain=dict(required=True, type='str'),
            record_type=dict(required=True, type='str', choices=[
                             'A', 'MX', 'CNAME', 'ALIAS', 'TXT', 'NS', 'AAAA', 'SRV', 'TLSA', 'CAA']),
            name=dict(required=True, type='str'),
            content=dict(required=True, type='str'),
            ttl=dict(required=False, type='int', default=600),
            api_key=dict(required=True, type='str', no_log=True),
            secret_api_key=dict(required=True, type='str', no_log=True),
        ),
        supports_check_mode=True,
    )

    state = module.params['state']
    domain = module.params['domain']
    record_type = module.params['record_type']
    name = module.params['name']
    content = module.params['content']
    ttl = module.params['ttl']
    api_key = module.params['api_key']
    secret_api_key = module.params['secret_api_key']

    porkbun = PorkbunAPI(api_key, secret_api_key)

    # Check if the record already exists
    record = porkbun.get_record(domain, record_type, name)
    # module.exit_json(record=record)

    if state == 'present':
        if record is None:
            # The record does not exist, create it
            porkbun.create_record(domain, record_type, name, content, ttl)
            module.exit_json(changed=True, msg="DNS record created")
        elif record['content'] != content or int(record['ttl']) != ttl:
            # The record exists but the content or ttl does not match, update it
            porkbun.update_record(domain, record_type, name, content, ttl)
            module.exit_json(changed=True, msg="DNS record updated")
        else:
            # The record already exists and the content and ttl matches
            module.exit_json(changed=False, msg="DNS record already exists")
    else:
        if record is None:
            # The record does not exist, nothing to do
            module.exit_json(changed=False, msg="DNS record does not exist")
        else:
            # The record exists, delete it
            porkbun.delete_record(domain, record['id'])
            module.exit_json(changed=True, msg="DNS record deleted")


if __name__ == '__main__':
    main()
