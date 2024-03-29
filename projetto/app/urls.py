from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.conf import settings

from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.routers import DefaultRouter

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from service.views.user_views import UserViewSet
from service.views.order_views import OrderViewSet
from service.views.ticket_views import TicketViewSet, TicketAttachmentViewSet
from service.views.freedom_views import FreedomCheckRequestViewSet, FreedomResultRequestViewSet

from residence.views import ResidenceViewSet, AttachmentViewSet, ClusterViewSet, FloorViewSet, ApartmentViewSet, \
                            LayoutViewSet, CityViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'residences', ResidenceViewSet)
router.register(r'attachments', AttachmentViewSet)
router.register(r'clusters', ClusterViewSet)
router.register(r'floors', FloorViewSet)
router.register(r'apartments', ApartmentViewSet)
router.register(r'layouts', LayoutViewSet)
router.register(r'cities', CityViewSet)
router.register(r'tickets', TicketViewSet)
router.register(r'ticket_attachments', TicketAttachmentViewSet)
router.register(r'freedom_check', FreedomCheckRequestViewSet)
router.register(r'freedom_result', FreedomResultRequestViewSet)

schema_view = get_schema_view(
   openapi.Info(
      title="Projetto Snippets API",
      default_version='v1',
      description="Projetto Backend API",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="a.ikayev@thefactory.kz"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path('', include(router.urls)),
]

urlpatterns += [
   re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

urlpatterns += [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/token/without-password/', TokenObtainPairWithoutPasswordView.as_view(), name='token_obtain_pair_without_password'),
]