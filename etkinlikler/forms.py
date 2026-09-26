from django import forms
from .models import Etkinlik


class EtkinlikForm(forms.ModelForm):
    class Meta:
        model = Etkinlik
        fields = ['baslik', 'tur', 'yil', 'yarisma_adi', 'basari', 'ogretmenler', 'ogrenciler', 'icerik', 'fotograf']
