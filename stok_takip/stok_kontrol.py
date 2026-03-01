"""
Zara Stok Kontrol Modülü (Selenium Tabanlı)
============================================
Zara ürün sayfalarını gerçek tarayıcı ile açarak
belirli bir bedenin stok durumunu kontrol eder.

Zara güçlü bot koruması (Akamai) kullandığı için
normal HTTP istekleri engellenir. Bu modül Selenium
ile gerçek Chrome tarayıcısı kullanarak bu korumayı aşar.
"""

import time
import logging
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import HEADLESS, SAYFA_BEKLEME, TEKRAR_DENEME

logger = logging.getLogger("stok_takip")


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


class ZaraStokKontrol:
    """
    Selenium ile Zara ürün sayfasını açıp beden bazlı stok kontrolü yapar.

    Zara'nın beden seçici yapısı:
      - li.size-selector-sizes__size → her beden bir <li>
      - .size-selector-sizes-size__label → beden adı (XS, S, M, ...)
      - button[data-qa-action="size-in-stock"] → stokta
      - button[data-qa-action="size-out-of-stock"] → stok dışı
      - CSS class: --disabled → stok dışı bedenlere eklenir
    """

    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None

    def _tarayici_baslat(self):
        """Chrome tarayıcısını bot korumasını aşacak şekilde başlatır."""
        if self.driver:
            return

        opts = Options()

        if HEADLESS:
            opts.add_argument("--headless=new")

        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(options=opts)

        # navigator.webdriver özelliğini gizle
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )

        logger.info("🌐 Chrome tarayıcı başlatıldı")

    def kapat(self):
        """Tarayıcıyı kapatır."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
            logger.info("🌐 Tarayıcı kapatıldı")

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
                return self._sayfa_kontrol(url, hedef_beden)
            except Exception as e:
                logger.warning(
                    f"Kontrol hatası (deneme {deneme + 1}/{TEKRAR_DENEME}): {e}"
                )
                # Tarayıcıyı yeniden başlat
                self.kapat()
                if deneme < TEKRAR_DENEME - 1:
                    time.sleep(3)

        return StokDurumu(
            stokta_var=False,
            beden=hedef_beden,
            mesaj="Tüm denemeler başarısız oldu",
        )

    def _sayfa_kontrol(self, url: str, hedef_beden: str) -> StokDurumu:
        """Sayfayı açıp beden bazlı stok kontrolü yapar."""
        self._tarayici_baslat()

        logger.debug(f"Sayfa açılıyor: {url}")
        self.driver.get(url)

        # Sayfanın yüklenmesini bekle (bot korumasını geçmek için)
        time.sleep(SAYFA_BEKLEME)

        # Cookie banner'ını kapat (varsa)
        self._cookie_kapat()

        # "EKLE" butonuna tıklayarak beden seçiciyi aç
        # Zara'da bedenler ancak bu butona tıklandığında görünür olur
        try:
            ekle_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[data-qa-action='add-to-cart']")
                )
            )
            self.driver.execute_script("arguments[0].click();", ekle_btn)
            time.sleep(2)
        except Exception:
            return StokDurumu(
                stokta_var=False,
                beden=hedef_beden,
                mesaj="EKLE butonu bulunamadı (sayfa yüklenemedi veya ürün kaldırıldı)",
            )

        # Beden listesinin yüklenmesini bekle
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "li[class*='size']")
                )
            )
        except Exception:
            return StokDurumu(
                stokta_var=False,
                beden=hedef_beden,
                mesaj="Beden listesi yüklenemedi (sayfa açılamadı veya ürün kaldırıldı)",
            )

        # Fiyat bilgisini al
        fiyat = self._fiyat_al()

        # Tüm bedenlerin stok durumunu tara
        tum_bedenler = {}
        hedef_stokta = False
        hedef_bulundu = False

        beden_elemanlari = self.driver.find_elements(
            By.CSS_SELECTOR, "li[class*='size']"
        )

        logger.info(f"  📏 {len(beden_elemanlari)} beden bulundu")

        for li in beden_elemanlari:
            try:
                # Beden adını al
                try:
                    label = li.find_element(
                        By.CSS_SELECTOR, "[class*='label']"
                    )
                except Exception:
                    label = li
                beden_adi = (
                    label.text.strip()
                    or label.get_attribute("textContent").strip()
                )

                if not beden_adi:
                    continue

                # Stok durumunu belirle
                btn = li.find_element(By.CSS_SELECTOR, "button")
                qa_action = btn.get_attribute("data-qa-action") or ""
                siniflar = li.get_attribute("class") or ""

                stokta = (
                    qa_action == "size-in-stock"
                    and "--disabled" not in siniflar
                    and "--unavailable" not in siniflar
                )

                tum_bedenler[beden_adi] = stokta

                # Hedef beden kontrolü
                if beden_adi.upper() == hedef_beden:
                    hedef_bulundu = True
                    hedef_stokta = stokta

            except Exception as e:
                logger.debug(f"Beden elementi okunamadı: {e}")
                continue

        # Sonuç oluştur
        if not hedef_bulundu:
            return StokDurumu(
                stokta_var=False,
                beden=hedef_beden,
                fiyat=fiyat,
                tum_bedenler=tum_bedenler,
                mesaj=f"'{hedef_beden}' bedeni bu üründe bulunamadı. "
                      f"Mevcut bedenler: {', '.join(tum_bedenler.keys())}",
            )

        # Diğer bedenlerin durumunu özetle
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

    def _cookie_kapat(self):
        """Zara cookie banner'ını kapatır."""
        try:
            btn = self.driver.find_element(
                By.CSS_SELECTOR, "#onetrust-accept-btn-handler"
            )
            if btn.is_displayed():
                btn.click()
                time.sleep(0.5)
        except Exception:
            pass

    def _fiyat_al(self) -> Optional[str]:
        """Sayfadan fiyat bilgisini alır."""
        selectors = [
            ".money-amount__main",
            "[class*='price'] [class*='current']",
            ".product-detail-info__price .money-amount",
        ]
        for sel in selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, sel)
                fiyat = el.text.strip()
                if fiyat:
                    return fiyat
            except Exception:
                continue
        return None
