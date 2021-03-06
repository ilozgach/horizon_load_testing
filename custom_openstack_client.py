import time
import random
from keystoneclient import session
from keystoneclient.auth.identity import v3
from glanceclient import Client as GlanceClient
from cinderclient.v2 import Client as CinderClient
from novaclient import client as NovaClientFactory
from neutronclient.v2_0 import client as NeutronClientFactory
from keystoneclient.v3 import client as KeystoneClientFactory


class CustomOpenstackClient:
    def __init__(self, conf):
        self.admin_user_id = conf["admin_user_id"]
        self.admin_user_password = conf["admin_user_password"]
        self.admin_project_id = conf["admin_project_id"]
        self.keystone_url = conf["keystone_public_url"]
        self.glance_url = conf["glance_public_url"]
        self.neutron_url = conf["neutron_public_url"]

        self.test_image = self._create_test_image()
        self.default_images = self._get_images()
        self.created_images = []

        self.test_volume = self._create_test_volume()
        self.default_volumes = self._get_volumes()
        self.created_volumes = []
        self.default_volume_snapshots = self._get_volume_snapshots()
        self.created_volume_snapshots = []

        self.test_network = self._create_test_network()
        self.default_networks = self._get_networks()
        self.created_networks = []
        self.default_routers = self._get_routers()
        self.created_routers = []

        self.test_flavor = self._create_test_flavor()
        self.default_flavors = self._get_flavors()
        self.created_flavors = []
        self.default_servers = self._get_servers()
        self.created_servers = []

        self.default_users = self._get_users()
        self.created_users = []
        self.default_projects = self._get_projects()
        self.created_projects = []

    def _get_neutron_client(self):
        session = self._authenticate()
        neutron = NeutronClientFactory.Client(version="2",
                                              endpoint_url=self.neutron_url,
                                              token=session.get_token())
        return neutron

    def cleanup(self):
        self._cleanup_servers()
        self._cleanup_images()
        self._cleanup_volume_snapshots()
        self._cleanup_volumes()
        self._cleanup_networks()
        self._cleanup_routers()
        self._cleanup_flavors()
        self._cleanup_users()
        self._cleanup_projects()

    # --------------------------------------------------------------------
    #                           Keystone stuff
    # --------------------------------------------------------------------

    def _authenticate(self):
        auth = v3.Password(auth_url=self.keystone_url,
                           user_id=self.admin_user_id,
                           password=self.admin_user_password,
                           project_id=self.admin_project_id)
        return session.Session(auth=auth)

    def _get_users(self):
        session = self._authenticate()
        keystone = KeystoneClientFactory.Client(token=session.get_token(), endpoint=self.keystone_url)

        users = keystone.users.list()
        return [user for user in users]

    def generate_users(self, nof_users):
        session = self._authenticate()
        keystone = KeystoneClientFactory.Client(token=session.get_token(), endpoint=self.keystone_url)

        if len(self.default_users) + len(self.created_users) < nof_users:
            nof_users_to_create = nof_users - len(self.default_users) - len(self.created_users)
            for i in range(0, nof_users_to_create):
                rand_hash = random.getrandbits(128)
                user = keystone.users.create(name="horizon_load_test_user_%032x" % rand_hash)
                self.created_users.append(user)
        elif len(self.default_users) + len(self.created_users) > nof_users:
            nof_users_to_delete = len(self.default_users) + len(self.created_users) - nof_users
            if nof_users_to_delete > len(self.created_users):
                raise Exception("Cannot delete such number of users")
            for i in range(nof_users_to_delete):
                user_to_delete = self.created_users.pop()
                keystone.users.delete(user_to_delete.id)

    def _cleanup_users(self):
        session = self._authenticate()
        keystone = KeystoneClientFactory.Client(token=session.get_token(), endpoint=self.keystone_url)
        for user in self.created_users:
            keystone.users.delete(user.id)

    def _get_projects(self):
        session = self._authenticate()
        keystone = KeystoneClientFactory.Client(token=session.get_token(), endpoint=self.keystone_url)

        projects = keystone.projects.list()
        return [project for project in projects]

    def generate_projects(self, nof_projects):
        session = self._authenticate()
        keystone = KeystoneClientFactory.Client(token=session.get_token(), endpoint=self.keystone_url)

        if len(self.default_projects) + len(self.created_projects) < nof_projects:
            nof_projects_to_create = nof_projects - len(self.default_projects) - len(self.created_projects)
            for i in range(0, nof_projects_to_create):
                rand_hash = random.getrandbits(128)
                project = keystone.projects.create(name="horizon_load_test_project_%032x" % rand_hash,
                                                domain="default")
                self.created_projects.append(project)
        elif len(self.default_projects) + len(self.created_projects) > nof_projects:
            nof_projects_to_delete = len(self.default_projects) + len(self.created_projects) - nof_projects
            if nof_projects_to_delete > len(self.created_projects):
                raise Exception("Cannot delete such number of projects")
            for i in range(nof_projects_to_delete):
                project_to_delete = self.created_users.pop()
                keystone.users.delete(project_to_delete)

    def _cleanup_projects(self):
        session = self._authenticate()
        keystone = KeystoneClientFactory.Client(token=session.get_token(), endpoint=self.keystone_url)

        for project in self.created_projects:
            keystone.projects.delete(project)

    # --------------------------------------------------------------------
    #                           Glance stuff
    # --------------------------------------------------------------------

    def _get_images(self):
        session = self._authenticate()
        glance = GlanceClient('1', endpoint=self.glance_url, token=session.get_token())
        images = glance.images.list()
        return [image for image in images]

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
        glance.images.delete(self.test_image.id)
        for image in self.created_images:
            glance.images.delete(image.id)

    def _create_test_image(self):
        session = self._authenticate()
        glance = GlanceClient('1', endpoint=self.glance_url, token=session.get_token())

        create_kw = {
            "container_format": "bare",
            "disk_format": "qcow2",
            "name": "horizon_load_test_image_for_servers",
            "copy_from": "http://172.16.44.5/cirros-0.3.1-x86_64-disk.img"
        }

        image = glance.images.create(**create_kw)
        self._wait_for_image_status(glance, image.id, "active")
        return image

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
                self.created_images.append(image)

        elif len(self.default_images) + len(self.created_images) > nof_images:
            nof_images_to_delete = len(self.default_images) + len(self.created_images) - nof_images
            if nof_images_to_delete > len(self.created_images):
                raise Exception("Cannot delete such number of images")
            for i in range(nof_images_to_delete):
                image_to_delete = self.created_images.pop()
                self._delete_image(image_to_delete.id)

    # --------------------------------------------------------------------
    #                           Cinder stuff
    # --------------------------------------------------------------------

    def _get_volumes(self):
        session = self._authenticate()
        cinder = CinderClient(session=session)

        volumes = cinder.volumes.list()
        return [volume for volume in volumes]

    def _get_volume_snapshots(self):
        session = self._authenticate()
        cinder = CinderClient(session=session)

        snapshots = cinder.volume_snapshots.list()
        return [snapshot for snapshot in snapshots]

    def _create_test_volume(self):
        session = self._authenticate()
        cinder = CinderClient(session=session)
        volume = cinder.volumes.create(size=1, name="horizon_load_test_volume_for_snapshots")
        self._wait_for_volume_status(cinder, volume.id, "available")
        return volume

    def _wait_for_volume_status(self, cinder, volume_id, status):
        while True:
            volume = cinder.volumes.get(volume_id)
            if status == volume.status:
                break
            else:
                time.sleep(3)

    def _wait_for_volume_snapshot_status(self, cinder, volume_snapshot_id, status):
        while True:
            volume = cinder.volume_snapshots.get(volume_snapshot_id)
            if status == volume.status:
                break
            else:
                time.sleep(3)

    def _delete_volume(self, volume, cinder=None):
        if cinder is None:
            session = self._authenticate()
            cinder = CinderClient(session=session)

        cinder.volumes.delete(volume.id)
        while True:
            volumes = self._get_volumes()
            found = False
            for vlm in volumes:
                if vlm.id == volume.id:
                    found = True
            if not found:
                break
            time.sleep(3)

    def _cleanup_volumes(self):
        session = self._authenticate()
        cinder = CinderClient(session=session)
        self._delete_volume(self.test_volume)
        for volume in self.created_volumes:
            self._delete_volume(volume, cinder)

    def _delete_volume_snapshot(self, volume_snapshot, cinder=None):
        if cinder is None:
            session = self._authenticate()
            cinder = CinderClient(session=session)

        cinder.volume_snapshots.delete(volume_snapshot)
        while True:
            volume_snapshots = self._get_volume_snapshots()
            found = False
            for vsnap in volume_snapshots:
                if vsnap.id == volume_snapshot.id:
                    found = True
            if not found:
                break
            time.sleep(3)

    def _cleanup_volume_snapshots(self):
        session = self._authenticate()
        cinder = CinderClient(session=session)
        for volume_snapshot in self.created_volume_snapshots:
            self._delete_volume_snapshot(volume_snapshot, cinder)

    def generate_volumes(self, nof_volumes):
        if len(self.default_volumes) + len(self.created_volumes) < nof_volumes:
            session = self._authenticate()
            cinder = CinderClient(session=session)
            nof_volumes_to_create = nof_volumes - len(self.default_volumes) - len(self.created_volumes)
            for i in range(0, nof_volumes_to_create):
                volume = cinder.volumes.create(size=1, name="horizon_load_test_volume")
                self._wait_for_volume_status(cinder, volume.id, "available")
                self.created_volumes.append(volume)

        elif len(self.default_volumes) + len(self.created_volumes) > nof_volumes:
            nof_volumes_to_delete = len(self.default_volumes) + len(self.created_volumes) - nof_volumes
            if nof_volumes_to_delete > len(self.created_volumes):
                raise Exception("Cannot delete such number of volumes")
            for i in range(nof_volumes_to_delete):
                volume_to_delete = self.created_volumes.pop()
                self._delete_volume(volume_to_delete)

    def generate_volume_snapshots(self, nof_snapshots):
        if len(self.default_volume_snapshots) + len(self.created_volume_snapshots) < nof_snapshots:
            session = self._authenticate()
            cinder = CinderClient(session=session)
            nof_volume_snapshots_to_create = nof_snapshots - len(self.default_volume_snapshots) - len(self.created_volume_snapshots)
            for i in range(0, nof_volume_snapshots_to_create):
                volume_snapshot = cinder.volume_snapshots.create(self.test_volume.id)
                self._wait_for_volume_snapshot_status(cinder, volume_snapshot.id, "available")
                self.created_volume_snapshots.append(volume_snapshot)
        elif len(self.default_volume_snapshots) + len(self.created_volume_snapshots) > nof_snapshots:
            nof_volume_snapshots_to_delete = len(self.default_volume_snapshots) + len(self.created_volume_snapshots) - nof_snapshots
            if nof_volume_snapshots_to_delete > len(self.created_volume_snapshots):
                raise Exception("Cannot delete such number of volume snapshots")
            for i in range(nof_volume_snapshots_to_delete):
                volume_snapshot_to_delete = self.created_volume_snapshots.pop()
                self._delete_volume_snapshot(volume_snapshot_to_delete)

    # --------------------------------------------------------------------
    #                           Nova stuff
    # --------------------------------------------------------------------

    def _get_servers(self):
        session = self._authenticate()
        nova = NovaClientFactory.Client("2.0", session=session)

        return nova.servers.list()

    def _get_flavors(self):
        session = self._authenticate()
        nova = NovaClientFactory.Client("2.0", session=session)

        flavors = nova.flavors.list()
        return [flavor for flavor in flavors]

    def _create_test_flavor(self):
        session = self._authenticate()
        nova = NovaClientFactory.Client("2.0", session=session)

        flavor = nova.flavors.create(name="horizon_load_test_flavor_for_servers",
                                     ram=64,
                                     vcpus=1,
                                     disk=1)
        return flavor

    def _delete_flavor(self, flavor, nova=None):
        if nova is None:
            session = self._authenticate()
            nova = NovaClientFactory.Client("2.0", session=session)

        nova.flavors.delete(flavor)
        while True:
            flavors = self._get_flavors()
            found = False
            for flv in flavors:
                if flv.id == flavor.id:
                    found = True
            if not found:
                break
            time.sleep(3)

    def _cleanup_flavors(self):
        session = self._authenticate()
        nova = NovaClientFactory.Client("2.0", session=session)
        self._delete_flavor(self.test_flavor)
        for flavor in self.created_flavors:
            self._delete_flavor(flavor)

    def generate_instances(self, nof_instances):
        if len(self.default_servers) + len(self.created_servers) < nof_instances:
            session = self._authenticate()
            nova = NovaClientFactory.Client("2.0", session=session)
            nof_instances_to_create = nof_instances - len(self.default_servers) - len(self.created_servers)
            for i in range(0, nof_instances_to_create):
                server = nova.servers.create("horizon_load_test_server",
                                             self.test_image,
                                             self.test_flavor,
                                             nics=[{"net-id": self.test_network["id"]}])
                self.created_servers.append(server)
        elif len(self.default_servers) + len(self.created_servers) > nof_instances:
            nof_servers_to_delete = len(self.default_servers) + len(self.created_servers) - nof_instances
            if nof_servers_to_delete > len(self.created_servers):
                raise Exception("Cannot delete such number of instances")
            for i in range(nof_servers_to_delete):
                server_to_delete = self.created_servers.pop()
                self._delete_server(server_to_delete)

    def _delete_server(self, server, nova=None):
        if nova is None:
            session = self._authenticate()
            nova = NovaClientFactory.Client("2.0", session=session)

        nova.servers.delete(server)
        while True:
            servers = self._get_servers()
            found = False
            for srv in servers:
                if srv.id == server.id:
                    found = True
            if not found:
                break
            time.sleep(3)

    def _cleanup_servers(self):
        session = self._authenticate()
        nova = NovaClientFactory.Client("2.0", session=session)
        for server in self.created_servers:
            self._delete_server(server, nova)

    def generate_flavors(self, nof_flavors):
        if len(self.default_flavors) + len(self.created_flavors) < nof_flavors:
            session = self._authenticate()
            nova = NovaClientFactory.Client("2.0", session=session)
            nof_flavors_to_create = nof_flavors - len(self.default_flavors) - len(self.created_flavors)
            for i in range(0, nof_flavors_to_create):
                rand_hash = random.getrandbits(128)
                flavor = nova.flavors.create(name="horizon_load_test_flavor_%032x" % rand_hash,
                                             ram=64,
                                             vcpus=1,
                                             disk=1)
                self.created_flavors.append(flavor)
        elif len(self.default_flavors) + len(self.created_flavors) > nof_flavors:
            nof_flavors_to_delete = len(self.default_flavors) + len(self.created_flavors) - nof_flavors
            if nof_flavors_to_delete > len(self.created_flavors):
                raise Exception("Cannot delete such number of flavors")
            for i in range(nof_flavors_to_delete):
                flavor_to_delete = self.created_flavors.pop()
                self._delete_flavor(flavor_to_delete)

    # --------------------------------------------------------------------
    #                           Neutron stuff
    # --------------------------------------------------------------------

    def _get_networks(self):
        neutron = self._get_neutron_client()

        networks = neutron.list_networks()
        return [network for network in networks["networks"]]

    def _get_routers(self):
        neutron = self._get_neutron_client()

        routers = neutron.list_routers()
        return [router for router in routers["routers"]]

    def _create_test_network(self):
        neutron = self._get_neutron_client()

        network = {"name": "horizon_load_test_network_for_servers", "admin_state_up": True}
        neutron.create_network({"network": network})
        networks = neutron.list_networks(name=network["name"])
        network = networks["networks"][0]
        subnet = {"network_id": network["id"], "cidr": "10.0.0.0/24", "ip_version": 4}
        neutron.create_subnet({"subnet": subnet})
        return network

    def _cleanup_networks(self):
        neutron = self._get_neutron_client()

        neutron.delete_network(self.test_network["id"])
        for network in self.created_networks:
            neutron.delete_network(network["id"])

    def _cleanup_routers(self):
        neutron = self._get_neutron_client()

        for router in self.created_routers:
            neutron.delete_router(router["id"])

    def generate_networks(self, nof_networks):
        neutron = self._get_neutron_client()

        if len(self.default_networks) + len(self.created_networks) < nof_networks:
            nof_networks_to_create = nof_networks - len(self.default_networks) - len(self.created_networks)
            for i in range(0, nof_networks_to_create):
                network = neutron.create_network({"network": {"name": "horizon_load_test_network", "admin_state_up": True}})
                self.created_networks.append(network["network"])
        elif len(self.default_networks) + len(self.created_networks) > nof_networks:
            nof_networks_to_delete = len(self.default_networks) + len(self.created_networks) - nof_networks
            if nof_networks_to_delete > len(self.created_networks):
                raise Exception("Cannot delete such number of networks")
            for i in range(nof_networks_to_delete):
                network_to_delete = self.created_networks.pop()
                neutron.delete_network(network_to_delete["id"])

    def generate_routers(self, nof_routers):
        neutron = self._get_neutron_client()

        if len(self.default_routers) + len(self.created_routers) < nof_routers:
            nof_routers_to_create = nof_routers - len(self.default_routers) - len(self.created_routers)
            for i in range(0, nof_routers_to_create):
                router = neutron.create_router({"router": {"name": "horizon_load_test_router", "admin_state_up": True}})
                self.created_routers.append(router["router"])
        elif len(self.default_routers) + len(self.created_routers) > nof_routers:
            nof_routers_to_delete = len(self.default_routers) + len(self.created_routers) - nof_routers
            if nof_routers_to_delete > len(self.created_routers):
                raise Exception("Cannot delete such number of routers")
            for i in range(nof_routers_to_delete):
                router_to_delete = self.created_routers.pop()
                neutron.delete_router(router_to_delete["id"])
