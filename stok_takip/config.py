# ============================================================
# ZARA STOK TAKİP SİSTEMİ - YAPILANDIRMA DOSYASI
# ============================================================
import os

# Takip edilecek Zara ürünleri
# Her ürün için URL, isim ve hedef beden belirtin
URUNLER = [
    {
        "isim": "Fiyonklu Dokulu Top",
        "url": "https://www.zara.com/tr/tr/fiyonklu-dokulu-top-p07521020.html?v1=505034866",
        "hedef_beden": "XS",
    },
    {
        "isim": "Fiyonklu Dokulu Top",
        "url": "https://www.zara.com/tr/tr/fiyonklu-dokulu-top-p07521020.html?v1=505034866",
        "hedef_beden": "S",
    },
    # Daha fazla ürün ekleyebilirsiniz:
    # {
    #     "isim": "Başka Ürün",
    #     "url": "https://www.zara.com/tr/tr/urun-p12345678.html?v1=...",
    #     "hedef_beden": "M",
    # },
]

# Kontrol aralığı (saniye cinsinden)
# Çok sık kontrol Zara tarafından engellenmenize neden olabilir
# Minimum 60 saniye önerilir
KONTROL_ARALIGI = 90  # 90 saniyede bir kontrol et

# ============================================================
# BİLDİRİM AYARLARI
# ============================================================

# GitHub Actions'da çalışıyorsak masaüstü/ses bildirimi kapansın
GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

# Masaüstü bildirimi (macOS/Windows/Linux) — CI'da otomatik kapalı
MASAUSTU_BILDIRIM = not GITHUB_ACTIONS

# Sesli bildirim — CI'da otomatik kapalı
SESLI_BILDIRIM = not GITHUB_ACTIONS

# E-posta bildirimi
EPOSTA_BILDIRIM = False
EPOSTA_AYARLARI = {
    "smtp_sunucu": "smtp.gmail.com",
    "smtp_port": 587,
    "gonderen_eposta": "sizin_emailiniz@gmail.com",
    "gonderen_sifre": "uygulama_sifresi",  # Gmail → Uygulama Şifreleri
    "alici_eposta": "bildirim_alacak@gmail.com",
}

# Telegram bildirimi — env variable varsa otomatik aktif
TELEGRAM_BILDIRIM = bool(os.getenv("TELEGRAM_BOT_TOKEN"))
TELEGRAM_AYARLARI = {
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", "BOT_TOKEN_BURAYA"),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID", "CHAT_ID_BURAYA"),
}

# ============================================================
# İSTEK AYARLARI
# ============================================================

# Hata durumunda tekrar deneme sayısı
TEKRAR_DENEME = 3

# Log dosyası
LOG_DOSYASI = "stok_takip.log"

# Durum dosyası (çalıştırmalar arası stok durumunu saklar)
DURUM_DOSYASI = "stok_durum.json"
