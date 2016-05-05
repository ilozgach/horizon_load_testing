import unittest
import urlparse

import ddt as ddt
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from custom_openstack_client import CustomOpenstackClient
from custom_report import CustomReport

KEYSTONE_PUBLIC_URL = "http://172.16.53.131:5000/v3"
GLANCE_PUBLIC_URL = "http://172.16.53.131:9292/v1"
NEUTRON_PUBLIC_URL = "http://172.16.53.131:9696"
HORIZON_BASE_URL = "http://172.16.53.131/horizon/"


@ddt.ddt
class HorizonLoadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = CustomReport()
        cls.client = CustomOpenstackClient(KEYSTONE_PUBLIC_URL, GLANCE_PUBLIC_URL, NEUTRON_PUBLIC_URL)

        cls.driver = webdriver.Chrome()

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()
        cls.client.cleanup()
        cls.report.write_results()

    def login_driver(self):
        login_url = urlparse.urljoin(HORIZON_BASE_URL, "auth/login")
        self.driver.get(login_url)

        try:
            input_password = self.driver.find_element_by_id("id_password")
            if input_password is not None:
                input_login = self.driver.find_element_by_id("id_username")

                input_login.send_keys("admin")
                input_password.send_keys("admin")
                self.driver.find_element_by_id("loginBtn").click()
        except NoSuchElementException:
            pass

    def set_number_of_items_per_page(self, nof_items):
        if nof_items > 1000:
            raise Exception("maximum number of items per page is 1000")

        settings_url = urlparse.urljoin(HORIZON_BASE_URL, "settings")
        self.driver.get(settings_url)
        input_pagesize = self.driver.find_element_by_id("id_pagesize")
        input_pagesize.clear()
        input_pagesize.send_keys(str(nof_items))
        btn_save = self.driver.find_element_by_class_name("btn")
        btn_save.click()

    def set_volumes_quota(self, nof_volumes):
        quotas_url = urlparse.urljoin(HORIZON_BASE_URL, "admin/defaults")
        self.driver.get(quotas_url)
        btn_update = self.driver.find_element_by_class_name("btn")
        btn_update.click()
        input_volumes = self.driver.find_element_by_id("id_volumes")
        input_volumes.clear()
        input_volumes.send_keys(str(nof_volumes))
        btn_update = self.driver.find_element_by_class_name("btn-primary")
        btn_update.click()


    # @ddt.data(
    #     # there test requires bin number of items per page
    #     {"nof_images": 10, "times": 20},
    #     {"nof_images": 30, "times": 20}
    # )
    # @ddt.unpack
    # def test_admin_images_page(self, nof_images, times):
    #     self.client.generate_images(nof_images)
    #     self.login_driver()

    #     images_url = urlparse.urljoin(HORIZON_BASE_URL, "admin/images")

    #     for i in range(0, times):
    #         ts = time.time()
    #         self.driver.get(images_url)
    #         te = time.time()
    #         count_span = self.driver.find_element_by_class_name("table_count")
    #         self.assertEquals(count_span.text, "Displaying {} items".format(nof_images))

    #         self.report.add_result("admin/images", nof_images, te - ts)

    @ddt.data(
        # there test requires bin number of items per page
        {"nof_volumes": 10, "times": 20},
        {"nof_volumes": 30, "times": 20}
    )
    @ddt.unpack
    def test_admin_volumes_page(self, nof_volumes, times):
        self.client.generate_volumes(nof_volumes)
        self.login_driver()
        self.set_number_of_items_per_page(nof_volumes)

        volumes_url = urlparse.urljoin(HORIZON_BASE_URL, "admin/volumes")

        for i in range(0, times):
            ts = time.time()
            self.driver.get(volumes_url)
            te = time.time()
            count_span = self.driver.find_element_by_class_name("table_count")
            self.assertEquals(count_span.text, "Displaying {} items".format(nof_volumes))

            self.report.add_result("admin/volumes", nof_volumes, te - ts)

    # @ddt.data(
    #     {"nof_users": 10, "times": 20},
    #     {"nof_users": 30, "times": 20}
    # )
    # @ddt.unpack
    # def test_identity_users_page(self, nof_users, times):
    #     self.client.generate_users(nof_users)
    #     self.login_driver()

    #     users_url = urlparse.urljoin(HORIZON_BASE_URL, "identity/users")

    #     for i in range(0, times):
    #         ts = time.time()
    #         self.driver.get(users_url)
    #         te = time.time()
    #         count_span = self.driver.find_element_by_class_name("table_count")
    #         self.assertEquals(count_span.text, "Displaying {} items".format(nof_users))

    #         self.report.add_result("identity/users", nof_users, te - ts)
