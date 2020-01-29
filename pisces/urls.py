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
from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import routers
from rest_framework.schemas import get_schema_view
from transformer.views import ArchivesSpaceTransformView
from fetcher.views import ArchivesSpaceFetchChangesView, ArchivesSpaceFetchURIView, FetchRunViewSet

router = routers.DefaultRouter()
router.register(r'fetches', FetchRunViewSet, 'fetchrun')

schema_view = get_schema_view(
      title="Pisces API",
      description="Endpoints for Pisces microservice application."
)


urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^fetch/archivesspace/changes/$', ArchivesSpaceFetchChangesView.as_view(), name='fetch-archivesspace-changes'),
    re_path(r'^fetch/archivesspace/uri/$', ArchivesSpaceFetchURIView.as_view(), name='fetch-archivesspace-uri'),
    re_path(r'^transform/archivesspace/$', ArchivesSpaceTransformView.as_view(), name='transform-archivesspace'),
    # path('find-by-id/', FindByIDView.as_view(), name='find-by-id'),
    # path('import/', ImportRunView.as_view(), name='import-data'),
    path('status/', include('health_check.api.urls')),
    path('schema/', schema_view, name='schema'),
    path('', include(router.urls)),
]
