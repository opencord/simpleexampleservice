
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


import os
import sys
from xossynchronizer.steps.syncstep import SyncStep
from xosconfig import Config
from multistructlog import create_logger

log = create_logger(Config().get('logging'))

class SyncSimpleExampleServiceInstance(SyncStep):
    observes = "SimpleExampleServiceInstance"
    requested_interval = 0

    def __init__(self, *args, **kwargs):
        super(SyncSimpleExampleServiceInstance, self).__init__(*args, **kwargs)

    def sync_record(self, o):
        # There's nothing to do at this time. Configuration of ExampleServiceInstance is handled by Kubernetes
        # through config maps, and that all happens in the model policy.
        #
        # TODO(smbaker): Consider deleting this sync step
        pass
