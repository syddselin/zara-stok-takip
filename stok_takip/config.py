# ============================================================
# ZARA STOK TAKİP SİSTEMİ - YAPILANDIRMA DOSYASI
# ============================================================
import os
from pathlib import Path


def _env_dosyasi_yukle():
    """.env dosyasındaki değişkenleri (varsa) ortama yükler."""
    adaylar = [
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]

    for yol in adaylar:
        if not yol.exists():
            continue

        for satir in yol.read_text(encoding="utf-8").splitlines():
            satir = satir.strip()
            if not satir or satir.startswith("#") or "=" not in satir:
                continue

            anahtar, deger = satir.split("=", 1)
            anahtar = anahtar.strip()
            deger = deger.strip().strip('"').strip("'")

            # Ortamda varsa ezme
            os.environ.setdefault(anahtar, deger)

        break


_env_dosyasi_yukle()

# Takip edilecek ürünler
# Her ürün için URL, isim ve hedef beden belirtin
URUNLER = [
    {
        "isim": "Düğmeli ve Bağcıklı 100% Keten Kimono",
        "url": "https://www.massimodutti.com/tr/dugmeli-ve-bagcıklı-100-keten-kimono-l06708939",
        "hedef_beden": "S",
    },
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
