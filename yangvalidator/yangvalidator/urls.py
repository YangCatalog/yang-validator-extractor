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
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views


app_name = 'yangvalidator'
urlpatterns = [
    path('', views.index, name='index'),
    path('/', views.index, name='index'),
    path('yangvalidator/', views.index, name='index'),
    path('yangvalidator/rest', views.rest, name='rest'),
    path('yangvalidator/about', views.about, name='about'),
    path('yangvalidator/draft/<draft>', views.validate_draft, name='validate_draft'),
    path('yangvalidator/rfc/<rfc>', views.validate_rfc, name='validate_rfc'),
    path('yangvalidator/api/draft/<draft>', views.json_validate_draft, name='json_validate_draft'),
    path('yangvalidator/api/rfc/<rfc>', views.json_validate_rfc, name='json_validate_rfc'),
    path('yangvalidator/api/versions', views.get_versions, name='get_versions'),
    path('yangvalidator/validator', views.upload_file, name='upload_file'),
    path('yangvalidator/draft-validator', views.upload_draft, name='upload_draft'),
    path('yangvalidator/draft', views.validate_draft_param, name='validate_draft'),
    path('yangvalidator/rfc', views.validate_rfc_param, name='validate_rfc'),
]
