#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║              🛒  STOK TAKİP SİSTEMİ  🛒                    ║
║  Zarada stoğu olmayan ürünleri takip edip stoğa girdiğinde  ║
║  otomatik bildirim gönderir.                                ║
╚══════════════════════════════════════════════════════════════╝

Kullanım:
    python main.py                  # Normal çalıştırma
    python main.py --tek-seferlik   # Sadece bir kez kontrol et
"""

import sys
import time
import json
import signal
import logging
import logging.handlers
import argparse
from pathlib import Path
from datetime import datetime

# Proje dizinini path'e ekle
sys.path.insert(0, ".")

from config import URUNLER, KONTROL_ARALIGI, LOG_DOSYASI, DURUM_DOSYASI
from stok_kontrol import ZaraStokKontrol
from bildirim import BildirimGonderici


# ================================================================
# LOGLAMA AYARI
# ================================================================
def log_ayarla():
    """Hem dosyaya hem konsola log yazar."""
    logger = logging.getLogger("stok_takip")
    logger.setLevel(logging.INFO)

    # Konsol handler
    konsol = logging.StreamHandler()
    konsol.setLevel(logging.INFO)
    konsol_format = logging.Formatter(
        "%(asctime)s │ %(message)s", datefmt="%H:%M:%S"
    )
    konsol.setFormatter(konsol_format)

    # Dosya handler - Saatte bir döndür, en fazla 6 yedek tut
    dosya = logging.handlers.TimedRotatingFileHandler(
        LOG_DOSYASI,
        when="H",
        interval=1,
        backupCount=6,
        encoding="utf-8",
    )
    dosya.setLevel(logging.DEBUG)
    dosya_format = logging.Formatter(
        "%(asctime)s │ %(levelname)-8s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    dosya.setFormatter(dosya_format)

    logger.addHandler(konsol)
    logger.addHandler(dosya)

    return logger


# ================================================================
# STOK TAKİP MOTORU
# ================================================================
class StokTakipMotoru:
    """
    Ana stok takip döngüsü.
    Ürünleri periyodik olarak kontrol eder ve stok değişikliğinde
    bildirim gönderir.
    """

    def __init__(self):
        self.kontrol = ZaraStokKontrol()
        self.bildirim = BildirimGonderici()
        self.logger = logging.getLogger("stok_takip")

        # Her ürün+beden kombinasyonunun önceki stok durumunu sakla
        self.onceki_durumlar: dict[str, bool] = {}
        self.calisiyor = True

    # ─── Durum dosyası (çalıştırmalar arası hafıza) ───────────

    def _durum_yukle(self):
        """Önceki stok durumlarını dosyadan yükler (varsa)."""
        yol = Path(DURUM_DOSYASI)
        if yol.exists():
            try:
                self.onceki_durumlar = json.loads(yol.read_text("utf-8"))
                self.logger.info(
                    f"💾 Önceki durum yüklendi ({len(self.onceki_durumlar)} kayıt)"
                )
                return True
            except Exception as e:
                self.logger.warning(f"⚠️  Durum dosyası okunamadı: {e}")
        return False

    def _durum_kaydet(self):
        """Mevcut stok durumlarını dosyaya kaydeder."""
        try:
            Path(DURUM_DOSYASI).write_text(
                json.dumps(self.onceki_durumlar, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.logger.info("💾 Durum dosyası güncellendi")
        except Exception as e:
            self.logger.warning(f"⚠️  Durum dosyası kaydedilemedi: {e}")

    # ─── Ana döngü ────────────────────────────────────────────

    def baslat(self, tek_seferlik: bool = False):
        """
        Stok takip döngüsünü başlatır.

        Args:
            tek_seferlik: True ise sadece bir kez kontrol eder
        """
        self._banner_yazdir()

        if not URUNLER:
            self.logger.error(
                "❌ Takip edilecek ürün bulunamadı! config.py dosyasını düzenleyin."
            )
            return

        self.logger.info(f"📋 {len(URUNLER)} ürün takip ediliyor")
        self.logger.info(f"⏱️  Kontrol aralığı: {KONTROL_ARALIGI} saniye")
        for urun in URUNLER:
            self.logger.info(f"  👗 {urun['isim']} → Beden: {urun['hedef_beden']}")
        self.logger.info("─" * 55)

        try:
            if tek_seferlik:
                # Önceki durumu dosyadan yükle (GitHub Actions hafızası)
                onceki_var = self._durum_yukle()
                ilk_kontrol = not onceki_var

                if ilk_kontrol:
                    self.logger.info("🔍 İlk çalıştırma — durumlar kaydediliyor...")
                else:
                    self.logger.info("🔍 Stok kontrol ediliyor (önceki durumla karşılaştırılacak)...")

                self._tum_urunleri_kontrol_et(ilk_kontrol=ilk_kontrol)
                self._durum_kaydet()
                self.logger.info("✅ Tek seferlik kontrol tamamlandı.")
                return

            # Sürekli takip — her zamanki gibi
            self.logger.info("🔍 İlk kontrol yapılıyor (mevcut durumlar kaydediliyor)...")
            self._tum_urunleri_kontrol_et(ilk_kontrol=True)

            self.logger.info("─" * 55)
            self.logger.info("🔄 Sürekli takip başladı. Durdurmak için Ctrl+C")
            self.logger.info("─" * 55)

            while self.calisiyor:
                try:
                    time.sleep(KONTROL_ARALIGI)
                    self._tum_urunleri_kontrol_et(ilk_kontrol=False)
                except KeyboardInterrupt:
                    break
        finally:
            self.kontrol.kapat()

        self.logger.info("\n👋 Stok takip sistemi durduruldu.")

    def _tum_urunleri_kontrol_et(self, ilk_kontrol: bool = False):
        """Tüm ürünlerin stok durumunu kontrol eder."""
        zaman = datetime.now().strftime("%H:%M:%S")
        self.logger.info(f"\n🕐 [{zaman}] Kontrol başlıyor...")

        for urun in URUNLER:
            isim = urun["isim"]
            url = urun["url"]
            hedef_beden = urun["hedef_beden"]
            anahtar = f"{url}#{hedef_beden}"

            try:
                durum = self.kontrol.kontrol_et(url, hedef_beden)
                onceki = self.onceki_durumlar.get(anahtar, False)

                # Durum göstergeleri
                if durum.stokta_var:
                    simge = "✅"
                    durum_metin = "STOKTA"
                else:
                    simge = "❌"
                    durum_metin = "STOK DIŞI"

                fiyat_bilgisi = f" | 💰 {durum.fiyat}" if durum.fiyat else ""

                # Tüm bedenlerin özet tablosu
                beden_ozet = ""
                if durum.tum_bedenler:
                    beden_ozet = " | Bedenler: " + " ".join(
                        f"[{b}:{'✓' if s else '✗'}]"
                        for b, s in durum.tum_bedenler.items()
                    )

                self.logger.info(
                    f"  {simge} {isim} [{hedef_beden}]: {durum_metin}"
                    f"{fiyat_bilgisi}{beden_ozet}"
                )

                # STOK DEĞİŞİKLİĞİ TESPİTİ
                if not ilk_kontrol and not onceki and durum.stokta_var:
                    self.logger.info(
                        f"  🎉🎉🎉 {isim} [{hedef_beden}] STOĞA GİRDİ! "
                        f"Bildirim gönderiliyor..."
                    )
                    self.bildirim.bildirim_gonder(
                        f"{isim} - {hedef_beden}", url, durum.fiyat
                    )

                # Durumu güncelle
                self.onceki_durumlar[anahtar] = durum.stokta_var

            except Exception as e:
                self.logger.error(f"  ⚠️  {isim}: Kontrol hatası - {e}")

    def durdur(self, *args):
        """Takip döngüsünü durdurur (sinyal işleyici)."""
        self.calisiyor = False

    def _banner_yazdir(self):
        """Başlangıç banner'ını yazdırır."""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║              🛒  STOK TAKİP SİSTEMİ  🛒                    ║
║         Ürün stoğa girdiğinde anında bildirim al!           ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)


# ================================================================
# ANA GİRİŞ NOKTASI
# ================================================================
def main():
    parser = argparse.ArgumentParser(
        description="🛒 Stok Takip Sistemi - Ürün stoğa girdiğinde bildirim al"
    )
    parser.add_argument(
        "--tek-seferlik",
        action="store_true",
        help="Sadece bir kez kontrol et ve çık",
    )
    args = parser.parse_args()

    logger = log_ayarla()
    motor = StokTakipMotoru()

    # Ctrl+C ile düzgün kapanma
    signal.signal(signal.SIGINT, motor.durdur)
    signal.signal(signal.SIGTERM, motor.durdur)

    try:
        motor.baslat(tek_seferlik=args.tek_seferlik)
    except Exception as e:
        logger.critical(f"💥 Beklenmeyen hata: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()


