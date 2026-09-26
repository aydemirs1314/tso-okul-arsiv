from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from etkinlikler import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', views.dashboard_view, name='dashboard'),
    path('ekle/', views.etkinlik_ekle_view, name='etkinlik_ekle'),
    path('kayitlar/', views.etkinlik_listesi_view, name='etkinlik_listesi'),
    path('kayit/<int:pk>/', views.etkinlik_detay_view, name='etkinlik_detay'),
    path('kayit-sil/<int:pk>/', views.etkinlik_sil_view, name='etkinlik_sil'),
    path('kayit-onayla/<int:pk>/', views.etkinlik_onayla_view, name='etkinlik_onayla'),
    path('onay-bekleyenler/', views.onay_bekleyenler_view, name='onay_bekleyenler'),
    # IoT & MQTT Kontrol Merkezi
    path('iot/', views.mqtt_panel_view, name='mqtt_panel'),
    # Kullanıcı Yönetimi
    path('yonetim/kullanicilar/', views.kullanici_listesi_view, name='kullanici_listesi'),
    path('yonetim/kullanici-ekle/', views.kullanici_ekle_view, name='kullanici_ekle'),
    path('yonetim/kullanici-sil/<int:pk>/', views.kullanici_sil_view, name='kullanici_sil'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
