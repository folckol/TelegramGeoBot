import sqlite3
import traceback
import uuid

from telethon.errors import PhoneNumberBannedError, AuthKeyDuplicatedError

from Abuse.TelegramGeoBot.converter import SessionToTData
from core.database import create_table, insert_location, insert_admin,  where_select_random_word, insert_word, delete_word,insert_received,select_random_word, delete_location, delete_admin, select_admin, select_received, select_location, select_location_where
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.distance import haversine_distance, get_name_position
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncio, os, random, subprocess, sys, zipfile, shutil
from aiogram import Bot, types, Dispatcher, executor
from telethon.tl.types import InputPeerUser
from telethon.tl.types import InputGeoPoint
from opentele.api import UseCurrentSession
from opentele.tl import TelegramClient as TC
from aiogram.dispatcher import FSMContext
from env.config.setting import settings
from core.keyboard import keyboard
from telethon.tl import functions
from opentele.td import TDesktop
from telethon import events
from tgbot import TgBot

conn = sqlite3.connect('Proxies.db', check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS Proxies (

        id STRING,

        accountName STRING,
        proxyData STRING

   );
    """)
conn.commit()
conn.close()


admin = [300105226, 649811235]
get_json = {}
get_client = {}
account_state = 0
config = settings.bots
DOWNLOAD_FOLDER = "account"


class UserState(StatesGroup):
    args = State()
    admin = State()
    people_near_id = State()
    coworking_id_msg = State()
    reply_id = State()
    user_id = State()

bot = Bot(token=config.bot_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
bot_two = TgBot(config.bot_token)

#Создает таблицы в бд
create_table()

# Ожидает новые сообщения от людишек и отправляет админу
async def message_listener(client):
    @client.on(events.NewMessage)
    async def handle_new_message(event):

        user = await client.get_me()
        people_id = event.message.from_id.user_id
        msg_text = event.message.text
        bot_id = user.id
        users = await event.get_sender()
        first_name = users.first_name
        keyboard = [[{'text': 'Ответить', 'callback_data': f'answer_{people_id}_{bot_id}'}]]
        reply_markup = {'inline_keyboard': keyboard}
        for admin_id in select_admin():
            bot_two.send_message_inline(admin_id, f'Новое сообщение от <a href="tg://user?id={people_id}">{first_name}</a> для <a href="tg://user?id={bot_id}">{user.first_name}</a> :\n\n{msg_text}', reply_markup=reply_markup, parse_mode='html')

# Главная функция где все взаимодействия с аккаунтами
async def main(array, send=None, user_id=None, data=None, spam=False):
    global account_state

    # for account in array:
    #     if "." in account and account.split(".")[1] == "session":
    #         await SessionToTData()
    #         break
    # array = os.listdir('./account/')

    # Получаем весь список аккаунтов
    for account in array:
        # Если аккаунт всего один а не несколько тогда сделаем переменную что всего один
        if type(array).__name__ != 'list':
            account = array


        # Если код запущен впервые тогда подключается к аккаунту
        if account_state == 0:
            try:
                # Подключаем аккаунт
                tdataFolders = f"./account/{account}"
                tdesk = TDesktop(tdataFolders)

                assert tdesk.isLoaded()

                # print(11)
                try:
                    # print(12)
                    client = await tdesk.ToTelethon(session=f"./session/{account}.session", flag=UseCurrentSession)
                except Exception as e:
                    print(f'Ошибка с входом в аккаунт {account} - ', e)
                    # input()

                await client.start()
                user = await client.get_me()

                # Добавляем данные о аккаунте в словарь, что бы работать с ним
                get_json[user.id] = account
                get_client[account] = client
                print(f'Успешно зашел в аккаунт - {account}')
            except:

                # traceback.print_exc()

                # Удаляем аккаунт если не зашли
                shutil.rmtree(f'./account/{account}/')
                print(f'{account} - not working')

    # for account in get_json:
    #     print(get_json[account])
    #
    # # print('work')
    # spam = True
    # Если в аргументах функции указали что нам нужен спам (что бы не вызвать повторное подключение аккаунта)

    if spam == True:
        # Перменные
        spam_id = {}
        is_send = []
        num = 0
        x, alls, no = 0, 0, 0

        # Читаем локации людей рядом
        location = select_location('location_search')[0]
        # Получаем айдишники тех кому мы уже отправляли
        received_ids = [true_id[0] for true_id in select_received()]

        # Цикл аккаунтов из json
        for accounts in get_json:
            # получаем людей рядом
            check_account = str(accounts)+'_'+str(get_json[accounts])
            result = await get_client[get_json[accounts]](functions.contacts.GetLocatedRequest(
                geo_point=InputGeoPoint(lat=float(location[1]), long=float(location[2]))
            ))
            # Заполняем id и access_hash в словарь
            for user in result.users:
                num += 1
                # Получем универсальный access_hash ( у каждого акканта свой ) и заполняем в словарь spam_id
                input_peer = InputPeerUser(user.id, user.access_hash)
                spam_id[check_account+'_'+str(num)] = input_peer

        # print(spam_id)
        # input()

        # Работает со словарем что бы получить что мы добавили в словарь
        for get_spam_id in spam_id:
            # Проверяем кому мы уже писали а кому нет, что бы избежать
            if spam_id[get_spam_id].user_id not in received_ids:
                # Получаем из spam_id информацию и добавляем в список
                user_ids = str(spam_id[get_spam_id].user_id)+'_'+get_spam_id.split('_')[1]
                access_hash = spam_id[get_spam_id].access_hash

                is_send.append({user_ids: access_hash})

        # перемешаем словарь
        random.shuffle(is_send)
        unique_numbers = set()

        # Сортируем айдишники что бы не повторялись в случае спамма (он мог бы несколько раз добавить одних и тех же людей)
        for dictionary in is_send:
            number = list(dictionary)[0].split('_')[0]
            # если нету такого айди в перменной тогда добавляем
            if number not in unique_numbers:
                unique_numbers.add(number)
                value = list(dictionary.keys())[0]
                user_idk = value.split('_')
                cliens = get_client[user_idk[1]]
                input_peer = InputPeerUser(int(user_idk[0]), dictionary[value])
                alls += 1
                try:

                    # отправляем сообщение
                    await cliens.send_message(input_peer, random.choice(select_random_word())[1])
                    # добавляем айди того кому отправили в базу данных
                    insert_received(input_peer.user_id)
                    x += 1
                except Exception as e:
                    no += 1
                    print('Ошибка -', e)

        # сообщаем что спам закончен из бд
        for admin_id in select_admin():
            bot_two.send_message(admin_id, f'Все, спам закончился, отправил {x}/{alls} (не {no})')

    # Ответ тем кто задал у нас вопрос
    if send != None:
        # получаем всех тех кому мы писали
        async for dialog in get_client[account].iter_dialogs():
            # если айди нашелся того который нам писал
            if dialog.id == int(user_id):
                # отправляем сообщение
                await get_client[account].send_message(dialog.id, send)

    # Когда мы добавили аккаунт в базу, он запускает функцию что бы он мог тоже читать что ему напишут и отправлять админам
    if data is None:
        if send is None:
            for i in get_client:
                asyncio.create_task(message_listener(get_client[i]))
    else:
        asyncio.create_task(message_listener(get_client[data]))

    # если аккаунт не запущен
    if account_state == 0:
        # делает статус 1, все аккаунт запущен
        account_state = 1
        # не помню, но не трогай а то пизда коду
        while True:
            await asyncio.sleep(0.5)

@dp.message_handler(state=UserState.args)
async def handler_text(message, state=FSMContext):
    args = await state.get_data()

    from_id = str(args['args']).split('_')[1]
    bot_id = str(args['args']).split('_')[2]

    await main(get_json[int(bot_id)], send=message.text, user_id=from_id)
    await message.answer('Сообщение отправлено')
    await state.finish()

# добавляем аккаунт и качаем архив
@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_archive(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    file_name = message.document.file_name

    await bot.download_file_by_id(file_id, f"{file_name}")

    with zipfile.ZipFile(file_name, "r") as zip_ref:
        nested_folders = set()

        for name in zip_ref.namelist():
            if '/' in name:
                nested_folder = name.split('/')[0]
                nested_folders.add(nested_folder)
        try:
            if nested_folder == 0:
                pass
        except:
            nested_folder = None

        if nested_folder == None:

            name = ''

            with zipfile.ZipFile(f"{file_name}", "r") as inner_zip_ref:
                name = [name for name in inner_zip_ref.namelist() if '.session' in name][0]
                inner_zip_ref.extractall(f'./sessions_to_tdata/',members=[name for name in inner_zip_ref.namelist()])

            # input()
            # print(name)
            await SessionToTData(name.split('.')[0])

            new_name = f"tdata{name.split('.')[0]}"

        else:

            target_folder = None
            for folder in nested_folders:
                with zipfile.ZipFile('./'+file_name, "r") as inner_zip_ref:
                    inner_files = inner_zip_ref.namelist()
                    if any(file.startswith(f"{folder}/tdata/") for file in inner_files):
                        target_folder = folder
                        break
                    elif any(file.startswith(f"tdata/") for file in inner_files):
                        target_folder = 'tdata'
                        break

            if target_folder is None:
                await message.reply("Не удалось найти папку 'tdata' в архиве.")
                return

            if target_folder == 'tdata':
                new_folder = f'tdata{random.randint(10000,10000000)}'

            # zip_ref.extractall(DOWNLOAD_FOLDER)

            tdata_folder_name = None
            with zipfile.ZipFile(f"{file_name}", "r") as inner_zip_ref:
                for name in inner_zip_ref.namelist():
                    if name.startswith(f"{target_folder}/tdata/") and target_folder != 'tdata':
                        tdata_folder_name = name.split('/')[1]
                        break
                    elif name.startswith(f"tdata/") and target_folder == 'tdata':
                        tdata_folder_name = 'tdata'
                        break


                if tdata_folder_name is None:
                    await message.reply("Не удалось найти папку 'tdata' внутри найденной папки.")
                    return

                if target_folder != 'tdata':
                    inner_zip_ref.extractall(DOWNLOAD_FOLDER, members=[name for name in inner_zip_ref.namelist() if name.startswith(f"{target_folder}/tdata/")])
                else:
                    # os.mkdir(os.path.join(DOWNLOAD_FOLDER, new_folder))
                    inner_zip_ref.extractall(f'{DOWNLOAD_FOLDER}/{new_folder}', members=[name for name in inner_zip_ref.namelist() if name.startswith(f"tdata/")])

                    target_folder = new_folder

            new_name = f'tdata{str(random.randint(100, 100000))}'
            os.rename(f'{DOWNLOAD_FOLDER}/{target_folder}/{tdata_folder_name}', f'./account/{new_name}')

        tdataFolders = f"./account/{new_name}"
        # print(tdataFolders)
        tdesk = TDesktop(tdataFolders)
        client = await tdesk.ToTelethon(session=f"./session/{new_name}.session", flag=UseCurrentSession)




    try:
        await client.start()
        await message.reply("Файлы успешно загружены!")

        if message.caption != None:

            conn = sqlite3.connect('Proxies.db', check_same_thread=False)
            cur = conn.cursor()

            cur.execute("""SELECT proxyData FROM Proxies WHERE accountName = ?""", (new_name,))
            try:
                a = cur.fetchone()[0]
                cur.execute("""UPDATE Proxies SET proxyData = ? WHERE accountName = ?""", (message.caption, new_name))
            except:
                cur.execute("""INSERT INTO Proxies VALUES (?,?,?)""", (str(uuid.uuid4()), new_name, message.caption))

            conn.commit()
            conn.close()




        user = await client.get_me()

        get_json.update({user.id: new_name})
        get_client.update({new_name: client})

        await main(os.listdir('./account/'), data=new_name)
    except:

        traceback.print_exc()

        await message.reply("Файлы невалидные")

@dp.message_handler(commands='start')
async def start(message):
    admins = select_admin()
    Nadmins = []
    for i in admins:
        Nadmins.append(i[0])

    if not admins:
        keyboards = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button = types.KeyboardButton(text="Отправить местоположение", request_location=True)
        keyboards.add(button)
        await message.answer("Нажмите кнопку для отправки местоположения", reply_markup=keyboards)
    else:
        # for admin_id in admins:
        if message.from_user.id in Nadmins or message.from_user.id in admin:
            await message.answer(
                text='Добро пожаловать в бота, вы находитесь в админ панеле, выберите нужный пункт.',
                reply_markup=keyboard
            )

@dp.callback_query_handler()
async def handler_check_callback(call, state=FSMContext):

    if call.data == 'back_for_admin':
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Добро пожаловать в бота, вы находитесь в админ панеле, выберите нужный пункт',
            reply_markup=keyboard
        )
        await state.finish()

    admin_keyboard = InlineKeyboardMarkup(row_width=1)
    if call.data == 'admin':
        if not select_admin():
            admin_keyboard.add(
                InlineKeyboardButton('➕ Админ', callback_data='add_admin')
            )
            await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text='Админов нету', reply_markup=admin_keyboard
            )
        else:
            for admin_id in select_admin():
                admin_keyboard.add(
                    InlineKeyboardButton(str(admin_id[0]), callback_data=f'adm_{admin_id[0]}')
                )
            admin_keyboard.add(
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin'),
                InlineKeyboardButton('➕ Админ', callback_data='add_admin')
            )

            await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text='Список админов',
                reply_markup=admin_keyboard
            )

    if call.data.startswith('adm_'):
        del_admin = InlineKeyboardMarkup()
        calldata = call.data.split('_')[1]
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Администратор №{calldata}',
            reply_markup=del_admin.add(
                InlineKeyboardButton('🗑️ Удалить', callback_data=f'delet_admin_{calldata}'),
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            )
        )

    if call.data.startswith('delet_admin'):
        calldata = call.data.split('_')[2]

        delete_admin(calldata)

        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Администратор №{calldata} был удален с поста.',
            reply_markup=keyboard
        )

    if call.data == 'add_admin':
        msg = await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Введите айди админа',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            )
        )
        await state.update_data(admin=msg.message_id)
        await UserState.admin.set()

    if call.data.startswith('answer'):
        await state.update_data(args=call.data)
        await UserState.args.set()

        await bot.send_message(call.message.chat.id, 'Введите сообщение которое вы хотите отправить:')

    if call.data == 'account':
        key = InlineKeyboardMarkup()
        for i in get_json:
            check = InlineKeyboardButton(f'{i}', callback_data=f'check_{i}')
            key.add(check)
        key.add(
            InlineKeyboardButton('👁‍🗨 Проверить', callback_data='read_work_account'),
            InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
        )

        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Список всех аккаунтов",
            reply_markup=key
        )

    if call.data.startswith('check'):

        calldata = call.data.split('_')[1]
        account = get_json[int(calldata)]
        info = await get_client[account].get_me()

        key = InlineKeyboardMarkup(row_width=1)
        check = InlineKeyboardButton(f'🗑️ Удалить', callback_data=f'delete_{calldata}')
        back = InlineKeyboardButton(f'🔙 Назад', callback_data=f'back')
        key.add(check, back)

        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'''<b>👤 Имя: {info.first_name}\n🆔 ID: {info.id}\n🗑 Удален: {info.deleted}\n☎️ Телефон: +{info.phone}\n🔐 Блокировка: {info.restricted}</b>''',
            parse_mode='HTML',
            reply_markup=key
        )

    if call.data == 'back':
        key = InlineKeyboardMarkup()
        for i in get_json:
            check = InlineKeyboardButton(f'{i}', callback_data=f'check_{i}')
            key.add(check)
        key.add(
            InlineKeyboardButton('👁‍🗨 Проверить', callback_data='read_work_account'),
            InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
        )

        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Список всех аккаунтов: ',
            reply_markup=key
        )

    if call.data.startswith('delete'):
        calldata = call.data.split('_')[1]
        account = get_json[int(calldata)]
        await get_client[account].disconnect()
        shutil.rmtree(f'./account/{account}')
        del get_client[account]
        del get_json[int(calldata)]

        key = InlineKeyboardMarkup()
        for i in get_json:
            check = InlineKeyboardButton(f'{i}', callback_data=f'check_{i}')
            key.add(check)
        key.add(
            InlineKeyboardButton('👁‍🗨 Проверить', callback_data='read_work_account'),
            InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
        )

        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Список всех аккаунтов: ',
            reply_markup=key
        )

    if call.data == 'coworking':
        coworking = InlineKeyboardMarkup()
        if not select_location('location_coworking'):
            coworking.add(
                InlineKeyboardButton('➕ Коворкинг', callback_data='coworking_add'),
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            )

            await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text='Нету коворкингов',
                reply_markup=coworking
            )
        else:
            for id_coworking in select_location('location_coworking'):
                coworking.add(
                    InlineKeyboardButton(f'{get_name_position(id_coworking[1], id_coworking[2])}', callback_data=f'cw_{id_coworking[0]}')
                )
            coworking.add(
                InlineKeyboardButton('➕ Коворкинг', callback_data='coworking_add'),
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            )

            await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text='Список всех коворкингов',
                reply_markup=coworking
            )

    if call.data.startswith('cw_'):
        info_location = InlineKeyboardMarkup()
        calldata = call.data.split('_')[1]
        location = select_location_where(mode='location_coworking', where_id=calldata)
        for position in location:
            info_location.add(
                InlineKeyboardButton('🗑️ Удалить', callback_data=f'dl_cw_{position[0]}'),
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            )
            await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'Улица {get_name_position(position[1], position[2])}\nКоординаты: {position[1]}, {position[2]}',
                reply_markup=info_location
            )

    if call.data == 'coworking_add':
        msg = await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Введите ширину и долготу через /\nПример: <b>38.000/14.000</b>',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            ),
            parse_mode='html'
        )
        await state.update_data(coworking_id_msg=msg.message_id)
        await UserState.coworking_id_msg.set()

    if call.data.startswith('dl_cw_'):
        calldata = call.data.split('_')[2]

        delete_location(calldata, 'location_coworking')

        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Коворкинг был удален.',
            reply_markup=keyboard
        )

    if call.data == 'search':
        people = InlineKeyboardMarkup(row_width=1)

        if not select_location('location_search'):
            people.add(
                InlineKeyboardButton('🛠 Локация', callback_data='people_add'),
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            )

            await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'Локации для поиска людей рядом нету.',
                reply_markup=people
            )

        else:
            for people_near in select_location('location_search'):
                people.add(
                    InlineKeyboardButton(get_name_position(people_near[1], people_near[2]), callback_data=f'search_people_{people_near[0]}')
                )

            people.add(
                InlineKeyboardButton('▶️ Старт', callback_data='start_spam'),
                InlineKeyboardButton('🛠 Локация', callback_data='people_add'),
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            )

            await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'Локации для поиска людяй рядом.',
                reply_markup=people
            )

    if call.data == 'read_work_account':
        true_account, false_account = 0, 0

        await bot.send_message(call.message.chat.id, 'Началась проверка аккаунтов')
        for user_id in get_json:
            tdata = get_json[user_id]
            try:
                true_account += 1
                me = await get_client[tdata].get_me()
                # print(me)
            except:
                false_account += 1
                del get_json[user_id]
                del get_client[tdata]
        await bot.send_message(call.message.chat.id, f'<b>Удаленных: {false_account}\nРабочих: {true_account}\nРабочие {true_account} из {true_account+false_account}</b>', parse_mode='html')

    if call.data == 'people_add':
        msg = await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Введите ширину и долготу через /\nПример: <b>38.000/14.000</b>',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            ),
            parse_mode='html'
        )
        await state.update_data(people_near_id=msg.message_id)
        await UserState.people_near_id.set()

    if call.data.startswith('search_people_'):
        calldata = call.data.split('_')[2]
        info_location = InlineKeyboardMarkup(row_width=1)
        info = select_location_where('location_search', calldata)
        for location_info in info:
            info_location.add(
                InlineKeyboardButton('🗑️ Удалить', callback_data=f'pl_sr_{location_info[0]}'),
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            )
            await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'Улица {get_name_position(location_info[1], location_info[2])}\nКоординаты: {location_info[1]}, {location_info[2]}',
                reply_markup=info_location
            )

    if call.data.startswith('pl_sr_'):
        calldata = call.data.split('_')[2]

        delete_location(calldata, 'location_search')

        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Локация была удалена.',
            reply_markup=keyboard
        )


    if call.data == 'reply':
        reply = InlineKeyboardMarkup(row_width=1)

        if not select_location('location_search'):
            reply.add(
                InlineKeyboardButton('➕ Ответ', callback_data='reply_add'),
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            )

            await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'Ответов в базе нету',
                reply_markup=reply
            )

        else:
            for reply_check in select_random_word():
                reply.add(
                    InlineKeyboardButton(reply_check[1],
                                         callback_data=f'srp_{reply_check[0]}')
                )

            reply.add(
                InlineKeyboardButton('➕ Ответ', callback_data='reply_add'),
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            )

            await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'Ответы для спама.',
                reply_markup=reply
            )

    if call.data == 'reply_add':
        msg = await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Введите текст для ответа',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            ),
            parse_mode='html'
        )
        await state.update_data(reply_id=msg.message_id)
        await UserState.reply_id.set()

    if call.data.startswith('srp_'):
        word_info = InlineKeyboardMarkup()
        calldata = call.data.split('_')[1]
        location = where_select_random_word(calldata)
        for words in location:
            word_info.add(
                InlineKeyboardButton('🗑️ Удалить', callback_data=f'rp_del_{words[0]}'),
                InlineKeyboardButton('🔙 Назад', callback_data='back_for_admin')
            )
            await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f'Ответы при спаме: {words[1]}',
                reply_markup=word_info
            )

    if call.data.startswith('rp_del_'):
        calldata = call.data.split('_')[2]

        delete_word(calldata)

        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'Ответ был удален.',
            reply_markup=keyboard
        )


    if call.data == 'start_spam':
        await bot.send_message(call.message.chat.id, 'Спам начался')
        await state.update_data(user_id=call.from_user.id)
        await main(os.listdir('./account/'), spam=True)

@dp.callback_query_handler(state=UserState.reply_id)
async def handler_check_callback(call, state=FSMContext):
    if call.data == 'back_for_admin':
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Добро пожаловать в бота, вы находитесь в админ панеле, выберите нужный пункт',
            reply_markup=keyboard
        )
        await state.finish()

@dp.message_handler(state=UserState.reply_id)
async def add_administrator(message, state=FSMContext):
    data = await state.get_data()
    insert_word(message.text)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['reply_id'],
        text='Ответ добавлен',
        reply_markup=keyboard
    )
    await state.finish()


@dp.callback_query_handler(state=UserState.people_near_id)
async def handler_check_callback(call, state=FSMContext):
    if call.data == 'back_for_admin':
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Добро пожаловать в бота, вы находитесь в админ панеле, выберите нужный пункт',
            reply_markup=keyboard
        )
        await state.finish()

@dp.message_handler(state=UserState.people_near_id)
async def add_administrator(message, state=FSMContext):
    data = await state.get_data()
    location = message.text.split('/')
    insert_location(location[0], location[1], 'location_search')
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['people_near_id'],
        text='Локация изменена',
        reply_markup=keyboard
    )
    await state.finish()



@dp.callback_query_handler(state=UserState.coworking_id_msg)
async def handler_check_callback(call, state=FSMContext):
    if call.data == 'back_for_admin':
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Добро пожаловать в бота, вы находитесь в админ панеле, выберите нужный пункт',
            reply_markup=keyboard
        )
        await state.finish()

@dp.message_handler(state=UserState.coworking_id_msg)
async def add_administrator(message, state=FSMContext):
    data = await state.get_data()
    location = message.text.split('/')
    insert_location(location[0], location[1], 'location_coworking')
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['coworking_id_msg'],
        text='Коворкинг добавлен',
        reply_markup=keyboard
    )
    await state.finish()

@dp.callback_query_handler(state=UserState.admin)
async def handler_check_callback(call, state=FSMContext):

    if call.data == 'back_for_admin':
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='Добро пожаловать в бота, вы находитесь в админ панеле, выберите нужный пункт',
            reply_markup=keyboard
        )
        await state.finish()


@dp.message_handler(state=UserState.admin)
async def add_administrator(message, state=FSMContext):
    data = await state.get_data()
    insert_admin(message.text)
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['admin'],
        text='Админ добавлен',
        reply_markup=keyboard
    )
    await state.finish()

@dp.message_handler(content_types=[types.ContentType.LOCATION])
async def handle_location(message: types.Message):
    closest_coordinate = None
    min_distance = float("inf")

    # получаем локацию пользователя
    latitude = message.location.latitude
    longitude = message.location.longitude

    # тут мы получаем все коворкинги рядом
    for coordinate in select_location('location_coworking'):
        # сравниваем на сколько близко
        dist = haversine_distance(latitude, longitude, float(coordinate[1]), float(coordinate[2]))
        if dist < min_distance:
            min_distance = dist
            closest_coordinate = coordinate

    # пишем
    await message.answer(f"Улица ближе всего к вам: {get_name_position(closest_coordinate[1], closest_coordinate[2])}")

if __name__ == '__main__':
    # запуск бота и аккантов, не трогай убьет током!
    loop = asyncio.get_event_loop()
    loop.create_task(main(array=os.listdir('./account/')))
    executor.start_polling(dp, skip_updates=True)
    loop.run_forever()
