from django.urls import path
from .views import CustomUserCreate, BlacklistTokenUpdateView, ProtectedPage, SubscribeUser
from django.conf.urls import url


app_name = 'users'

urlpatterns = [
    url(r'^create/$', CustomUserCreate.as_view(), name="create_user"),
    url(r'^logout/blacklist/$', BlacklistTokenUpdateView.as_view(),
         name='blacklist'),
    # path('username/', GetUserName.as_view(), name="username"),
    url(r'^protected/$', ProtectedPage.as_view()),
    url(r'^subscribe/$', SubscribeUser.as_view()),
]