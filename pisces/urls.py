"""pisces URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from asterism.views import PingView
from django.contrib import admin
from django.urls import include, path, re_path

from fetcher.views import FetchRunViewSet
from transformer.views import DataObjectUpdateByIdView, DataObjectViewSet

from .routers import PiscesRouter

router = PiscesRouter()
router.register(r'fetches', FetchRunViewSet, 'fetchrun')
router.register(r'objects', DataObjectViewSet, 'dataobject')


urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^index-complete/$', DataObjectUpdateByIdView.as_view(), name='index-action-complete'),
    path('status/', PingView.as_view(), name='ping'),
    path('', include(router.urls)),
]
