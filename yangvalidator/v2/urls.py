# Copyright The IETF Trust 2021, All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = "Miroslav Kovac"
__copyright__ = "Copyright The IETF Trust 2021, All Rights Reserved"
__license__ = "Apache License, Version 2.0"
__email__ = "miroslav.kovac@pantheon.tech"

from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = 'yangvalidator'
urlpatterns = [
    path('validate', csrf_exempt(views.validate), name='validate'),
    path('draft', csrf_exempt(views.validate_doc), name='validate_draft'),
    path('rfc', csrf_exempt(views.validate_doc), name='validate_rfc'),
    path('upload-files-setup', csrf_exempt(views.upload_setup), name='upload_setup'),
    path('validator/<id>', csrf_exempt(views.upload_file), name='upload_file'),
    path('draft-validator/<id>', csrf_exempt(views.upload_draft_id), name='upload_draft_id'),
    path('draft-validator', csrf_exempt(views.upload_draft), name='upload_draft'),
    path('versions', csrf_exempt(views.versions), name='versions')
]
