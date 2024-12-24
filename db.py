import sqlite3
from datetime import datetime
import json

def get_db_connection():
    conn = sqlite3.connect('project.db')
    conn.row_factory = sqlite3.Row  # Для обращения к данным по имени столбца
    return conn

# Создание таблиц
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        birth_date TEXT,
        stylist BOOLEAN DEFAULT 0,
        level INTEGER DEFAULT 0,
        photo_path TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_parameters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        height REAL,
        weight REAL,
        chest_size REAL,
        ass_size REAL,
        waist_size REAL,
        clothes_size TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stylist_docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        resume_path TEXT,
        certificate_path TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_chats (
        user_chats_id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        creator_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES user_chats(chat_id),
        FOREIGN KEY (creator_id) REFERENCES users(user_id)
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_read_status (
        chat_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        last_read TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (chat_id, user_id),
        FOREIGN KEY (chat_id) REFERENCES user_chats(chat_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shmotki (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        shmotka_id TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER NOT NULL,
            stylist_id INTEGER NOT NULL,
            score INTEGER,
            text TEXT,
            order_id INTEGER,
            FOREIGN KEY (creator_id) REFERENCES users(user_id)
            FOREIGN KEY (stylist_id) REFERENCES users(user_id)
        );
        ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_anketa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            anketa_purpose TEXT,
            anketa_style TEXT,
            anketa_season TEXT,
            anketa_price_range TEXT,
            gender INTEGER,
            work TEXT,
            hair_color TEXT,
            size_top TEXT,
            size_bottom TEXT,
            kabluck TEXT,
            skinny_or_not_top TEXT,
            skinny_or_not_bottom TEXT,
            jeans_type TEXT,
            posadka TEXT,
            jeans_length TEXT,
            length TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            stylist_id  INTEGER NOT NULL,
            order_status TEXT,
            FOREIGN KEY (client_id) REFERENCES users(user_id)
            FOREIGN KEY (stylist_id) REFERENCES users(user_id)
        );
        ''')    

    conn.commit()
    conn.close()

# добавление пользователя
def add_user(first_name, last_name, password, email, birth_date, stylist, level, photo_path): # Добавить исключение и возвращение результата
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO users (first_name, last_name, password, email, birth_date, stylist, level, photo_path)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    ''', (first_name, last_name, password, email, birth_date, stylist, level, photo_path))
    conn.commit()
    conn.close()

# добавление параметров пользователя
def add_user_params(height, weight, chest_size, ass_size, waist_size, clothes_size, email):
    user_id=get_user_info_by_email(email)['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO user_parameters (user_id, height, weight, chest_size, ass_size, waist_size, clothes_size)
    VALUES(?, ?, ?, ?, ?, ?, ?) 
    ''',(user_id, height, weight, chest_size, ass_size, waist_size, clothes_size))

    conn.commit()
    conn.close()

# сохранение анкеты пользователя
def save_user_anketa(user_id, anketa):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Преобразуем словари в JSON строки перед сохранением
    anketa_data = {
        key: json.dumps(anketa.get(key))
        for key in [
            'purpose', 'style', 'season', 'price_range', 'gender',
            'work', 'hair_color', 'size_top', 'size_bottom',
            'kabluck', 'skinny_or_not_top', 'skinny_or_not_bottom',
            'jeans_type', 'posadka', 'jeans_length', 'length'
        ]
    }

    cursor.execute('''
    INSERT INTO user_anketa (
        user_id, anketa_purpose, anketa_style, anketa_season, anketa_price_range,
        gender, work, hair_color, size_top, size_bottom, kabluck,
        skinny_or_not_top, skinny_or_not_bottom, jeans_type, posadka,
        jeans_length, length
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        anketa_data['purpose'],
        anketa_data['style'],
        anketa_data['season'],
        anketa_data['price_range'],
        anketa_data['gender'],
        anketa_data['work'],
        anketa_data['hair_color'],
        anketa_data['size_top'],
        anketa_data['size_bottom'],
        anketa_data['kabluck'],
        anketa_data['skinny_or_not_top'],
        anketa_data['skinny_or_not_bottom'],
        anketa_data['jeans_type'],
        anketa_data['posadka'],
        anketa_data['jeans_length'],
        anketa_data['length']
    ))

    for i in range(1, 11):
        skin = f'skin{i}_likes'
        skin_value = anketa.get(skin)
        # Преобразуем в JSON если это словарь
        if isinstance(skin_value, dict):
            skin_value = json.dumps(skin_value)
            
        cursor.execute('''
        INSERT INTO shmotki (user_id, shmotka_id)
        VALUES (?, ?)
        ''', (user_id, skin_value))
    conn.commit()
    conn.close()

# сохранение резюме стилиста
def save_stylist_docs(user_id, resume_path, certificate_path):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO stylist_docs (user_id, resume_path, certificate_path)
    VALUES (?, ?, ?)
    ''', (user_id, resume_path, certificate_path))

    conn.commit()
    conn.close()

# добавление отзыва
def add_feedback(stylist_id, user_id, score, text, order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO feedbacks (stylist_id, score, text, creator_id, order_id) VALUES (?, ?, ?, ?, ?)', 
                   (stylist_id, score, text, user_id, order_id))
    conn.commit()
    conn.close()

    update_level(stylist_id)

def update_level(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    average_score = get_average_score(user_id)
    number_of_completed_orders = count_completed_orders(user_id)

    if number_of_completed_orders >= 5 and average_score * number_of_completed_orders >= 20:
        level = 'middle'
    elif number_of_completed_orders >= 10 and average_score * number_of_completed_orders >= 40 and average_score >= 4.5:
        level = 'senior'
    else:
        level = 'junior'

    if level == 'junior':
        level = 0
    elif level == 'middle':
        level = 1
    elif level == 'senior':
        level = 2

    cursor.execute('UPDATE users SET level = ? WHERE user_id = ?', (level, user_id))
    conn.commit()
    conn.close()

def count_completed_orders(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM completed_orders WHERE stylist_id = ?', (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

# получение резюме стилиста
def get_resume_path(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT resume_path FROM stylist_docs WHERE user_id = ?', (user_id,))
    resume_path = cursor.fetchone()[0]
    conn.close()
    return resume_path

# обновление резюме стилиста
def update_resume(user_id, resume_path):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('UPDATE stylist_docs SET resume_path = ? WHERE user_id = ?', (resume_path, user_id))
    conn.commit()
    conn.close()

# плучение информации о пользователе по email
def get_user_info_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user_info = cursor.fetchone()
    conn.close()
    return dict(user_info) if user_info else None

# получение информации о пользователе по id
def get_user_info_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user_info = cursor.fetchone()
    conn.close()
    return dict(user_info) if user_info else None

# получение списка клиентов
def get_CL_list():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE stylist = 0')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# получение списка стилистов
def get_ST_list():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE stylist = 1')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# получение параметро пользователя
def get_user_params(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM user_parameters WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# получение истории заказов
def get_completed_orders_client(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT DISTINCT co.*, 
           u1.first_name as client_name, 
           u2.first_name as stylist_name,
           u2.level as stylist_level
    FROM completed_orders co
    JOIN users u1 ON co.client_id = u1.user_id
    JOIN users u2 ON co.stylist_id = u2.user_id
    WHERE co.client_id = ?
    AND co.order_status = 'completed'
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# получение заказов стилиста
def get_completed_orders_stylist(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT DISTINCT co.*, 
           u1.first_name as client_name, 
           u2.first_name as stylist_name
    FROM completed_orders co
    JOIN users u1 ON co.client_id = u1.user_id
    JOIN users u2 ON co.stylist_id = u2.user_id
    WHERE co.stylist_id = ?
    AND co.order_status = 'completed'
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# получение отзыв��в оставленных клиентом
def get_comments(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM feedbacks WHERE creator_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# получение отзывов оставленных стилистом
def get_feedbacks(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT f.*, u.*
    FROM feedbacks f
    JOIN users u ON f.creator_id = u.user_id
    WHERE f.stylist_id = ?
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# получение id стилиста по id заказа
def get_stylist_id_by_order_id(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT stylist_id FROM completed_orders WHERE id = ?', (order_id,))
    stylist_id = cursor.fetchone()[0]
    conn.close()
    return stylist_id

# получение id клиента по id заказа
def get_client_id_by_order_id(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT client_id FROM completed_orders WHERE id = ?', (order_id,))
    client_id = cursor.fetchone()[0]
    conn.close()
    return client_id

# получение текущих заказов
def get_current_orders(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT DISTINCT 
           co.id as order_id,
           co.client_id,
           co.stylist_id,
           co.order_status,
           u1.user_id as client_user_id,
           u1.first_name as client_first_name,
           u1.last_name as client_last_name,
           u1.email as client_email,
           u1.photo_path as client_photo,
           u2.user_id as stylist_user_id,
           u2.first_name as stylist_first_name,
           u2.last_name as stylist_last_name,
           u2.email as stylist_email,
           u2.photo_path as stylist_photo
    FROM completed_orders co
    JOIN users u1 ON co.client_id = u1.user_id
    JOIN users u2 ON co.stylist_id = u2.user_id
    WHERE (co.client_id = ? OR co.stylist_id = ?)
    AND co.order_status = 'active'
    ''', (user_id, user_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_average_score(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT AVG(score) FROM feedbacks WHERE stylist_id = ?', (user_id,))
    average_score = cursor.fetchone()[0]
    conn.close()
    return average_score

# З��вершение заказа
def complete_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('UPDATE completed_orders SET order_status = ? WHERE id = ?', ('completed', order_id))
    conn.commit()
    conn.close()

##################################################################################################
############################ ЧАТЫ ################################################################

# удаление чата
def delete_chat(stylist_id, client_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    chat_id = get_chat_between_users(stylist_id, client_id)['chat_id']

    delete_messages(chat_id)
    delete_chat_read_status(chat_id)
    cursor.execute('DELETE FROM user_chats WHERE chat_id = ?', (chat_id,))
    conn.commit()
    conn.close()

# удаление сообщений
def delete_messages(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
    conn.commit()
    conn.close()

# удаление статуса прочтения чата
def delete_chat_read_status(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM chat_read_status WHERE chat_id = ?', (chat_id,))
    conn.commit()
    conn.close()

# получение чата между двумя пользователями
def get_chat_between_users(user1_id, user2_id): # 
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT uc.chat_id, uc.user_id
    FROM user_chats uc
    WHERE uc.user_id = ? 
    AND EXISTS (
        SELECT 1 
        FROM user_chats uc2
        WHERE uc2.chat_id = uc.chat_id
        AND uc2.user_id = ?
    )
    ''', (user1_id, user2_id))

    chat = cursor.fetchone()
    conn.close()
    return dict(chat) if chat else None

# Функция для создания чата
def create_chat(user_ids):
    conn = get_db_connection()
    cursor = conn.cursor()

    create_order(user_ids[0], user_ids[1])

    chat_id = get_chat_last_id()
    print(f'Last chat id: {chat_id}')
    if chat_id is None or chat_id == 0:
            chat_id = 1
    try:
        # Создаем чат с первым участником для получения chat_id
        cursor.execute('''
        INSERT INTO user_chats (chat_id, user_id)
        VALUES (?, ?);
        ''', (chat_id, user_ids[0],))
        

        cursor.execute('''
        INSERT INTO user_chats (chat_id, user_id)
        VALUES (?, ?);
        ''', (chat_id, user_ids[1]))

        # Завершаем транзакцию
        conn.commit()
        conn.close()

        return chat_id

    except Exception as e:
        # В случае ошибки откатываем все изменения
        conn.rollback()
        conn.close()
        raise e

# создание заказа
def create_order(client_id, stylist_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO completed_orders (client_id, stylist_id, order_status) VALUES (?, ?, ?)', (stylist_id, client_id, 'active'))
    conn.commit()
    conn.close()

# обновление статуса заказа
def update_order_status(order_id): ### ??? испошльзовать id пользователя\стилиста
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('UPDATE completed_orders SET order_status = ? WHERE id = ?', ('completed', order_id))
    conn.commit()
    conn.close()

def get_chat_last_id():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(chat_id) FROM user_chats')
    chat_id = cursor.fetchone()[0]
    print(f'Last chat id: {chat_id}')
    conn.close()
    return chat_id

# Функция для получения чатов пользователя по user_id
def get_user_chats(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT * from user_chats JOIN users on user_chats.user_id = users.user_id WHERE users.user_id = ?''',(user_id,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows] if rows else None

# Функция для получения чатов и пользовтелей в этом чате по chat_id
def get_chats(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT * from user_chats JOIN users on user_chats.user_id = users.user_id WHERE user_chats.chat_id = ?''',(chat_id,)) # Возвращает список чатов

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows] if rows else None

# Функция для отправки сообщения
def send_message(chat_id, recipient_id, creator_id, message): # Под вопросом
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO messages (chat_id, creator_id, recipient_id, message)
    VALUES (?, ?, ?);
    ''', (chat_id, creator_id, recipient_id, message))
    conn.commit()
    conn.close()

# Функция для обновления времени последнего прочтения чата
def mark_chat_as_read(chat_id, user_id): # Вроде должно работать
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO chat_read_status (chat_id, user_id, last_read)
    VALUES (?, ?, datetime('now', 'localtime'))
    ON CONFLICT (chat_id, user_id) DO UPDATE SET
        last_read = datetime('now', 'localtime');
    ''', (chat_id, user_id,))
    conn.commit()
    conn.close()

# Функция для получения непрочитанных сообщений
def get_unread_messages(chat_id, user_id): # ��од вопросом
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT *
    FROM messages m
    LEFT JOIN chat_read_status crs ON crs.chat_id = m.chat_id AND crs.user_id = ?
    WHERE m.chat_id = ?
    AND (crs.last_read IS NULL OR m.timestamp > crs.last_read)
    ORDER BY m.timestamp;
    ''', (user_id, chat_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Функция для получения нпрочинных сообщений пользователя
def get_user_unread_messages(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT *
    FROM chat_read_status crs
    LEFT JOIN messages m ON m.chat_id = crs.chat_id
    AND (crs.last_read IS NULL OR m.timestamp > crs.last_read)
    WHERE crs.user_id = ? AND m.creator_id IS NOT ? 
    ORDER BY m.timestamp;
    ''',(user_id, user_id)) # Возвращает непрочитанные сообщения, где пользователь не автор

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Функция для получения сообщений в чате
def get_chat_messages(chat_id,): # Работает
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT *
    FROM messages
    JOIN users ON messages.creator_id = users.user_id
    WHERE messages.chat_id = ?
    ORDER BY messages.timestamp ASC
    ''', (chat_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Функция для сохранения нового сообщения
def save_message(chat_id, sender_id, message): # Вроде должно работать
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO messages (chat_id, creator_id, message, timestamp)
    VALUES (?, ?, ?, datetime('now', 'localtime'))
    ''', (chat_id, sender_id, message))
    conn.commit()
    conn.close()

# Функция для получения последнего сообщения в чате
def get_last_message(chat_id,): # Работает
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT message
    FROM messages
    JOIN users ON messages.creator_id = users.user_id
    WHERE messages.chat_id = ?
    ORDER BY messages.timestamp DESC LIMIT 1;
    ''', (chat_id,))
    message = cursor.fetchone()
    conn.close()
    if message != None:
        return dict(message)['message']
    else:
        return 'Нет сообщений'



def get_anketi():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM user_anketa')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_skins():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM shmotki')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users JOIN user_parameters ON users.user_id = user_parameters.user_id WHERE stylist = 0')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_users_without_chats():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT DISTINCT u.*, up.*
    FROM users u
    JOIN user_parameters up ON u.user_id = up.user_id
    WHERE u.stylist = 0
    AND u.user_id NOT IN (
        SELECT user_id 
        FROM user_chats
    )
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_stylists():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE stylist = 1') #JOIN stylist_docs ON users.user_id = stylist_docs.user_id
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]