import time
import random
from keystoneclient import session
from keystoneclient.auth.identity import v3
from glanceclient import Client as GlanceClient
from cinderclient.v2 import Client as CinderClient
from novaclient import client as NovaClientFactory
from neutronclient.v2_0 import client as NeutronClientFactory
from keystoneclient.v3 import client as KeystoneClientFactory

ADMIN_USER_ID = "cd761c068199487898fa1d7b9edb1cff"
ADMIN_USER_PASSWORD = "admin"
ADMIN_PROJECT_ID = "47b4db36d1584adebec7031623356dd9"


class CustomOpenstackClient:
    def __init__(self, keystone_url, glance_url, neutron_url):
        self.keystone_url = keystone_url
        self.glance_url = glance_url
        self.neutron_url = neutron_url

        self.default_images = self._get_images()
        self.created_images = []

        self.default_volumes = self._get_volumes()
        self.created_volumes = []

        self.test_network_id = self._create_test_network()
        self.default_networks = self._get_networks()

        self.test_flavor_id = self._create_test_flavor()
        self.default_flavors = self._get_flavors()
        self.default_servers = self._get_servers()

        self.default_users = self._get_users()
        self.created_users = []

    def cleanup(self):
        self._cleanup_images()
        self._cleanup_volumes()
        self._cleanup_networks()
        self._cleanup_flavors()
        self._cleanup_users()

    # --------------------------------------------------------------------
    #                           Keystone stuff
    # --------------------------------------------------------------------

    def _authenticate(self):
        auth = v3.Password(auth_url=self.keystone_url,
                           user_id=ADMIN_USER_ID,
                           password=ADMIN_USER_PASSWORD,
                           project_id=ADMIN_PROJECT_ID)
        return session.Session(auth=auth)

    def _get_users(self):
        session = self._authenticate()
        keystone = KeystoneClientFactory.Client(token=session.get_token(), endpoint=self.keystone_url)

        users = keystone.users.list()
        return [{"id": user.id} for user in users]

    def generate_users(self, nof_users):
        session = self._authenticate()
        keystone = KeystoneClientFactory.Client(token=session.get_token(), endpoint=self.keystone_url)

        if len(self.default_users) + len(self.created_users) < nof_users:
            nof_users_to_create = nof_users - len(self.default_users) - len(self.created_users)
            for i in range(0, nof_users_to_create):
                rand_hash = random.getrandbits(128)
                user = keystone.users.create(name="horizon_load_test_user_%032x" % rand_hash)
                self.created_users.append({"id": user.id})
        elif len(self.default_users) + len(self.created_users) > nof_users:
            nof_users_to_delete = len(self.default_users) + len(self.created_users) - nof_users
            if nof_users_to_delete > len(self.created_users):
                raise Exception("Cannot delete such number of users")
            for i in range(nof_users_to_delete):
                user_to_delete = self.created_users.pop()
                print "deleting user {}".format(str(user_to_delete))
                keystone.users.delete(user_to_delete["id"])

    def _cleanup_users(self):
        session = self._authenticate()
        keystone = KeystoneClientFactory.Client(token=session.get_token(), endpoint=self.keystone_url)
        for user in self.created_users:
            keystone.users.delete(user["id"])

    # --------------------------------------------------------------------
    #                           Glance stuff
    # --------------------------------------------------------------------

    def _get_images(self):
        session = self._authenticate()
        glance = GlanceClient('1', endpoint=self.glance_url, token=session.get_token())

        images = glance.images.list()
        return [{"id": image.id} for image in images]

    def _wait_for_image_status(self, glance, image_id, status):
        while True:
            image = glance.images.get(image_id)
            if status == image.status:
                break
            else:
                time.sleep(1)

    def _delete_image(self, image_id):
        session = self._authenticate()
        glance = GlanceClient('1', endpoint=self.glance_url, token=session.get_token())
        glance.images.delete(image_id)

    def _cleanup_images(self):
        session = self._authenticate()
        glance = GlanceClient('1', endpoint=self.glance_url, token=session.get_token())
        for image in self.created_images:
            glance.images.delete(image["id"])

    def generate_images(self, nof_images):
        if len(self.default_images) + len(self.created_images) < nof_images:
            session = self._authenticate()
            glance = GlanceClient('1', endpoint=self.glance_url, token=session.get_token())

            create_kw = {
                "container_format": "bare",
                "disk_format": "qcow2",
                "name": "horizon_load_test_image",
                "copy_from": "http://172.16.44.5/cirros-0.3.1-x86_64-disk.img"
            }

            nof_images_to_create = nof_images - len(self.default_images) - len(self.created_images)
            for i in range(0, nof_images_to_create):
                image = glance.images.create(**create_kw)
                self._wait_for_image_status(glance, image.id, "active")
                self.created_images.append({"id": image.id})

        elif len(self.default_images) + len(self.created_images) > nof_images:
            nof_images_to_delete = len(self.default_images) + len(self.created_images) - nof_images
            if nof_images_to_delete > len(self.created_images):
                raise Exception("Cannot delete such number of images")
            for i in range(nof_images_to_delete):
                image_to_delete = self.created_images.pop()
                self._delete_image(image_to_delete["id"])

    # --------------------------------------------------------------------
    #                           Cinder stuff
    # --------------------------------------------------------------------

    def _get_volumes(self):
        session = self._authenticate()
        cinder = CinderClient(session=session)

        volumes = cinder.volumes.list()
        return [{"id": volume.id} for volume in volumes]

    def _wait_for_volume_status(self, cinder, volume_id, status):
        while True:
            volume = cinder.volumes.get(volume_id)
            if status == volume.status:
                break
            else:
                time.sleep(1)

    def _delete_volume(self, volume_id):
        session = self._authenticate()
        cinder = CinderClient(session=session)
        cinder.volumes.delete(volume_id)

    def _cleanup_volumes(self):
        session = self._authenticate()
        cinder = CinderClient(session=session)
        for volume in self.created_volumes:
            cinder.volumes.delete(volume["id"])

    def generate_volumes(self, nof_volumes):
        if len(self.default_volumes) + len(self.created_volumes) < nof_volumes:
            session = self._authenticate()
            cinder = CinderClient(session=session)

            nof_volumes_to_create = nof_volumes - len(self.default_volumes) - len(self.created_volumes)
            for i in range(0, nof_volumes_to_create):
                volume = cinder.volumes.create(size=1, name="horizon_load_test_volume")
                self._wait_for_volume_status(cinder, volume.id, "available")
                self.created_volumes.append({"id": volume.id})

        elif len(self.default_volumes) + len(self.created_volumes) > nof_volumes:
            nof_volumes_to_create = len(self.default_volumes) + len(self.created_volumes) - nof_volumes
            if nof_volumes_to_create > len(self.created_volumes):
                raise Exception("Cannot delete such number of volumes")
            for i in range(nof_volumes_to_create):
                volume_to_delete = self.created_volumes.pop()
                self._delete_volume(volume_to_delete["id"])

    # --------------------------------------------------------------------
    #                           Nova stuff
    # --------------------------------------------------------------------

    def _get_servers(self):
        session = self._authenticate()
        nova = NovaClientFactory.Client("2.0", session=session)

        servers = nova.servers.list()
        return [{"id": server.id} for server in servers]

    def _get_flavors(self):
        session = self._authenticate()
        nova = NovaClientFactory.Client("2.0", session=session)

        flavors = nova.flavors.list()
        return [{"id": flavor.id} for flavor in flavors]

    def _create_test_flavor(self):
        session = self._authenticate()
        nova = NovaClientFactory.Client("2.0", session=session)

        flavor = nova.flavors.create(name="horizon_load_test_flavor_for_servers",
                                     ram=64,
                                     vcpus=1,
                                     disk=1)
        return flavor.id

    def _cleanup_flavors(self):
        session = self._authenticate()
        nova = NovaClientFactory.Client("2.0", session=session)

        flavor = nova.flavors.get(self.test_flavor_id)
        nova.flavors.delete(flavor)

    # --------------------------------------------------------------------
    #                           Neutron stuff
    # --------------------------------------------------------------------

    def _get_networks(self):
        session = self._authenticate()
        neutron = NeutronClientFactory.Client(version="2",
                                              endpoint_url=self.neutron_url,
                                              token=session.get_token())

        networks = neutron.list_networks()
        return [{"id": network["id"]} for network in networks["networks"]]

    def _create_test_network(self):
        session = self._authenticate()
        neutron = NeutronClientFactory.Client(version="2",
                                              endpoint_url=self.neutron_url,
                                              token=session.get_token())

        network = {"name": "horizon_load_test_network_for_servers", "admin_state_up": True}
        neutron.create_network({"network": network})
        networks = neutron.list_networks(name="horizon_load_test_network_for_servers")
        network_id = networks['networks'][0]['id']
        subnet = {"network_id": network_id, "cidr": "10.0.0.0/24", "ip_version": 4}
        neutron.create_subnet({"subnet": subnet})
        return network_id

    def _cleanup_networks(self):
        session = self._authenticate()
        neutron = NeutronClientFactory.Client(version="2",
                                              endpoint_url=self.neutron_url,
                                              token=session.get_token())
        # delete test network
        neutron.delete_network(self.test_network_id)
