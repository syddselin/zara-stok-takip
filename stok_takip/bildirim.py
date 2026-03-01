"""
Bildirim Modülü
===============
Stok değişikliği algılandığında kullanıcıya bildirim gönderir.
Desteklenen bildirim kanalları:
  - Masaüstü bildirimi (macOS / Windows / Linux)
  - Sesli uyarı
  - E-posta (SMTP)
  - Telegram Bot
"""

import logging
import platform
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

import requests

from config import (
    MASAUSTU_BILDIRIM,
    SESLI_BILDIRIM,
    EPOSTA_BILDIRIM,
    EPOSTA_AYARLARI,
    TELEGRAM_BILDIRIM,
    TELEGRAM_AYARLARI,
)

logger = logging.getLogger("stok_takip")


class BildirimGonderici:
    """Birden fazla kanal üzerinden bildirim gönderir."""

    def bildirim_gonder(self, urun_ismi: str, url: str, fiyat: str = None):
        """
        Tüm aktif kanallar üzerinden bildirim gönderir.

        Args:
            urun_ismi: Stok durumu değişen ürünün adı
            url: Ürünün sayfasının URL'si
            fiyat: Ürünün fiyatı (varsa)
        """
        zaman = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        fiyat_bilgisi = f" | Fiyat: {fiyat}" if fiyat else ""

        baslik = f"🎉 STOK BİLDİRİMİ: {urun_ismi}"
        mesaj = (
            f"Ürün stoğa girdi!\n\n"
            f"📦 Ürün: {urun_ismi}\n"
            f"💰 {fiyat_bilgisi}\n"
            f"🔗 Link: {url}\n"
            f"⏰ Zaman: {zaman}"
        )

        logger.info(f"🎉 {urun_ismi} STOĞA GİRDİ! {fiyat_bilgisi}")

        if MASAUSTU_BILDIRIM:
            self._masaustu_bildirim(baslik, mesaj, url)

        if SESLI_BILDIRIM:
            self._sesli_bildirim()

        if EPOSTA_BILDIRIM:
            self._eposta_gonder(baslik, mesaj, url)

        if TELEGRAM_BILDIRIM:
            self._telegram_gonder(baslik, mesaj, url)

    # ================================================================
    # BİLDİRİM KANALLARI
    # ================================================================

    def _masaustu_bildirim(self, baslik: str, mesaj: str, url: str = ""):
        """İşletim sistemine uygun masaüstü bildirimi gönderir."""
        try:
            sistem = platform.system()

            if sistem == "Darwin":  # macOS
                # macOS popup dialog - izin gerektirmez, her zaman gorunur
                script = (
                    'tell application "System Events"\n'
                    f'  set sonuc to display dialog "{baslik}" & return & return & "{mesaj[:200]}" '
                    f'with title "Stok Takip" buttons {{"Urune Git", "Tamam"}} default button "Urune Git"\n'
                    'end tell\n'
                    'if button returned of sonuc is "Urune Git" then\n'
                    f'  do shell script "open {url}"\n'
                    'end if'
                )
                subprocess.Popen(["osascript", "-e", script])
                logger.info("✅ Masaüstü bildirimi gönderildi (macOS)")

            elif sistem == "Linux":
                # Linux için notify-send
                subprocess.run(
                    ["notify-send", baslik, mesaj[:200], "-u", "critical"],
                    check=True,
                )
                logger.info("✅ Masaüstü bildirimi gönderildi (Linux)")

            elif sistem == "Windows":
                # Windows için PowerShell toast bildirimi
                ps_script = f"""
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
                $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
                $textNodes = $template.GetElementsByTagName("text")
                $textNodes.Item(0).AppendChild($template.CreateTextNode("{baslik}")) > $null
                $textNodes.Item(1).AppendChild($template.CreateTextNode("{mesaj[:150]}")) > $null
                $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("StokTakip").Show($toast)
                """
                subprocess.run(
                    ["powershell", "-Command", ps_script],
                    check=True,
                    capture_output=True,
                )
                logger.info("✅ Masaüstü bildirimi gönderildi (Windows)")

        except Exception as e:
            logger.error(f"❌ Masaüstü bildirimi gönderilemedi: {e}")

    def _sesli_bildirim(self):
        """Sesli uyarı çalar."""
        try:
            sistem = platform.system()

            if sistem == "Darwin":
                # macOS ses çalma
                subprocess.run(
                    ["afplay", "/System/Library/Sounds/Glass.aiff"],
                    check=True,
                )
            elif sistem == "Linux":
                subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"], check=True)
            elif sistem == "Windows":
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

            logger.info("✅ Sesli bildirim çalındı")

        except Exception as e:
            logger.error(f"❌ Sesli bildirim çalınamadı: {e}")

    def _eposta_gonder(self, baslik: str, mesaj: str, url: str):
        """E-posta bildirimi gönderir."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = baslik
            msg["From"] = EPOSTA_AYARLARI["gonderen_eposta"]
            msg["To"] = EPOSTA_AYARLARI["alici_eposta"]

            # HTML formatında e-posta
            html_icerik = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="background: #4CAF50; color: white; padding: 15px; border-radius: 8px;">
                    <h2 style="margin: 0;">🎉 Stok Bildirimi</h2>
                </div>
                <div style="padding: 20px; border: 1px solid #ddd; border-radius: 0 0 8px 8px;">
                    <p style="white-space: pre-line; font-size: 16px;">{mesaj}</p>
                    <a href="{url}" style="display: inline-block; padding: 12px 24px;
                       background: #4CAF50; color: white; text-decoration: none;
                       border-radius: 5px; font-size: 16px; margin-top: 10px;">
                       🛒 Ürüne Git
                    </a>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(mesaj, "plain", "utf-8"))
            msg.attach(MIMEText(html_icerik, "html", "utf-8"))

            with smtplib.SMTP(
                EPOSTA_AYARLARI["smtp_sunucu"], EPOSTA_AYARLARI["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    EPOSTA_AYARLARI["gonderen_eposta"],
                    EPOSTA_AYARLARI["gonderen_sifre"],
                )
                server.send_message(msg)

            logger.info(
                f"✅ E-posta gönderildi: {EPOSTA_AYARLARI['alici_eposta']}"
            )

        except Exception as e:
            logger.error(f"❌ E-posta gönderilemedi: {e}")

    def _telegram_gonder(self, baslik: str, mesaj: str, url: str):
        """Telegram bot aracılığıyla bildirim gönderir."""
        try:
            telegram_mesaj = (
                f"*{baslik}*\n\n"
                f"{mesaj}\n\n"
                f"[🛒 Ürüne Git]({url})"
            )

            api_url = (
                f"https://api.telegram.org/bot{TELEGRAM_AYARLARI['bot_token']}"
                f"/sendMessage"
            )

            payload = {
                "chat_id": TELEGRAM_AYARLARI["chat_id"],
                "text": telegram_mesaj,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            }

            response = requests.post(api_url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info("✅ Telegram bildirimi gönderildi")

        except Exception as e:
            logger.error(f"❌ Telegram bildirimi gönderilemedi: {e}")
