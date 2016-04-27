import time
from keystoneclient import session
from keystoneclient.auth.identity import v3
from glanceclient import Client as GlanceClient
from cinderclient.v2 import Client as CinderClient

class CustomOpenstackClient:
    def __init__(self, keystone_url, glance_url):
        self.keystone_url = keystone_url
        self.glance_url = glance_url

        self.default_images = self._get_images()
        self.created_images = []

        self.default_volumes = self._get_volumes()
        self.created_volumes = []

    # --------------------------------------------------------------------
    #                           Keystone stuff
    # --------------------------------------------------------------------

    def _authenticate(self):
        auth = v3.Password(auth_url='http://172.16.54.195:5000/v3',
                           user_id='b90cd04517a346de955af12bbbdf1ac9',
                           password='admin',
                           project_id='88418fb881a84b67b475c0ee5eadfd24')
        return session.Session(auth=auth)

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

    def cleanup(self):
        self._cleanup_images()
        self._cleanup_volumes()
