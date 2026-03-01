# 🛒 Stok Takip Sistemi

Zarada (veya herhangi bir e-ticaret sitesinde) stoğu olmayan ürünleri takip edip, stoğa girdiğinde otomatik bildirim gönderen Python uygulaması.

## 🚀 Kurulum

```bash
cd stok_takip
pip install -r requirements.txt
```

## ⚙️ Yapılandırma

`config.py` dosyasını düzenleyerek takip edilecek ürünleri ekleyin:

```python
URUNLER = [
    {
        "isim": "Zara Deri Ceket",
        "url": "https://www.zara.com/tr/tr/urun-p12345.html",
        "site": "generic",
    },
    {
        "isim": "Trendyol Ayakkabı",
        "url": "https://www.trendyol.com/urun/67890",
        "site": "trendyol",
    },
]
```

### Bildirim Kanalları

| Kanal | Açıklama | Ayar |
|-------|----------|------|
| 🖥️ Masaüstü | macOS/Windows/Linux bildirimi | `MASAUSTU_BILDIRIM = True` |
| 🔊 Sesli | Ses çalarak uyarı | `SESLI_BILDIRIM = True` |
| 📧 E-posta | Gmail SMTP ile e-posta | `EPOSTA_BILDIRIM = True` |
| 📱 Telegram | Telegram bot bildirimi | `TELEGRAM_BILDIRIM = True` |

## ▶️ Çalıştırma

```bash
# Sürekli takip (varsayılan - 60 saniyede bir kontrol)
python main.py

# Sadece bir kez kontrol et
python main.py --tek-seferlik
```

## 📁 Proje Yapısı

```
stok_takip/
├── main.py           # Ana çalıştırma dosyası
├── config.py         # Yapılandırma ayarları
├── stok_kontrol.py   # Stok durumu kontrol modülü
├── bildirim.py       # Bildirim gönderme modülü
├── requirements.txt  # Gerekli Python paketleri
└── README.md         # Bu dosya
```

## 📝 Nasıl Çalışır?

1. **İlk kontrol**: Tüm ürünlerin mevcut stok durumu kaydedilir
2. **Periyodik kontrol**: Belirlenen aralıkta ürünler tekrar kontrol edilir
3. **Stok değişikliği**: Ürün "stok dışı" → "stokta" geçiş yaparsa bildirim gönderilir
4. **Bildirim**: Aktif tüm kanallar üzerinden kullanıcıya haber verilir

## 🔧 Telegram Bildirimi Kurulumu

1. Telegram'da [@BotFather](https://t.me/BotFather) ile yeni bir bot oluşturun
2. Bot token'ını `config.py`'deki `TELEGRAM_AYARLARI["bot_token"]`'a yapıştırın
3. Bot'a bir mesaj gönderin, ardından `https://api.telegram.org/bot<TOKEN>/getUpdates` adresinden `chat_id`'yi bulun
4. `TELEGRAM_BILDIRIM = True` yapın

## 📧 Gmail E-posta Kurulumu

1. Google Hesabınızda "Uygulama Şifreleri" oluşturun
2. `config.py`'deki `EPOSTA_AYARLARI`'nı doldurun
3. `EPOSTA_BILDIRIM = True` yapın
