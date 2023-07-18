# Ansible Collection - sdorra.porkbun

This Ansible Collection provides a module for managing DNS records on [porkbun](https://porkbun.com/).

## Included content

This collection includes the following module:

- `porkbun_record`: This module allows you to create, update, and delete DNS records on [porkbun](https://porkbun.com/).

## Using this collection

You can use the modules in this collection in your playbooks as follows:

```yaml
- name: Create DNS record
  sdorra.porkbun.porkbun_record:
    state: present
    domain: example.com
    record_type: A
    name: www
    content: 192.0.2.1
    ttl: 3600
    api_key: your_api_key
    secret_api_key: your_secret_api_key
```

Replace `your_api_key` and `your_secret_api_key` with your actual Porkbun API key and secret API key.

## License
This collection is licensed under the GNU General Public License v3.0.

## Author

[Sebastian Sdorra](https://sdorra.dev)