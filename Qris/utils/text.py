class TEXT:

    @staticmethod
    def start_msg(username, bot_name):
        return f"""
<b>Hai {username}!, Selamat datang di {bot_name} 👋</b>

<blockquote><b>
🤖 Bot ini dirancang untuk membantumu membuat QRIS Dinamis secara praktis dan otomatis.

Ketik /qris [nominal] atau tekan tombol di bawah untuk mulai membuat QRIS. 🚀
</b></blockquote>
"""