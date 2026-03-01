"""
Zara Stok Kontrol Modülü (API Tabanlı)
=======================================
Zara'nın dahili ürün API'sini kullanarak beden bazlı stok kontrolü yapar.

Selenium veya Chrome gerektirmez — sadece HTTP istekleri kullanır.
Bu sayede GitHub Actions'da çok daha hızlı çalışır (~2 sn vs ~30 sn).

API endpoint:
  https://www.zara.com/tr/tr/products-details?productIds={id}&ajax=true

Ürün URL'sindeki "v1" parametresi doğrudan API'nin beklediği ID'dir.
  Örnek: ...p07521020.html?v1=505034866  →  productId = 505034866
"""

import re
import time
import logging
from typing import Optional
from urllib.parse import urlparse, parse_qs

import requests

from config import TEKRAR_DENEME

logger = logging.getLogger("stok_takip")


# ================================================================
# VERİ MODELİ
# ================================================================

class StokDurumu:
    """Bir ürünün stok durumunu temsil eder."""

    def __init__(
        self,
        stokta_var: bool,
        beden: str = "",
        fiyat: Optional[str] = None,
        tum_bedenler: Optional[dict] = None,
        mesaj: str = "",
    ):
        self.stokta_var = stokta_var
        self.beden = beden
        self.fiyat = fiyat
        self.tum_bedenler = tum_bedenler or {}
        self.mesaj = mesaj

    def __repr__(self):
        durum = "STOKTA ✅" if self.stokta_var else "STOK DIŞI ❌"
        return f"[{self.beden}] {durum} | Fiyat: {self.fiyat} | {self.mesaj}"


# ================================================================
# STOK KONTROL SINIFI
# ================================================================

class ZaraStokKontrol:
    """
    Zara'nın dahili API'si ile beden bazlı stok kontrolü yapar.
    Chrome/Selenium gerektirmez.
    """

    API_URL = "https://www.zara.com/tr/tr/products-details"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.zara.com/tr/tr/",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self._cookie_alindi = False

    def kapat(self):
        """HTTP oturumunu kapatır."""
        self.session.close()
        logger.info("🌐 HTTP oturumu kapatıldı")

    def kontrol_et(self, url: str, hedef_beden: str) -> StokDurumu:
        """
        Zara ürün sayfasındaki belirtilen bedenin stok durumunu kontrol eder.

        Args:
            url: Zara ürün sayfasının URL'si
            hedef_beden: Kontrol edilecek beden (ör: "XS", "S", "M", "L")

        Returns:
            StokDurumu nesnesi
        """
        hedef_beden = hedef_beden.strip().upper()

        for deneme in range(TEKRAR_DENEME):
            try:
                return self._api_kontrol(url, hedef_beden)
            except Exception as e:
                logger.warning(
                    f"Kontrol hatası (deneme {deneme + 1}/{TEKRAR_DENEME}): {e}"
                )
                # Cookie'ler geçersiz olmuş olabilir, yeniden al
                self._cookie_alindi = False
                if deneme < TEKRAR_DENEME - 1:
                    time.sleep(3)

        return StokDurumu(
            stokta_var=False,
            beden=hedef_beden,
            mesaj="Tüm denemeler başarısız oldu",
        )

    # ================================================================
    # API İSTEĞİ
    # ================================================================

    def _cookie_al(self):
        """Zara ana sayfasını ziyaret ederek gerekli cookie'leri alır."""
        if self._cookie_alindi:
            return

        try:
            self.session.get("https://www.zara.com/tr/tr/", timeout=15)
            self._cookie_alindi = True
            logger.debug("🍪 Cookie'ler alındı")
        except Exception as e:
            logger.debug(f"Cookie alma hatası (devam ediliyor): {e}")

    def _product_id_cek(self, url: str) -> str:
        """
        URL'den Zara ürün API ID'sini çıkarır.
        Ürün URL'sindeki v1 parametresi doğrudan API ID'sidir.

        Örnek: ...p07521020.html?v1=505034866  →  505034866
        """
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        # v1 parametresi = renk bazlı ürün ID
        if "v1" in params:
            return params["v1"][0]

        # v1 yoksa, URL'den ana ürün ID'sini çıkar (daha az güvenilir)
        match = re.search(r"-p(\d+)\.html", url)
        if match:
            return match.group(1)

        raise ValueError(f"URL'den ürün ID'si çıkarılamadı: {url}")

    def _api_kontrol(self, url: str, hedef_beden: str) -> StokDurumu:
        """Zara API'sinden ürün verisini çekip stok durumunu döndürür."""
        self._cookie_al()

        product_id = self._product_id_cek(url)
        logger.debug(f"API sorgusu: productId={product_id}")

        resp = self.session.get(
            self.API_URL,
            params={"productIds": product_id, "ajax": "true"},
            timeout=15,
        )
        resp.raise_for_status()

        data = resp.json()

        if not data:
            raise ValueError(f"API boş yanıt döndü (productId: {product_id})")

        product = data[0]
        return self._veriyi_isle(product, product_id, hedef_beden)

    # ================================================================
    # VERİ İŞLEME
    # ================================================================

    def _veriyi_isle(
        self, product: dict, product_id: str, hedef_beden: str
    ) -> StokDurumu:
        """API yanıtından beden bazlı stok durumunu çıkarır."""
        tum_bedenler = {}
        hedef_stokta = False
        hedef_bulundu = False
        fiyat = None

        detail = product.get("detail", {})
        colors = detail.get("colors", [])

        # Doğru rengi bul (product_id ile eşleşen)
        hedef_renk = None
        for color in colors:
            if str(color.get("productId")) == str(product_id):
                hedef_renk = color
                break

        # Eşleşen renk bulunamazsa ilk rengi al
        if not hedef_renk and colors:
            hedef_renk = colors[0]

        if not hedef_renk:
            return StokDurumu(
                stokta_var=False,
                beden=hedef_beden,
                mesaj="Ürün renk/varyant bilgisi bulunamadı",
            )

        # Bedenleri tara
        sizes = hedef_renk.get("sizes", [])
        logger.info(f"  📏 {len(sizes)} beden bulundu")

        for size in sizes:
            beden = (size.get("name") or "").strip().upper()
            stokta = size.get("availability") == "in_stock"

            if beden:
                tum_bedenler[beden] = stokta

            # Fiyat (kuruş cinsinden gelir: 149000 → 1.490,00 TRY)
            if not fiyat and size.get("price"):
                fiyat_kurus = size["price"]
                fiyat = f"{fiyat_kurus / 100:,.2f} TRY".replace(",", ".")

            if beden == hedef_beden:
                hedef_bulundu = True
                hedef_stokta = stokta

        # Sonuç oluştur
        if not hedef_bulundu:
            mevcut = ", ".join(tum_bedenler.keys()) or "Beden bilgisi alınamadı"
            return StokDurumu(
                stokta_var=False,
                beden=hedef_beden,
                fiyat=fiyat,
                tum_bedenler=tum_bedenler,
                mesaj=f"'{hedef_beden}' bedeni bu üründe bulunamadı. Mevcut: {mevcut}",
            )

        stokta_bedenler = [b for b, s in tum_bedenler.items() if s]
        diger_bilgi = (
            f"Stokta olan diğer bedenler: {', '.join(stokta_bedenler)}"
            if stokta_bedenler
            else "Hiçbir beden stokta değil"
        )

        if hedef_stokta:
            mesaj = f"{hedef_beden} bedeni STOKTA! {diger_bilgi}"
        else:
            mesaj = f"{hedef_beden} bedeni stok dışı. {diger_bilgi}"

        return StokDurumu(
            stokta_var=hedef_stokta,
            beden=hedef_beden,
            fiyat=fiyat,
            tum_bedenler=tum_bedenler,
            mesaj=mesaj,
        )
