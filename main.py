import json
import threading
import unittest
import urlparse

import ddt as ddt
import time

import os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from custom_openstack_client import CustomOpenstackClient
from custom_report import CustomReport

@ddt.ddt
class HorizonLoadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scr_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(scr_dir, "conf.json"), "r") as cf:
            cls.conf = json.load(cf)
        cls.report = CustomReport()
        cls.client = CustomOpenstackClient(cls.conf)

    @classmethod
    def tearDownClass(cls):
        cls.report.write_results()
        cls.client.cleanup()

    def login_driver(self, driver):
        login_url = urlparse.urljoin(self.conf["horizon_base_url"], "auth/login")
        driver.get(login_url)

        try:
            input_password = driver.find_element_by_id("id_password")
            if input_password is not None:
                input_login = driver.find_element_by_id("id_username")

                input_login.send_keys("admin")
                input_password.send_keys("admin")
                driver.find_element_by_id("loginBtn").click()
        except NoSuchElementException:
            pass

    def set_number_of_items_per_page(self, driver, nof_items):
        if nof_items > 1000:
            raise Exception("maximum number of items per page is 1000")

        settings_url = urlparse.urljoin(self.conf["horizon_base_url"], "settings")
        driver.get(settings_url)
        input_pagesize = driver.find_element_by_id("id_pagesize")
        input_pagesize.clear()
        input_pagesize.send_keys(str(nof_items))
        btn_save = driver.find_element_by_class_name("btn")
        btn_save.click()

    # def set_volumes_quota(self, nof_volumes):
    #     quotas_url = urlparse.urljoin(self.conf["horizon_base_url"], "admin/defaults")
    #     self.driver.get(quotas_url)
    #     btn_update = self.driver.find_element_by_class_name("btn")
    #     btn_update.click()
    #     input_volumes = self.driver.find_element_by_id("id_volumes")
    #     input_volumes.clear()
    #     input_volumes.send_keys(str(nof_volumes))
    #     btn_update = self.driver.find_element_by_class_name("btn-primary")
    #     btn_update.click()

    def worker(self, driver, page, nof_instances, times, results):
        for i in range(0, times):
            ts = time.time()
            driver.get(page)
            te = time.time()
            count_span = driver.find_element_by_class_name("table_count")

            self.assertTrue("Displaying {} items".format(nof_instances) in count_span.text)

            results.append(te - ts)

    @ddt.data(
        {"page": "admin/images",
         "instance_generator": "generate_images",
         "nof_instances": 100,
         "times": 100,
         "concurrency": 1},
        {"page": "admin/volumes",
         "instance_generator": "generate_volumes",
         "nof_instances": 100,
         "times": 100,
         "concurrency": 1},
        {"page": "project/volumes",
         "instance_generator": "generate_volumes",
         "nof_instances": 100,
         "times": 100,
         "concurrency": 1},
        {"page": "admin/volumes/?tab=volumes_group_tabs__snapshots_tab",
         "instance_generator": "generate_volume_snapshots",
         "nof_instances": 100,
         "times": 100,
         "concurrency": 1},
        {"page": "identity/users",
         "instance_generator": "generate_users",
         "nof_instances": 100,
         "times": 100,
         "concurrency": 1},
        {"page": "identity",
         "instance_generator": "generate_projects",
         "nof_instances": 100,
         "times": 100,
         "concurrency": 1},
        {"page": "admin/instances",
         "instance_generator": "generate_instances",
         "nof_instances": 100,
         "times": 100,
         "concurrency": 1},
        {"page": "project/instances",
         "instance_generator": "generate_instances",
         "nof_instances": 100,
         "times": 100,
         "concurrency": 1},
        {"page": "admin/networks",
         "instance_generator": "generate_networks",
         "nof_instances": 100,
         "times": 100,
         "concurrency": 1},
        {"page": "admin/routers",
         "instance_generator": "generate_routers",
         "nof_instances": 100,
         "times": 100,
         "concurrency": 1},
        {"page": "admin/flavors",
         "instance_generator": "generate_flavors",
         "nof_instances": 100,
         "times": 100,
         "concurrency": 1}
    )
    @ddt.unpack
    def test_admin_volume_snapshots_page(self, page, instance_generator, nof_instances, times, concurrency):
        page_url = urlparse.urljoin(self.conf["horizon_base_url"], page)
        getattr(self.client, instance_generator)(nof_instances)

        if concurrency == 1:
            driver = webdriver.Chrome()
            self.login_driver(driver)
            self.set_number_of_items_per_page(driver, nof_instances)

            results = []
            self.worker(driver, page_url, nof_instances, times, results)

            for result in results:
                self.report.add_result(page, nof_instances, result)

            driver.close()
        elif concurrency > 1:
            results = [[] for _ in xrange(0, concurrency)]
            drivers = [webdriver.Remote(self.conf["grid_url"], desired_capabilities={"browserName": "chrome"}) for _ in xrange(0, concurrency)]
            threads = [threading.Thread(target=self.worker, args=(drivers[i], page_url, nof_instances, times, results[i])) for i in xrange(0, concurrency)]

            for driver in drivers:
                self.login_driver(driver)
                self.set_number_of_items_per_page(driver, nof_instances)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            for result in results:
                for val in result:
                    self.report.add_result(page, nof_instances, val)

            for driver in drivers:
                driver.close()
