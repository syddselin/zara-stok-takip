"""
Stok Kontrol Modülü (API Tabanlı)
===================================
Zara ve Massimo Dutti ürünlerinin beden bazlı stok kontrolünü yapar.
Selenium veya Chrome gerektirmez — sadece HTTP istekleri kullanır.

Desteklenen markalar:
  - Zara      → https://www.zara.com/tr/tr/products-details?productIds={id}&ajax=true
  - Massimo Dutti → https://www.massimodutti.com/itxrest/2/catalog/store/{storeId}/product/{productId}/detail

Kullanım:
  kontrol = StokKontrol()
  durum = kontrol.kontrol_et(url, "S")
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
# ZARA STOK KONTROL
# ================================================================


class ZaraStokKontrol:
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
        self.session.close()
        logger.info("🌐 HTTP oturumu kapatıldı")

    def _cookie_al(self):
        if self._cookie_alindi:
            return
        try:
            self.session.get("https://www.zara.com/tr/tr/", timeout=15)
            self._cookie_alindi = True
            logger.debug("🍪 Cookie'ler alındı")
        except Exception as e:
            logger.debug(f"Cookie alma hatası (devam ediliyor): {e}")

    def _product_id_cek(self, url: str) -> str:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "v1" in params:
            return params["v1"][0]
        match = re.search(r"-p(\d+)\.html", url)
        if match:
            return match.group(1)
        raise ValueError(f"URL'den ürün ID'si çıkarılamadı: {url}")

    def _api_kontrol(self, url: str, hedef_beden: str) -> StokDurumu:
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

    def _veriyi_isle(self, product: dict, product_id: str, hedef_beden: str) -> StokDurumu:
        tum_bedenler = {}
        hedef_stokta = False
        hedef_bulundu = False
        fiyat = None

        detail = product.get("detail", {})
        colors = detail.get("colors", [])
        if not colors:
            return StokDurumu(stokta_var=False, beden=hedef_beden, mesaj="Ürün renk/varyant bilgisi bulunamadı")

        # hedef renkteki bedenleri tara
        hedef_renk = None
        for color in colors:
            if str(color.get("productId")) == str(product_id):
                hedef_renk = color
                break
        if not hedef_renk and colors:
            hedef_renk = colors[0]

        sizes = hedef_renk.get("sizes", [])
        logger.info(f"  📏 {len(sizes)} beden bulundu")

        for size in sizes:
            beden = (size.get("name") or "").strip().upper()
            stokta = size.get("availability") == "in_stock"
            if beden:
                tum_bedenler[beden] = stokta
            if not fiyat and size.get("price"):
                try:
                    fiyat = f"{float(size['price'])/100:,.2f} TRY".replace(",", ".")
                except Exception:
                    fiyat = str(size.get("price"))
            if beden == hedef_beden:
                hedef_bulundu = True
                hedef_stokta = stokta

        if not hedef_bulundu:
            mevcut = ", ".join(tum_bedenler.keys()) or "Beden bilgisi alınamadı"
            return StokDurumu(stokta_var=False, beden=hedef_beden, fiyat=fiyat, tum_bedenler=tum_bedenler, mesaj=f"'{hedef_beden}' bedeni bu üründe bulunamadı. Mevcut: {mevcut}")

        stokta_bedenler = [b for b, s in tum_bedenler.items() if s]
        diger_bilgi = (f"Stokta olan diğer bedenler: {', '.join(stokta_bedenler)}" if stokta_bedenler else "Hiçbir beden stokta değil")
        mesaj = f"{hedef_beden} bedeni STOKTA! {diger_bilgi}" if hedef_stokta else f"{hedef_beden} bedeni stok dışı. {diger_bilgi}"

        return StokDurumu(stokta_var=hedef_stokta, beden=hedef_beden, fiyat=fiyat, tum_bedenler=tum_bedenler, mesaj=mesaj)

    def kontrol_et(self, url: str, hedef_beden: str) -> StokDurumu:
        hedef_beden = hedef_beden.strip().upper()
        for deneme in range(TEKRAR_DENEME):
            try:
                return self._api_kontrol(url, hedef_beden)
            except Exception as e:
                logger.warning(f"Kontrol hatası (deneme {deneme + 1}/{TEKRAR_DENEME}): {e}")
                self._cookie_alindi = False
                if deneme < TEKRAR_DENEME - 1:
                    time.sleep(3)
        return StokDurumu(stokta_var=False, beden=hedef_beden, mesaj="Tüm denemeler başarısız oldu")


# ================================================================
# MASSIMO DUTTI STOK KONTROL
# (unchanged)
# ================================================================


class MassimoDuttiStokKontrol:
    STORE_ID = "34009471"
    CATALOG_ID = "30359503"

    PRODUCT_TEMPLATE = (
        "https://www.massimodutti.com/itxrest/2/catalog/store/{store_id}/"
        "{catalog_id}/product/{part_number}"
    )
    STOCK_TEMPLATE = (
        "https://www.massimodutti.com/itxrest/2/catalog/store/{store_id}/"
        "{catalog_id}/product/{product_id}/stock"
    )

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.massimodutti.com/tr/",
        "Origin": "https://www.massimodutti.com",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def kapat(self):
        self.session.close()

    def kontrol_et(self, url: str, hedef_beden: str) -> StokDurumu:
        hedef_beden = hedef_beden.strip().upper()
        for deneme in range(TEKRAR_DENEME):
            try:
                return self._api_kontrol(url, hedef_beden)
            except Exception as e:
                logger.warning(f"Massimo Dutti kontrol hatası (deneme {deneme + 1}/{TEKRAR_DENEME}): {e}")
                if deneme < TEKRAR_DENEME - 1:
                    time.sleep(3)
        return StokDurumu(stokta_var=False, beden=hedef_beden, mesaj="Tüm denemeler başarısız oldu")

    def _product_id_cek(self, url: str) -> str:
        parsed = urlparse(url)
        match = re.search(r"-l(\d+)", parsed.path)
        if match:
            return match.group(1)
        params = parse_qs(parsed.query)
        if "v1" in params:
            return params["v1"][0]
        raise ValueError(f"Massimo Dutti URL'den ürün ID'si çıkarılamadı: {url}")

    def _api_kontrol(self, url: str, hedef_beden: str) -> StokDurumu:
        part_number = self._product_id_cek(url)
        product_url = self.PRODUCT_TEMPLATE.format(store_id=self.STORE_ID, catalog_id=self.CATALOG_ID, part_number=part_number)
        product_resp = self.session.get(product_url, timeout=15)
        product_resp.raise_for_status()
        product_data = product_resp.json()
        product_id = product_data.get("id")
        stock_data = None
        if product_id:
            stock_url = self.STOCK_TEMPLATE.format(store_id=self.STORE_ID, catalog_id=self.CATALOG_ID, product_id=product_id)
            stock_resp = self.session.get(stock_url, timeout=15)
            stock_resp.raise_for_status()
            stock_data = stock_resp.json()
        return self._veriyi_isle(product_data, stock_data, hedef_beden)

    def _veriyi_isle(self, product_data: dict, stock_data: Optional[dict], hedef_beden: str) -> StokDurumu:
        tum_bedenler = {}
        fiyat = None
        hedef_bulundu = False
        hedef_stokta = False
        sku_to_stok = {}
        if stock_data:
            for entry in stock_data.get("stocks", []):
                for stock_item in entry.get("stocks", []):
                    sku = stock_item.get("id")
                    availability = stock_item.get("availability", "")
                    if sku is not None:
                        sku_to_stok[str(sku)] = availability in ("in_stock", "available", "low_on_stock")
        detail = product_data.get("detail", {})
        colors = detail.get("colors", [])
        if not colors:
            return StokDurumu(stokta_var=False, beden=hedef_beden, mesaj="Renk/beden bilgisi alınamadı — API yapısı beklenmedik")
        sizes = colors[0].get("sizes", [])
        logger.info(f"  📏 {len(sizes)} beden bulundu")
        for size in sizes:
            beden = (size.get("name") or "").strip().upper()
            sku = size.get("sku")
            sku_anahtar = str(sku) if sku is not None else ""
            if sku_anahtar in sku_to_stok:
                stokta = sku_to_stok[sku_anahtar]
            else:
                visibility = (size.get("visibilityValue") or "").upper()
                stokta = visibility in ("SHOW", "VISIBLE")
            if beden:
                tum_bedenler[beden] = stokta
            if not fiyat:
                raw_price = size.get("price")
                if raw_price:
                    try:
                        fiyat_sayi = float(raw_price)
                        fiyat = f"{fiyat_sayi / 100:,.2f} TRY".replace(",", ".")
                    except (TypeError, ValueError):
                        fiyat = str(raw_price)
            if beden == hedef_beden:
                hedef_bulundu = True
                hedef_stokta = stokta
        if not hedef_bulundu:
            mevcut = ", ".join(tum_bedenler.keys()) or "Beden bilgisi alınamadı"
            return StokDurumu(stokta_var=False, beden=hedef_beden, fiyat=fiyat, tum_bedenler=tum_bedenler, mesaj=f"'{hedef_beden}' bedeni bulunamadı. Mevcut: {mevcut}")
        stokta_bedenler = [b for b, s in tum_bedenler.items() if s]
        diger_bilgi = (f"Stokta olan diğer bedenler: {', '.join(stokta_bedenler)}" if stokta_bedenler else "Hiçbir beden stokta değil")
        mesaj = f"{hedef_beden} bedeni STOKTA! {diger_bilgi}" if hedef_stokta else f"{hedef_beden} bedeni stok dışı. {diger_bilgi}"
        return StokDurumu(stokta_var=hedef_stokta, beden=hedef_beden, fiyat=fiyat, tum_bedenler=tum_bedenler, mesaj=mesaj)


# ================================================================
# MARKA BAĞIMSIZ SARMALAYICI
# ================================================================


class StokKontrol:
    """URL'deki domain'e göre doğru stok kontrol sınıfına yönlendirir."""

    def __init__(self):
        self._zara = ZaraStokKontrol()
        self._massimo = MassimoDuttiStokKontrol()

    def kontrol_et(self, url: str, hedef_beden: str) -> StokDurumu:
        if "massimodutti.com" in url:
            return self._massimo.kontrol_et(url, hedef_beden)
        return self._zara.kontrol_et(url, hedef_beden)

    def kapat(self):
        self._zara.kapat()
        self._massimo.kapat()
        logger.info("🌐 HTTP oturumları kapatıldı")
