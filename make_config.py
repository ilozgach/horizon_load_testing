import json
import os

if __name__ == '__main__':
    # collect values from fuel
    admin_user_id = os.popen(
        "keystone user-list | grep admin | head -n 1 | cut -d'|' -f 2"
    ).read().strip()

    admin_user_password = "admin"

    admin_project_id = os.popen(
        "keystone tenant-list | grep admin | head -n 1 | cut -d'|' -f 2"
    ).read().strip()

    horizon_base_url = os.popen(
        "keystone endpoint-list | grep 9696 | head -n 1 | cut -d'|' -f 4"
    ).read().strip().replace(":9292", "")

    keystone_public_url = os.popen(
        "keystone endpoint-list | grep 5000 | head -n 1 | cut -d'|' -f 4"
    ).read().strip().replace('v2.0', 'v3')

    glance_public_url = os.popen(
        "keystone endpoint-list | grep 9292 | head -n 1 | cut -d'|' -f 4"
    ).read().strip()

    neutron_public_url = os.popen(
        "keystone endpoint-list | grep 9696 | head -n 1 | cut -d'|' -f 4"
    ).read().strip()

    grid_url = "http://localhost:4444/wd/hub"

    # update config file for horizon tests
    with open('./conf.json', "r") as data_file:
        data = json.load(data_file)

        data["admin_user_id"] = admin_user_id
        data["admin_user_password"] = admin_user_password
        data["admin_project_id"] = admin_project_id
        data["horizon_base_url"] = horizon_base_url
        data["keystone_public_url"] = keystone_public_url
        data["glance_public_url"] = glance_public_url
        data["neutron_public_url"] = neutron_public_url

    with open('./conf.json', "w") as data_file:
        json.dump(data, data_file, indent=4, sort_keys=True)
