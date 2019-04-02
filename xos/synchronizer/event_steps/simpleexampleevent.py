
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


import json
from xossynchronizer.event_steps.eventstep import EventStep
from xosconfig import Config
from multistructlog import create_logger

log = create_logger(Config().get('logging'))


class SimpleExampleEventStep(EventStep):
    topics = ["SimpleExampleEvent"]
    technology = "kafka"

    def __init__(self, *args, **kwargs):
        super(SimpleExampleEventStep, self).__init__(*args, **kwargs)

    def process_event(self, event):
        value = json.loads(event.value)
        service_instance_name = value["service_instance"]
        tenant_message = value["tenant_message"]

        objs = self.model_accessor.SimpleExampleServiceInstance.objects.filter(name=service_instance_name)
        if not objs:
            raise Exception("failed to find %s" % service_instance_name)

        for obj in objs:
            obj.tenant_message = tenant_message
            obj.save(always_update_timestamp=True)
