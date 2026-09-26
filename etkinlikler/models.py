from django.db import models
from django.contrib.auth.models import User

class Etkinlik(models.Model):
    ETKINLIK_TURLERI = (
        ('proje', 'Proje'),
        ('etkinlik', 'Etkinlik'),
        ('gezi', 'Gezi'),
        ('spor', 'Sportif Müsabaka'),
        ('diger', 'Diğer'),
    )

    baslik = models.CharField(max_length=200, verbose_name="Etkinlik/Proje Adı")
    tur = models.CharField(max_length=50, choices=ETKINLIK_TURLERI, default='proje', verbose_name="Türü")
    yil = models.IntegerField(verbose_name="Yapıldığı Yıl")
    yarisma_adi = models.CharField(max_length=200, blank=True, null=True, verbose_name="Başvurulan Yarışma (Varsa)")
    basari = models.TextField(blank=True, null=True, verbose_name="Elde Edilen Başarı / Derece / Ödül")
    ogretmenler = models.TextField(verbose_name="Hazırlayan Öğretmenler")
    ogrenciler = models.TextField(verbose_name="Hazırlayan Öğrenciler")
    icerik = models.TextField(verbose_name="İçerik ve Detaylar")
    fotograf = models.ImageField(upload_to='etkinlik_fotograflari/', blank=True, null=True, verbose_name="Kapak Fotoğrafı")
    
    ekleyen = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Sisteme Giren Kullanıcı")
    kayit_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")
    onaylandi = models.BooleanField(default=False, verbose_name="Onay Durumu")

    class Meta:
        verbose_name = "Etkinlik/Proje"
        verbose_name_plural = "Etkinlikler ve Projeler"
        ordering = ['-yil', '-kayit_tarihi']

    def __str__(self):
        return f"{self.baslik} ({self.yil})"


class EtkinlikFotograf(models.Model):
    etkinlik = models.ForeignKey(Etkinlik, on_delete=models.CASCADE, related_name='fotograflar', verbose_name="İlgili Faaliyet")
    fotograf = models.ImageField(upload_to='etkinlik_fotograflari/', verbose_name="Fotoğraf")
    yuklenme_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Faaliyet Fotoğrafı"
        verbose_name_plural = "Faaliyet Fotoğrafları"
