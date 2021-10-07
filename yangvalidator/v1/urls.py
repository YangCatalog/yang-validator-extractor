# Copyright The IETF Trust 2019, All Rights Reserved
# Copyright 2015 Cisco and its affiliates
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

"""yangvalidator URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

__author__ = "Miroslav Kovac, Carl Moberg"
__copyright__ = "Copyright 2015 Cisco and its affiliates, Copyright The IETF Trust 2019, All Rights Reserved"
__license__ = "Apache License, Version 2.0"
__email__ = "miroslav.kovac@pantheon.tech, camoberg@cisco.com"

from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = 'yangvalidator'
urlpatterns = [
    path('', views.index, name='index'),
    path('rest', views.rest, name='rest'),
    path('about', views.about, name='about'),
    path('draft/<draft>', views.validate_draft, name='validate_draft'),
    path('rfc/<rfc>', views.validate_rfc, name='validate_rfc'),
    path('api/draft/<draft>', views.json_validate_draft, name='json_validate_draft'),
    path('api/rfc/<rfc>', views.json_validate_rfc, name='json_validate_rfc'),
    path('api/versions', views.get_versions, name='get_versions'),
    path('api/v1/datatracker/draft', views.datatracker_draft, name='datatracker_draft'),
    path('api/v1/datatracker/rfc', views.datatracker_rfc, name='datatracker_rfc'),
    path('validator', views.upload_file, name='upload_file'),
    path('draft-validator', views.upload_draft, name='upload_draft'),
    path('draft', views.validate_draft_param, name='validate_draft'),
    path('rfc', views.validate_rfc_param, name='validate_rfc')
]
