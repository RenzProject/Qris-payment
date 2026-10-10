from .db_client import dB

# AKSES MANAGEMENT
async def add_akses(user_id):
    return await dB.add_akses(user_id)

async def get_akses(user_id):
    return await dB.get_akses(user_id)

async def all_akses():
    return await dB.all_akses()

async def remove_akses(user_id):
    return await dB.remove_akses(user_id)

async def check_akses(user_id: int) -> bool:
    akses = await get_akses(user_id)
    return akses is not None

# BROADCAST MANAGEMENT
async def add_broadcast_user(user_id):
    return await dB.add_broadcast(user_id)

async def get_broadcast_user(user_id):
    return await dB.get_broadcast(user_id)

async def all_broadcast_users():
    return await dB.all_broadcast()

async def remove_broadcast_user(user_id):
    return await dB.remove_broadcast_user(user_id)

# TRANSAKSI MANAGEMENT
async def add_transaksi(transaction_id, user_id, amount):
    return await dB.add_transaksi(transaction_id, user_id, amount)

async def get_transaksi(transaction_id):
    return await dB.get_transaksi(transaction_id)

async def get_transaksi_user_id(user_id):
    return await dB.get_transaksi_user_id(user_id)

async def all_transaksi():
    return await dB.all_transaksi()

async def update_status_transaksi(transaction_id, status):
    return await dB.update_status_transaksi(transaction_id, status)

async def remove_transaksi(transaction_id):
    return await dB.remove_transaksi(transaction_id)

async def remove_transaksi_user_id(user_id):
    return await dB.remove_transaksi_user_id(user_id)

# SALDO USER MANAGEMENT
async def add_saldo_user(user_id, amount=0):
    return await dB.add_saldo_user(user_id, amount)

async def get_saldo_user(user_id):
    return await dB.get_saldo_user(user_id)

async def get_all_saldo_user():
    return await dB.get_all_saldo_user()

async def reset_saldo_user(user_id):
    return await dB.reset_saldo_user(user_id)

async def set_fee_user(user_id, fee):
    return await dB.set_fee_user(user_id, fee)

async def get_fee_user(user_id):
    return await dB.get_fee_user(user_id)