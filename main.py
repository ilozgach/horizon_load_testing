import unittest
import urlparse

import ddt as ddt
import time
from selenium import webdriver

from custom_openstack_client import CustomOpenstackClient

KEYSTONE_PUBLIC_URL = "http://172.16.54.195:5000/v3"
GLANCE_PUBLIC_URL = "http://172.16.54.195:9292/v1"
HORIZON_BASE_URL = "http://172.16.54.195/horizon/"


@ddt.ddt
class HorizonLoadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = CustomOpenstackClient(KEYSTONE_PUBLIC_URL, GLANCE_PUBLIC_URL)

        cls.driver = webdriver.Chrome()
        login_url = urlparse.urljoin(HORIZON_BASE_URL, "auth/login")
        cls.driver.get(login_url)

        input_password = cls.driver.find_element_by_id("id_password")
        if input_password is not None:
            input_login = cls.driver.find_element_by_id("id_username")

            input_login.send_keys("admin")
            input_password.send_keys("admin")
            cls.driver.find_element_by_id("loginBtn").click()

    @classmethod
    def tearDownClass(cls):
        cls.client.cleanup()

    @ddt.data(
        {"nof_images": 3},
    )
    @ddt.unpack
    def test_admin_images_page(self, nof_images):
        self.client.generate_images(nof_images)

        images_url = urlparse.urljoin(HORIZON_BASE_URL, "admin/images")
        ts = time.time()
        self.driver.get(images_url)
        te = time.time()
        count_span = self.driver.find_element_by_class_name("table_count")
        self.assertEquals(count_span.text, "Displaying {} items".format(nof_images))
        print '%d images loaded in %2.2f sec' % (nof_images, te - ts)
