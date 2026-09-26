import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from .models import Etkinlik, EtkinlikFotograf
from .forms import EtkinlikForm
from .mqtt import MQTT_BROKERS, DEFAULT_TOPIC, send_mqtt_message, notify_new_etkinlik


def is_admin(user):
    return user.is_superuser


@login_required
def dashboard_view(request):
    user = request.user
    
    # Onaylı kayıtlar üzerinden istatistikler
    onayli_kayitlar = Etkinlik.objects.filter(onaylandi=True)
    toplam_proje = onayli_kayitlar.filter(tur='proje').count()
    toplam_etkinlik = onayli_kayitlar.filter(tur='etkinlik').count()
    toplam_spor = onayli_kayitlar.filter(tur='spor').count()
    toplam_gezi = onayli_kayitlar.filter(tur='gezi').count()
    toplam_kayit = onayli_kayitlar.count()

    # Onay bekleyenler (Yönetici için)
    onay_bekleyen_sayisi = Etkinlik.objects.filter(onaylandi=False).count()

    # Yıllara göre dağılım
    yil_istatistik = (
        onayli_kayitlar.values('yil')
        .annotate(sayi=Count('id'))
        .order_by('-yil')
    )
    yil_verileri = json.dumps(list(yil_istatistik))

    # Kategori dağılımı
    tur_mapping = dict(Etkinlik.ETKINLIK_TURLERI)
    tur_istatistik = (
        onayli_kayitlar.values('tur')
        .annotate(sayi=Count('id'))
        .order_by('tur')
    )
    tur_verileri = json.dumps([
        {'tur': tur_mapping.get(item['tur'], item['tur']), 'sayi': item['sayi']}
        for item in tur_istatistik
    ])

    # Mevcut yıllar listesi
    mevcut_yillar = list(onayli_kayitlar.values_list('yil', flat=True).distinct().order_by('-yil'))

    context = {
        'toplam_proje': toplam_proje,
        'toplam_etkinlik': toplam_etkinlik,
        'toplam_spor': toplam_spor,
        'toplam_gezi': toplam_gezi,
        'toplam_kayit': toplam_kayit,
        'onay_bekleyen_sayisi': onay_bekleyen_sayisi,
        'today': timezone.now(),
        'yil_verileri': yil_verileri,
        'tur_verileri': tur_verileri,
        'mevcut_yillar': mevcut_yillar,
    }
    return render(request, 'dashboard.html', context)


@login_required
def etkinlik_ekle_view(request):
    if request.method == 'POST':
        form = EtkinlikForm(request.POST, request.FILES)
        if form.is_valid():
            etkinlik = form.save(commit=False)
            etkinlik.ekleyen = request.user
            
            if request.user.is_superuser:
                etkinlik.onaylandi = True
                messages.success(request, '✅ Proje/Etkinlik başarıyla yayınlandı!')
            else:
                etkinlik.onaylandi = False
                messages.info(request, '⏳ Projeniz kaydedildi ve yönetici onayına iletildi.')
            
            etkinlik.save()

            # Birden fazla fotoğrafları kaydet
            fotograflar = request.FILES.getlist('fotograflar')
            for f in fotograflar:
                EtkinlikFotograf.objects.create(etkinlik=etkinlik, fotograf=f)

            # MQTT Üzerinden IoT / Akıllı Cihazlara Anlık Bildirim Gönder
            try:
                notify_new_etkinlik(etkinlik)
            except Exception:
                pass

            return redirect('dashboard')
    else:
        form = EtkinlikForm()
    return render(request, 'etkinlikler/etkinlik_form.html', {'form': form})


@login_required
def etkinlik_listesi_view(request):
    user = request.user
    if user.is_superuser:
        qs = Etkinlik.objects.all()
    else:
        qs = Etkinlik.objects.filter(Q(onaylandi=True) | Q(ekleyen=user))

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(baslik__icontains=q) |
            Q(ogretmenler__icontains=q) |
            Q(ogrenciler__icontains=q) |
            Q(icerik__icontains=q) |
            Q(yarisma_adi__icontains=q) |
            Q(basari__icontains=q) |
            Q(yil__icontains=q)
        )

    tur = request.GET.get('tur', '').strip()
    if tur:
        qs = qs.filter(tur=tur)

    yil = request.GET.get('yil', '').strip()
    if yil and yil.isdigit():
        qs = qs.filter(yil=int(yil))

    kayitlar = qs.order_by('-yil', '-kayit_tarihi')
    tum_yillar = Etkinlik.objects.filter(onaylandi=True).values_list('yil', flat=True).distinct().order_by('-yil')

    context = {
        'kayitlar': kayitlar,
        'q': q,
        'secili_tur': tur,
        'secili_yil': int(yil) if yil and yil.isdigit() else None,
        'tum_yillar': tum_yillar,
        'toplam_sonuc': kayitlar.count(),
    }
    return render(request, 'etkinlikler/etkinlik_listesi.html', context)


@login_required
def etkinlik_detay_view(request, pk):
    etkinlik = get_object_or_404(Etkinlik, pk=pk)
    
    if not etkinlik.onaylandi and not request.user.is_superuser and etkinlik.ekleyen != request.user:
        messages.warning(request, 'Bu kayıt henüz yönetici tarafından onaylanmamıştır.')
        return redirect('dashboard')
    
    ek_fotograflar = etkinlik.fotograflar.all().order_by('yuklenme_tarihi')

    context = {
        'etkinlik': etkinlik,
        'ek_fotograflar': ek_fotograflar,
    }
    return render(request, 'etkinlikler/etkinlik_detay.html', context)


@login_required
def etkinlik_sil_view(request, pk):
    etkinlik = get_object_or_404(Etkinlik, pk=pk)
    if request.user.is_superuser or etkinlik.ekleyen == request.user:
        baslik = etkinlik.baslik
        etkinlik.delete()
        messages.success(request, f'🗑️ "{baslik}" başarıyla sistemden kaldırıldı.')
    else:
        messages.error(request, 'Bu kaydı silme yetkiniz bulunmuyor!')
    return redirect('etkinlik_listesi')


@login_required
@user_passes_test(is_admin)
def etkinlik_onayla_view(request, pk):
    etkinlik = get_object_or_404(Etkinlik, pk=pk)
    etkinlik.onaylandi = True
    etkinlik.save()
    
    # Onaylandığında da MQTT bildirimi fırlat
    try:
        notify_new_etkinlik(etkinlik)
    except Exception:
        pass

    messages.success(request, f'✅ "{etkinlik.baslik}" onaylandı ve arşive eklendi! (MQTT yayını yapıldı)')
    return redirect('onay_bekleyenler')


@login_required
@user_passes_test(is_admin)
def onay_bekleyenler_view(request):
    kayitlar = Etkinlik.objects.filter(onaylandi=False).order_by('-kayit_tarihi')
    return render(request, 'etkinlikler/onay_bekleyenler.html', {'kayitlar': kayitlar})


# ===== IoT & MQTT KONTROL MERKEZİ =====

@login_required
def mqtt_panel_view(request):
    secili_broker = request.GET.get('broker', 'hivemq')
    test_sonucu = None

    if request.method == 'POST':
        secili_broker = request.POST.get('broker', 'hivemq')
        test_mesaji = request.POST.get('mesaj', 'TSO Arşiv IoT Test Mesajı')
        
        payload = {
            'tip': 'test_mesaji',
            'gonderen': request.user.username,
            'mesaj': test_mesaji,
            'zaman': str(timezone.now())
        }
        
        basarili, sonuc_metni = send_mqtt_message(
            topic=f"{DEFAULT_TOPIC}/test",
            payload=payload,
            broker_key=secili_broker
        )
        test_sonucu = {
            'basarili': basarili,
            'mesaj': sonuc_metni,
            'broker': MQTT_BROKERS.get(secili_broker, {}).get('name', secili_broker),
            'topic': f"{DEFAULT_TOPIC}/test"
        }

    broker_bilgi = MQTT_BROKERS.get(secili_broker, MQTT_BROKERS['hivemq'])

    context = {
        'brokers': MQTT_BROKERS,
        'secili_broker': secili_broker,
        'broker_bilgi': broker_bilgi,
        'default_topic': DEFAULT_TOPIC,
        'test_sonucu': test_sonucu,
    }
    return render(request, 'etkinlikler/mqtt_panel.html', context)


# ===== KULLANICI YÖNETİMİ (Sadece Admin) =====

@login_required
@user_passes_test(is_admin)
def kullanici_listesi_view(request):
    kullanicilar = User.objects.all().order_by('-date_joined')
    return render(request, 'yonetim/kullanici_listesi.html', {'kullanicilar': kullanicilar})


@login_required
@user_passes_test(is_admin)
def kullanici_ekle_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'"{user.username}" kullanıcısı başarıyla oluşturuldu!')
            return redirect('kullanici_listesi')
    else:
        form = UserCreationForm()
    return render(request, 'yonetim/kullanici_ekle.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def kullanici_sil_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        messages.error(request, 'Yönetici hesabı silinemez!')
    else:
        username = user.username
        user.delete()
        messages.success(request, f'"{username}" kullanıcısı silindi.')
    return redirect('kullanici_listesi')
