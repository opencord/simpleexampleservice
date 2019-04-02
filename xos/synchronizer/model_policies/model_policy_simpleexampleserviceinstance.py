
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

import base64
import jinja2
import json
import os
from xossynchronizer.model_policies.policy import Policy

from xosconfig import Config
from multistructlog import create_logger

log = create_logger(Config().get('logging'))


class SimpleExampleServiceInstancePolicy(Policy):
    model_name = "SimpleExampleServiceInstance"

    def handle_create(self, service_instance):
        return self.handle_update(service_instance)

    def render_index(self, service_instance):
        service = service_instance.owner.leaf_model

        fields = {}
        fields['tenant_message'] = service_instance.tenant_message
        fields['service_message'] = service.service_message

        if service_instance.foreground_color:
            fields["foreground_color"] = service_instance.foreground_color.html_code

        if service_instance.background_color:
            fields["background_color"] = service_instance.background_color.html_code

        images = []
        for image in service_instance.embedded_images.all():
            images.append({"name": image.name,
                           "url": image.url})
        fields["images"] = images

        template_fn = os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(__file__))), "index.html.j2")
        template = jinja2.Template(open(template_fn).read())

        return template.render(fields)

    def handle_update(self, service_instance):
        if not service_instance.compute_instance:
            # TODO: Break dependency
            compute_service = self.model_accessor.KubernetesService.objects.first()
            compute_service_instance_class = self.model_accessor.Service.objects.get(
                id=compute_service.id
            ).get_service_instance_class()

            exampleservice = service_instance.owner.leaf_model

            # TODO: What if there is the wrong number of slices?
            slice = exampleservice.slices.first()

            # TODO: What if there is no default image?
            image = slice.default_image

            name = "simpleexampleserviceinstance-%s" % service_instance.id
            compute_service_instance = compute_service_instance_class(
                slice=slice, owner=compute_service, image=image, name=name, no_sync=True)
            compute_service_instance.save()

            # Create a configmap and attach it to the compute instance
            data = {"index.html": self.render_index(service_instance)}
            cfmap = self.model_accessor.KubernetesConfigMap(
                name="simpleexampleserviceinstance-map-%s" %
                service_instance.id, trust_domain=slice.trust_domain, data=json.dumps(data))
            cfmap.save()
            cfmap_mnt = self.model_accessor.KubernetesConfigVolumeMount(config=cfmap,
                                                                        service_instance=compute_service_instance,
                                                                        mount_path="/usr/local/apache2/htdocs")
            cfmap_mnt.save()

            # Create a secret and attach it to the compute instance
            data = {"service_secret.txt": base64.b64encode(str(exampleservice.service_secret)),
                    "tenant_secret.txt": base64.b64encode(str(service_instance.tenant_secret))}
            secret = self.model_accessor.KubernetesSecret(
                name="simpleexampleserviceinstance-secret-%s" %
                service_instance.id, trust_domain=slice.trust_domain, data=json.dumps(data))
            secret.save()
            secret_mnt = self.model_accessor.KubernetesSecretVolumeMount(
                secret=secret,
                service_instance=compute_service_instance,
                mount_path="/usr/local/apache2/secrets")
            secret_mnt.save()

            compute_service_instance.no_sync = False
            compute_service_instance.save(update_fields=["no_sync"])

            service_instance.compute_instance = compute_service_instance
            service_instance.save(update_fields=["compute_instance"])
        else:
            compute_instance = service_instance.compute_instance
            mnt = compute_instance.leaf_model.kubernetes_config_volume_mounts.first()
            config = mnt.config
            new_data = json.dumps({"index.html": self.render_index(service_instance)})
            if (new_data != config.data):
                config.data = new_data
                config.save(always_update_timestamp=True)
                # Force the Kubernetes syncstep
                compute_instance.save(always_update_timestamp=True)

    def handle_delete(self, service_instance):
        log.info("handle_delete")
        if service_instance.compute_instance:
            log.info("has a compute_instance")
            service_instance.compute_instance.delete()
            service_instance.compute_instance = None
            # TODO: I'm not sure we can save things that are being deleted...
            service_instance.save(update_fields=["compute_instance"])
