from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

keyboard = InlineKeyboardMarkup(row_width=2)

key_admin = InlineKeyboardButton('👮‍♂️ Админы', callback_data='admin')
key_account = InlineKeyboardButton('👨‍🔧 Аккаунты', callback_data='account')
key_coworking = InlineKeyboardButton('📍 Коворкинг', callback_data='coworking')
key_search = InlineKeyboardButton('📍 Люди рядом', callback_data='search')
key_reply = InlineKeyboardButton('🗣 Ответы', callback_data='reply')
keyboard.add(key_admin, key_account, key_coworking, key_search, key_reply)
