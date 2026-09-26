from django.contrib import admin
from .models import Etkinlik, EtkinlikFotograf


class EtkinlikFotografInline(admin.TabularInline):
    model = EtkinlikFotograf
    extra = 1


@admin.register(Etkinlik)
class EtkinlikAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'tur', 'yil', 'basari', 'onaylandi', 'ekleyen', 'kayit_tarihi')
    list_filter = ('onaylandi', 'tur', 'yil', 'ekleyen')
    search_fields = ('baslik', 'ogretmenler', 'ogrenciler', 'icerik', 'yarisma_adi', 'basari')
    readonly_fields = ('ekleyen',)
    inlines = [EtkinlikFotografInline]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.ekleyen = request.user
            if request.user.is_superuser:
                obj.onaylandi = True
        super().save_model(request, obj, form, change)
