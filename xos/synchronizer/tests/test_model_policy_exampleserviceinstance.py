
# Copyright 2017-present Open Networking Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Tests for SimpleExampleServiceInstance model policies

import base64
import json
import os
import sys
import unittest
from mock import patch, PropertyMock, ANY, MagicMock
from unit_test_common import setup_sync_unit_test


class TestSimpleExampleServiceInstancePolicy(unittest.TestCase):

    def setUp(self):
        self.unittest_setup = setup_sync_unit_test(os.path.abspath(os.path.dirname(os.path.realpath(__file__))),
                                                   globals(),
                                                   [("simpleexampleservice", "simpleexampleservice.xproto"),
                                                    ("kubernetes-service", "kubernetes.xproto")] )

        self.MockObjectList = self.unittest_setup["MockObjectList"]

        sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(__file__))), "../model_policies"))

        from model_policy_simpleexampleserviceinstance import SimpleExampleServiceInstancePolicy
        self.policy_class = SimpleExampleServiceInstancePolicy

        self.service = SimpleExampleService(service_message="hello", service_secret="p@ssw0rd")
        self.k8s_service = KubernetesService(id=1111)
        self.k8s_service.get_service_instance_class=MagicMock(return_value=KubernetesServiceInstance)
        self.trust_domain = TrustDomain(owner=self.k8s_service, name="test-trust")
        self.image = Image(name="test-image", tag="1.2", kind="container")
        self.slice = Slice(trust_domain=self.trust_domain, service=self.service, default_image = self.image)
        self.service.slices = self.MockObjectList([self.slice])

    def tearDown(self):
        sys.path = self.unittest_setup["sys_path_save"]

    def test_policy_create(self):
        with patch.object(KubernetesService.objects, "get_items") as k8s_service_objects, \
                patch.object(Service.objects, "get_items") as service_objects, \
                patch.object(KubernetesServiceInstance, "save", autospec=True) as ksi_save, \
                patch.object(KubernetesConfigMap, "save", autospec=True) as kcfm_save, \
                patch.object(KubernetesConfigVolumeMount, "save", autospec=True) as kcfm_mnt_save, \
                patch.object(KubernetesSecret, "save", autospec=True) as ksec_save, \
                patch.object(KubernetesSecretVolumeMount, "save", autospec=True) as ksec_mnt_save:
            k8s_service_objects.return_value = [self.k8s_service]
            service_objects.return_value = [self.k8s_service, self.service]

            si = SimpleExampleServiceInstance(name="test-simple-instance",
                                              id=1112,
                                              owner=self.service, tenant_message="world", tenant_secret="l3tm31n")
            si.embedded_images = self.MockObjectList([])

            step = self.policy_class()

            desired_data = json.dumps({"index.html": step.render_index(si)})

            desired_secret_data = json.dumps({"service_secret.txt": base64.b64encode("p@ssw0rd"),
                                              "tenant_secret.txt": base64.b64encode("l3tm31n")})

            step.handle_create(si)

            # Saved twice, once with no_sync=True and once with no_sync=False
            self.assertEqual(ksi_save.call_count, 2)
            saved_ksi = ksi_save.call_args[0][0]
            self.assertEqual(saved_ksi.slice, self.slice)
            self.assertEqual(saved_ksi.owner, self.k8s_service)
            self.assertEqual(saved_ksi.image, self.image)
            self.assertEqual(saved_ksi.name, "simpleexampleserviceinstance-1112")

            # Config Map
            self.assertEqual(kcfm_save.call_count, 1)
            saved_cfm = kcfm_save.call_args[0][0]
            self.assertEqual(saved_cfm.name, "simpleexampleserviceinstance-map-1112")
            self.assertEqual(saved_cfm.trust_domain, self.trust_domain)
            self.assertEqual(saved_cfm.data, desired_data)

            # Mouhnt of Config Map to Service Instance
            self.assertEqual(kcfm_mnt_save.call_count, 1)
            saved_cfm_mnt = kcfm_mnt_save.call_args[0][0]
            self.assertEqual(saved_cfm_mnt.config, saved_cfm)
            self.assertEqual(saved_cfm_mnt.service_instance, saved_ksi)

            # Secret
            self.assertEqual(ksec_save.call_count, 1)
            saved_sec = ksec_save.call_args[0][0]
            self.assertEqual(saved_sec.name, "simpleexampleserviceinstance-secret-1112")
            self.assertEqual(saved_sec.trust_domain, self.trust_domain)
            self.assertEqual(saved_sec.data, desired_secret_data)

            # Mount of Secret to Service Instance
            self.assertEqual(ksec_mnt_save.call_count, 1)
            saved_sec_mnt = ksec_mnt_save.call_args[0][0]
            self.assertEqual(saved_sec_mnt.secret, saved_sec)
            self.assertEqual(saved_sec_mnt.service_instance, saved_ksi)

    def test_policy_update(self):
        with patch.object(KubernetesService.objects, "get_items") as k8s_service_objects, \
                patch.object(Service.objects, "get_items") as service_objects, \
                patch.object(KubernetesServiceInstance, "save", autospec=True) as ksi_save, \
                patch.object(KubernetesConfigMap, "save", autospec=True) as kcfm_save, \
                patch.object(KubernetesConfigVolumeMount, "save", autospec=True) as kcfm_mnt_save, \
                patch.object(KubernetesSecret, "save", autospec=True) as ksec_save, \
                patch.object(KubernetesSecretVolumeMount, "save", autospec=True) as ksec_mnt_save:
            k8s_service_objects.return_value = [self.k8s_service]
            service_objects.return_value = [self.k8s_service, self.service]

            si = SimpleExampleServiceInstance(name="test-simple-instance",
                                              id=1112,
                                              owner=self.service, tenant_message="world", tenant_secret="l3tm31n")
            si.embedded_images = self.MockObjectList([])

            ksi = KubernetesServiceInstance(owner=self.k8s_service, slice=self.slice, image=self.image,
                                            name="simpleexampleserviceinstance-1112")

            cfm = KubernetesConfigMap(trust_domain=self.trust_domain, name="simpleexampleserviceinstance-map-1112",
                                      data="junk")

            cfm_mnt = KubernetesConfigVolumeMount(config=cfm, service_instance=ksi)

            si.compute_instance = ksi
            ksi.kubernetes_config_volume_mounts = self.MockObjectList([cfm_mnt])

            step = self.policy_class()

            desired_data = json.dumps({"index.html": step.render_index(si)})

            step.handle_update(si)

            self.assertEqual(ksi_save.call_count, 1)

            # Config Map
            self.assertEqual(kcfm_save.call_count, 1)
            saved_cfm = kcfm_save.call_args[0][0]
            self.assertEqual(saved_cfm.name, "simpleexampleserviceinstance-map-1112")
            self.assertEqual(saved_cfm.trust_domain, self.trust_domain)
            self.assertEqual(saved_cfm.data, desired_data)

            self.assertEqual(kcfm_mnt_save.call_count, 0)
            self.assertEqual(ksec_save.call_count, 0)
            self.assertEqual(ksec_mnt_save.call_count, 0)

    def test_policy_update_no_difference(self):
        with patch.object(KubernetesService.objects, "get_items") as k8s_service_objects, \
                patch.object(Service.objects, "get_items") as service_objects, \
                patch.object(KubernetesServiceInstance, "save", autospec=True) as ksi_save, \
                patch.object(KubernetesConfigMap, "save", autospec=True) as kcfm_save, \
                patch.object(KubernetesConfigVolumeMount, "save", autospec=True) as kcfm_mnt_save, \
                patch.object(KubernetesSecret, "save", autospec=True) as ksec_save, \
                patch.object(KubernetesSecretVolumeMount, "save", autospec=True) as ksec_mnt_save:
            k8s_service_objects.return_value = [self.k8s_service]
            service_objects.return_value = [self.k8s_service, self.service]

            step = self.policy_class()

            si = SimpleExampleServiceInstance(name="test-simple-instance",
                                              id=1112,
                                              owner=self.service, tenant_message="world", tenant_secret="l3tm31n")
            si.embedded_images = self.MockObjectList([])

            desired_data = json.dumps({"index.html": step.render_index(si)})

            ksi = KubernetesServiceInstance(owner=self.k8s_service, slice=self.slice, image=self.image,
                                            name="simpleexampleserviceinstance-1112")

            cfm = KubernetesConfigMap(trust_domain=self.trust_domain, name="simpleexampleserviceinstance-map-1112",
                                      data=desired_data)

            cfm_mnt = KubernetesConfigVolumeMount(config=cfm, service_instance=ksi)

            si.compute_instance = ksi
            ksi.kubernetes_config_volume_mounts = self.MockObjectList([cfm_mnt])

            step.handle_update(si)

            self.assertEqual(ksi_save.call_count, 0)
            self.assertEqual(kcfm_save.call_count, 0)
            self.assertEqual(kcfm_mnt_save.call_count, 0)
            self.assertEqual(ksec_save.call_count, 0)
            self.assertEqual(ksec_mnt_save.call_count, 0)

    def test_policy_delete(self):
        with patch.object(KubernetesServiceInstance, "delete", autospec=True) as ksi_delete, \
                patch.object(SimpleExampleServiceInstance, "save", autospec=True) as sesi_save:
            si = SimpleExampleServiceInstance(name="test-simple-instance",
                                              id=1112,
                                              owner=self.service, tenant_message="world", tenant_secret="l3tm31n")

            ksi = KubernetesServiceInstance(owner=self.k8s_service, slice=self.slice, image=self.image,
                                            name="simpleexampleserviceinstance-1112")
            si.compute_instance = ksi

            step = self.policy_class()

            step.handle_delete(si)

            # The compute instance should have been deleted
            self.assertEqual(ksi_delete.call_count, 1)
            deleted_ksi = ksi_delete.call_args[0][0]
            self.assertEqual(deleted_ksi, ksi)

            # The serviceInstance should have had its compute_instance set to none
            self.assertEqual(si.compute_instance.None)

            # The SimpleExampleServiceInstance should have been saved
            self.assertEqual(sesi_save.call_count, 1)

if __name__ == '__main__':
    unittest.main()
