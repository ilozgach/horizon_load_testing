import unittest
import urlparse

import ddt as ddt
import time
from selenium import webdriver

from custom_openstack_client import CustomOpenstackClient
from custom_report import CustomReport

KEYSTONE_PUBLIC_URL = "http://172.16.54.195:5000/v3"
GLANCE_PUBLIC_URL = "http://172.16.54.195:9292/v1"
NEUTRON_PUBLIC_URL = "http://172.16.54.195:9696"
HORIZON_BASE_URL = "http://172.16.54.195/horizon/"


@ddt.ddt
class HorizonLoadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = CustomReport()
        cls.client = CustomOpenstackClient(KEYSTONE_PUBLIC_URL, GLANCE_PUBLIC_URL, NEUTRON_PUBLIC_URL)

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
        cls.driver.close()
        cls.client.cleanup()
        cls.report.write_results()

    @ddt.data(
        {"nof_images": 3, "times": 10},
        {"nof_images": 5, "times": 10}
    )
    @ddt.unpack
    def test_admin_images_page(self, nof_images, times):
        self.client.generate_images(nof_images)

        images_url = urlparse.urljoin(HORIZON_BASE_URL, "admin/images")

        for i in range(0, times):
            ts = time.time()
            self.driver.get(images_url)
            te = time.time()
            count_span = self.driver.find_element_by_class_name("table_count")
            self.assertEquals(count_span.text, "Displaying {} items".format(nof_images))

            self.report.add_result("admin/images", nof_images, te - ts)

    @ddt.data(
        {"nof_volumes": 3, "times": 10},
        {"nof_volumes": 5, "times": 10}
    )
    @ddt.unpack
    def test_admin_volumes_page(self, nof_volumes, times):
        self.client.generate_volumes(nof_volumes)

        volumes_url = urlparse.urljoin(HORIZON_BASE_URL, "admin/volumes")

        for i in range(0, times):
            ts = time.time()
            self.driver.get(volumes_url)
            te = time.time()
            count_span = self.driver.find_element_by_class_name("table_count")
            self.assertEquals(count_span.text, "Displaying {} items".format(nof_volumes))

            self.report.add_result("admin/volumes", nof_volumes, te - ts)

    @ddt.data(
        {"nof_users": 10, "times": 10},
        {"nof_users": 20, "times": 10}
    )
    @ddt.unpack
    def test_identity_users_page(self, nof_users, times):
        self.client.generate_users(nof_users)

        users_url = urlparse.urljoin(HORIZON_BASE_URL, "identity/users")

        for i in range(0, times):
            ts = time.time()
            self.driver.get(users_url)
            te = time.time()
            count_span = self.driver.find_element_by_class_name("table_count")
            # confusing hack for heat_admin user which is not displaying on horizon users page
            # should not significally affect time of page load
            self.assertEquals(count_span.text, "Displaying {} items".format(nof_users - 1))

            self.report.add_result("identity/users", nof_users, te - ts)
