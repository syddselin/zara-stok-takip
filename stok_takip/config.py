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
# Massimo Dutti ürünleri (geçici olarak pasif):
# {
#     "isim": "Yüksek Bel Geniş Paça Jean",
#     "url": "https://www.massimodutti.com/tr/yuksek-bel-genis-paca-jean-l05040940?pelement=56904167&banner=true",
#     "hedef_beden": "XS",
# },
# {
#     "isim": "Yüksek Bel Geniş Paça Jean",
#     "url": "https://www.massimodutti.com/tr/yuksek-bel-genis-paca-jean-l05040940?pelement=56904167&banner=true",
#     "hedef_beden": "S",
# },
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
    {
        "isim": "Bağcıklı Dekolteli Top",
        "url": "https://www.zara.com/tr/tr/bagcikli-dekolteli-top-p07521019.html?v1=503297735",
        "hedef_beden": "S",
    },
    {
        "isim": "Bağcıklı Dekolteli Top",
        "url": "https://www.zara.com/tr/tr/bagcikli-dekolteli-top-p07521019.html?v1=503297735",
        "hedef_beden": "M",
    },
    {
        "isim": "Kısa Kollu Düğmeli Top (v2)",
        "url": "https://www.zara.com/tr/tr/kisa-kollu-dugmeli-top-p02162272.html?v1=547356736",
        "hedef_beden": "S",
    },
    {
        "isim": "Kısa Kollu Düğmeli Top (v2)",
        "url": "https://www.zara.com/tr/tr/kisa-kollu-dugmeli-top-p02162272.html?v1=547356736",
        "hedef_beden": "M",
    },
    {
        "isim": "Pilili Dokumlu Pantolon",
        "url": "https://www.zara.com/tr/tr/pilili-dokumlu-pantolon-p03152410.html?v1=535973339",
        "hedef_beden": "XS",
    },
    {
        "isim": "Süslü Düğmeli Dokumlu Bluz ZW Collection",
        "url": "https://www.zara.com/tr/tr/suslu-dugmeli-dokumlu-bluz-zw-collection-p00340004.html?v1=535481971",
        "hedef_beden": "XS",
    },
    {
        "isim": "Çizgili Geniş Paça Pantolon",
        "url": "https://www.zara.com/tr/tr/cizgili-genis-paca-pantolon-p02785512.html?v1=527054741",
        "hedef_beden": "S",
    },
]

# Kontrol aralığı (saniye cinsinden)
# Token/limit dostu kullanım için 5 dakikada bir kontrol
KONTROL_ARALIGI = 5 * 60

# Takibin otomatik duracağı tarih-saat (YYYY-MM-DD HH:MM:SS)
# Eski tarih geçerse uygulama kontrolü hiç başlatmaz; gelecekte kalmalı.
TAKIP_BITIS_TARIHI = "2026-07-15 23:59:59"

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
