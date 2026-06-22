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
URUNLER = [
    {
        "isim": "İşlemeli Pullu Şort Etek",
        "url": "https://www.zara.com/tr/tr/islemeli-pullu-sort-etek-p03666094.html?v1=512893564",
        "hedef_beden": "S",
    },
    {
        "isim": "Peplum Pensli Üst",
        "url": "https://www.zara.com/tr/tr/peplum-pensli-ust-p02610769.html?v1=515228351",
        "hedef_beden": "M",
    },
    {
        "isim": "Kısa Kollu Düğmeli Top",
        "url": "https://www.zara.com/tr/tr/kisa-kollu-dugmeli-top-p02162272.html?v1=547356735",
        "hedef_beden": "S",
    },
    {
        "isim": "Kısa Kollu Düğmeli Top",
        "url": "https://www.zara.com/tr/tr/kisa-kollu-dugmeli-top-p02162272.html?v1=547356735",
        "hedef_beden": "M",
    },
    {
        "isim": "Oversize Poplin Gömlek",
        "url": "https://www.zara.com/tr/tr/oversize-poplin-gomlek-p02620695.html?v1=515236464",
        "hedef_beden": "S",
    },
    {
        "isim": "Oversize Poplin Gömlek",
        "url": "https://www.zara.com/tr/tr/oversize-poplin-gomlek-p02620695.html?v1=515236464",
        "hedef_beden": "M",
    },
    {
        "isim": "Dantel Detaylı Saten Şort",
        "url": "https://www.zara.com/tr/tr/dantel-detayli-saten-sort-p01165117.html?v1=548196693",
        "hedef_beden": "XS",
    },
    {
        "isim": "Dantel Detaylı Saten Şort",
        "url": "https://www.zara.com/tr/tr/dantel-detayli-saten-sort-p01165117.html?v1=548196693",
        "hedef_beden": "S",
    },
    {
        "isim": "Mini Çizgili Triko Elbise",
        "url": "https://www.zara.com/tr/tr/mini-cizgili-triko-elbise-p02142175.html?v1=526130439",
        "hedef_beden": "S",
    },
    {
        "isim": "Basic Poplin Gömlek",
        "url": "https://www.zara.com/tr/tr/basic-poplin-gomlek-p00387060.html?v1=551481783",
        "hedef_beden": "M",
    },
]

# Kontrol aralığı (saniye cinsinden)
KONTROL_ARALIGI = 5 * 60

# Takibin otomatik duracağı tarih-saat (YYYY-MM-DD HH:MM:SS)
TAKIP_BITIS_TARIHI = "2026-06-25 23:59:59"

# ============================================================
# BİLDİRİM AYARLARI
# ============================================================

GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

MASAUSTU_BILDIRIM = not GITHUB_ACTIONS
SESLI_BILDIRIM = not GITHUB_ACTIONS

EPOSTA_BILDIRIM = False
EPOSTA_AYARLARI = {
    "smtp_sunucu": "smtp.gmail.com",
    "smtp_port": 587,
    "gonderen_eposta": "sizin_emailiniz@gmail.com",
    "gonderen_sifre": "uygulama_sifresi",
    "alici_eposta": "bildirim_alacak@gmail.com",
}

TELEGRAM_BILDIRIM = bool(os.getenv("TELEGRAM_BOT_TOKEN"))
TELEGRAM_AYARLARI = {
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", "BOT_TOKEN_BURAYA"),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID", "CHAT_ID_BURAYA"),
}

# ============================================================
# İSTEK AYARLARI
# ============================================================

TEKRAR_DENEME = 3
LOG_DOSYASI = "stok_takip.log"
DURUM_DOSYASI = "stok_durum.json"
