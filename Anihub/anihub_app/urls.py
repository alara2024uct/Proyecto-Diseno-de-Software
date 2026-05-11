from django.urls import path
from .views import CatalogView, ForumView

urlpatterns = [
    path('api/catalog/', CatalogView.as_view(), name='api-catalog'),
    path('api/forum/', ForumView.as_view(), name='api-forum'),
]
