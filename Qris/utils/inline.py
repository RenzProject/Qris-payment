from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

class BUTTON:

    @staticmethod
    def start():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("⚡ Buat QRIS Dinamis", callback_data="gen_qris")
                ],
                [
                    InlineKeyboardButton("📜 Riwayat Transaksi", callback_data="history"),
                    InlineKeyboardButton("💰 Total Pendapatan", callback_data="total_pendapatan")
                ],
            ]
        )

    @staticmethod
    def back_to_start():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("Kembali", callback_data="back_start")
                ]
            ]
        )