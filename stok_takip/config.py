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
        "isim": "Kemerli Kareli Kısa Trençkot",
        "url": "https://shop.mango.com/tr/tr/p/kadın/ceket/kemerli-kareli-kısa-trenckot/37054100/08/00",
        "hedef_beden": "XS",
    },
    {
        "isim": "Kemerli Kareli Kısa Trençkot",
        "url": "https://shop.mango.com/tr/tr/p/kadın/ceket/kemerli-kareli-kısa-trenckot/37054100/08/00",
        "hedef_beden": "S",
    },
    {
        "isim": "Kemerli Kareli Kısa Trençkot",
        "url": "https://shop.mango.com/tr/tr/p/kadın/ceket/kemerli-kareli-kısa-trenckot/37054100/08/00",
        "hedef_beden": "M",
    },
]

# Kontrol aralığı (saniye cinsinden)
# 4 dakikada bir kontrol
KONTROL_ARALIGI = 4 * 60

# Takibin otomatik duracağı tarih-saat (YYYY-MM-DD HH:MM:SS)
# Eski tarih geçerse uygulama kontrolü hiç başlatmaz; gelecekte kalmalı.
TAKIP_BITIS_TARIHI = "2026-12-31 23:59:59"

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

# Telegram bildirimi — env variable varsa ve chat_id tanımlıysa otomatik aktif
_TELEGRAM_BOT = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
_TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Sadece hem token hem chat_id sağlanmışsa bildirimi etkinleştir
TELEGRAM_BILDIRIM = bool(
    _TELEGRAM_BOT and _TELEGRAM_CHAT and _TELEGRAM_BOT != "BOT_TOKEN_BURAYA" and _TELEGRAM_CHAT != "CHAT_ID_BURAYA"
)
TELEGRAM_AYARLARI = {
    "bot_token": _TELEGRAM_BOT or "BOT_TOKEN_BURAYA",
    "chat_id": _TELEGRAM_CHAT or "CHAT_ID_BURAYA",
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
