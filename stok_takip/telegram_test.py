#!/usr/bin/env python3
"""Telegram ayarlarını test etmek için yardımcı script."""

from bildirim import BildirimGonderici
from config import TELEGRAM_BILDIRIM, TELEGRAM_AYARLARI


def main():
    token = TELEGRAM_AYARLARI.get("bot_token", "")
    chat_id = TELEGRAM_AYARLARI.get("chat_id", "")

    if (
        not TELEGRAM_BILDIRIM
        or not token
        or token == "BOT_TOKEN_BURAYA"
        or not chat_id
        or chat_id == "CHAT_ID_BURAYA"
    ):
        print("❌ Telegram ayarları eksik.")
        print("   TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID değerlerini .env dosyasına girin.")
        return

    gonderici = BildirimGonderici()
    gonderici._telegram_gonder(
        "✅ Telegram Test",
        "Stok takip Telegram entegrasyonu aktif.",
        "https://www.massimodutti.com/tr/dugmeli-ve-bagc%C4%B1kl%C4%B1-100-keten-kimono-l06708939",
    )
    print("✅ Test mesajı gönderildi (logları da kontrol edin).")


if __name__ == "__main__":
    main()
