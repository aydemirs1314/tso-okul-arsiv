import json
import logging
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

# Desteklenen Genel MQTT Brokerlar
MQTT_BROKERS = {
    'hivemq': {
        'name': 'HiveMQ (Tavsiye Edilen - Hızlı & Kararlı)',
        'host': 'broker.hivemq.com',
        'port': 1883,
        'ws_port': 8000,
    },
    'emqx': {
        'name': 'EMQX (Yedek - Halka Açık Test Sunucusu)',
        'host': 'broker.emqx.io',
        'port': 1883,
        'ws_port': 8083,
    },
    'mosquitto': {
        'name': 'Mosquitto (Test Sunucusu)',
        'host': 'test.mosquitto.org',
        'port': 1883,
        'ws_port': 8080,
    }
}

DEFAULT_TOPIC = "tso/okul/etkinlikler"


def send_mqtt_message(topic=DEFAULT_TOPIC, payload=None, broker_key='hivemq'):
    """
    Seçilen MQTT Broker'a (HiveMQ / EMQX / Mosquitto) JSON formatında mesaj yayınlar.
    """
    if payload is None:
        payload = {}

    broker_info = MQTT_BROKERS.get(broker_key, MQTT_BROKERS['hivemq'])
    host = broker_info['host']
    port = broker_info['port']

    try:
        # Paho MQTT Client v2 uyumlu
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(host, port, keepalive=10)
        
        message_str = json.dumps(payload, ensure_ascii=False)
        client.publish(topic, message_str, qos=1)
        client.disconnect()
        return True, f"Mesaj başarıyla {broker_info['name']} brokerına iletildi."
    except Exception as e:
        logger.error(f"MQTT Gönderme Hatası: {e}")
        return False, str(e)


def notify_new_etkinlik(etkinlik, broker_key='hivemq'):
    """
    Yeni bir faaliyet eklendiğinde veya onaylandığında IoT cihazlarına anlık bildirim fırlatır.
    """
    payload = {
        'event': 'yeni_etkinlik',
        'id': etkinlik.id,
        'baslik': etkinlik.baslik,
        'tur': etkinlik.get_tur_display(),
        'yil': etkinlik.yil,
        'yarisma': etkinlik.yarisma_adi or '',
        'basari': etkinlik.basari or '',
        'ogretmenler': etkinlik.ogretmenler,
        'ogrenciler': etkinlik.ogrenciler,
        'ekleyen': etkinlik.ekleyen.username if etkinlik.ekleyen else 'Sistem',
        'onay_durumu': 'Onaylandı' if etkinlik.onaylandi else 'Onay Bekliyor',
        'timestamp': str(etkinlik.kayit_tarihi),
    }
    
    topic = f"{DEFAULT_TOPIC}/yeni"
    return send_mqtt_message(topic=topic, payload=payload, broker_key=broker_key)
