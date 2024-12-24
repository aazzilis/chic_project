from datetime import datetime
import os
from flask import Flask, json, jsonify, render_template, request, redirect, send_file, url_for, session, flash
from flask_socketio import SocketIO, emit, join_room, leave_room
import db
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'
socketio = SocketIO(app)
anketa = {}

@app.route('/') # Индекс
def start_page():
    print(session)
    if 'email' in session:
        user_session = 1
    else:
        user_session = 0
    db.create_tables()
    return render_template('index.html', user_session = user_session)

##################################################################################################
############################ РЕГИСТРАЦИЯ\ АВТОРИЗАЦИЯ ############################################

@app.route('/chooseClientOrStyle') # выбор роли (стилист\клиент)
def chooseClientOrStyle():
    return render_template('chooseClientOrStyle.html')

@app.route('/auth', methods=['POST', 'GET']) # авторизация
def auth_page():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        userInfo = db.get_user_info_by_email(email)
        print(userInfo)
        if userInfo:
            print('Правильное мыло')
            if password == userInfo.get('password'):
                print('Правильный пароль')
                session['email'] = email
                if userInfo['stylist'] == 0:
                    return redirect(url_for('lkCL'))  # При удачной авторизации перенаправляется в лк
                if userInfo['stylist'] == 1:
                    return redirect(url_for('lkST'))
            else:
                #flash(message='Неправильный пароль')
                print('Неправильный пароль')
        else:
            #flash(message='Такого пользователя не существует')
            print('Такого пользователя не существует')
    return render_template('auth.html')

@app.route('/registrationCL', methods=['GET', 'POST'])  # регистрация клиента
def registrationCL_page():
    if request.method == 'POST':
        #данные регистрации
        email = request.form.get('email')
        first_name = request.form.get('name')
        last_name = request.form.get('surname')
        password = request.form.get('password')
        birth_date = request.form.get('dob')
        isStylist = False
        level = 0

        #параметры пользователя
        height = request.form.get('height')
        weight = request.form.get('weight')
        chest_size = request.form.get('chest')
        ass_size = request.form.get('hips')
        waist_size = request.form.get('waist') # талия
        clothes_size = request.form.get('size')

        print(f'{email}, {first_name}, height: {height}')

        #retypedPassword = request.form.get('retypedPassword')
        userInfo = db.get_user_info_by_email(email)

        if userInfo is None:
            #if password == retypedPassword:

                db.add_user(first_name= first_name, last_name= last_name, email= email, password= password,
                             birth_date= birth_date, level= level, photo_path= '', stylist= isStylist)
                db.add_user_params(height, weight, chest_size, ass_size, waist_size, clothes_size, email)

                print('Регистрация успешна!')
                session['email'] = email
                #return redirect(url_for('auth_page'))
                return redirect(url_for('anket_gender'))  # Редирект на страницу выбра пола анкета
           #else:
                #flash(message='Пароли не совпадают')
        else:
            #flash(message='Эта почта уже используется')
            print('Эта почта уже используется')

    return render_template('registration.html')  # Возвращаем форму регистрации для GET-запроса

@app.route('/registrationST', methods=['GET', 'POST'])  # регистрация стилиста
def registrationST_page(): 
    if request.method == 'POST':
        #данные регистрации
        email = request.form.get('email')
        first_name = request.form.get('name')
        last_name = request.form.get('surname')
        password = request.form.get('password')
        #birth_date = request.form.get('birth_date')
        isStylist = True
        level = 0

        resume = request.files['resume']
        certificate = request.files['certificate']
        # Сохранение резюме
        if resume:
            resume_filename = secure_filename(resume.filename)
            print(resume_filename)
            resume_path = os.path.join('./static/uploads/resumes', resume_filename)
            resume.save(resume_path)
            
        # Сохранение сертификата    
        if certificate:
            cert_filename = secure_filename(certificate.filename)
            print(cert_filename)
            cert_path = os.path.join('./static/uploads/certificates', cert_filename)
            certificate.save(cert_path)

        #retypedPassword = request.form.get('retypedPassword')
        userInfo = db.get_user_info_by_email(email)

        if userInfo is None:
            #if password == retypedPassword:
                db.add_user(first_name= first_name, last_name= last_name, email= email, 
                             birth_date='NULL', password= password, level= level, photo_path= '', stylist= isStylist)
                user_id = db.get_user_info_by_email(email)['user_id']
                db.save_stylist_docs(user_id=user_id, resume_path=resume_path, certificate_path=cert_path)
                flash('Регистрация успешна!')
                return redirect(url_for('auth_page'))
                #return redirect(url_for('start_page'))  # Редирект на страницу входа после регистрации ???
           #else:
                flash(message='Пароли не совпадают')
        else:
            print('Эта почта уже используется')

    return render_template('registrationStilist.html')  # Возвращаем форму регистрации для GET-запроса

# Завершение заказа  и удаление чата
@app.route('/complete_order/<int:order_id>')
def complete_order(order_id):

    stylist_id = db.get_stylist_id_by_order_id(order_id)
    client_id = db.get_client_id_by_order_id(order_id)

    db.delete_chat(stylist_id, client_id)

    db.complete_order(order_id)
    return redirect(url_for('lkST'))

##################################################################################################
############################ ЛИЧНЫЙ КАБИНЕТ\ ЧАТЫ ################################################

@app.route('/lkCL')
def lkCL():
    email = session['email']
    user_info = db.get_user_info_by_email(email)
    user_params = db.get_user_params(user_info['user_id'])

    birth_date= user_info['birth_date']
    format = '%d.%m.%Y'
    years_old = (datetime.now() - datetime.strptime(birth_date, format)).days // 365

    orders = db.get_completed_orders_client(user_info['user_id'])
    completed_orders = []
    for order in orders:
        completed_orders.append({'stylist_id': order['stylist_id'], 'stylist_name': order['stylist_name'],
                                  'average_score': db.get_average_score(order['stylist_id']), 'order_id': order['id'],
                                  'level': order['stylist_level']})
    print(f'completed_orders: {completed_orders}')
    current_user_comments = db.get_comments(user_info['user_id'])
    print(f'current_user_comments: {current_user_comments}')

    return render_template('lkClient.html', user_info=user_info, params = user_params,
    user_years = years_old, completed_orders = completed_orders, current_user_comments = current_user_comments)

@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.json
    # Получаем email текущего пользователя из сессии
    email = session['email']
    # Получаем информацию о пользователе из БД
    user_info = db.get_user_info_by_email(email)
    # Добавляем отзыв с ID пользователя и заказа
    db.add_feedback(stylist_id=data['stylist_id'], 
                   user_id=user_info['user_id'], 
                   order_id=data['order_id'],  # Добавляем order_id
                   score=data['score'], 
                   text=data['text'])
    return jsonify({'success': True})

@app.route('/chats')
def chats():
    email = session['email']
    user_info = db.get_user_info_by_email(email)

    current_user_chats = db.get_user_chats(user_id=user_info['user_id'])
    #print(f'chats {chats}')

    # Получение информации о пользователях с которыми есть чат, для получения имён
    if current_user_chats:
        chat_ids = [] # Получение списка id чатов
        for chat in current_user_chats:
            chat_ids.append(chat['chat_id'])
        print(f'Current user chats: {chat_ids}')
        user_chats = [] # Список чатов (информ. о других пользов.)
        for id in chat_ids:
            user_chats.append(db.get_chats(id)) # добавление записи в список пользователей
    else:
        user_chats = None

    users = db.get_users() # Получение всех пользователей
    print(f'user chats: {user_chats}')

    if user_chats != None:
        last_messages = []
        for chats in current_user_chats:
            last_messages.append({'chat_id': chats['chat_id'], 'message': db.get_last_message(chats['chat_id'])}) # спсок последних сообщений 
    else:
        last_messages = None

    if user_info['stylist'] == 0: # клиент только стилисту и наоборот
        users = db.get_ST_list()
    else:
        users = db.get_CL_list()

    return render_template('lkClientChat.html', users = users, chats = user_chats,
                            user_id=user_info['user_id'], unreaded=0, stylist = user_info['stylist'], last_message = last_messages,
                            user_info = user_info)

@app.route('/lkST')
def lkST(): ## добавить получение отзывов из бд
    feedbacks_test = [{'id': 1, 'creator_id': 2, 'stylist_id': 2, 'score': 5, 'text': 'Хороший стилист'},
    {'id': 2, 'creator_id': 2, 'stylist_id': 2, 'score': 4, 'text': 'Замечательный стилист'}, 
    {'id': 3, 'creator_id': 3, 'stylist_id': 2, 'score': 5, 'text': 'Чудесный стилист'}, 
    {'id': 4, 'creator_id': 5, 'stylist_id': 2, 'score': 0, 'text': 'Еблан'}, 
    {'id': 5, 'creator_id': 6, 'stylist_id': 2, 'score': 0, 'text': 'Криворукий'}]
    email = session['email']
    user_info = db.get_user_info_by_email(email)
    feedbacks = db.get_feedbacks(user_info['user_id'])

    print(f'feedbacks: {feedbacks}')
    print(f'user_info: {user_info}')

    #### мотьемотическая д'модьель ####
    sum_scores = 0
    for feedback in feedbacks:
        sum_scores += feedback['score']
    average_score = sum_scores / (len(feedbacks) if len(feedbacks) > 0 else 1) 

    # Получение заказов
    completed_orders = db.get_completed_orders_stylist(user_info['user_id']) # завершенные заказы
    current_orders = db.get_current_orders(user_info['user_id']) # активные заказы
    print(f'completed_orders: {completed_orders}')
    print(f'current_orders: {current_orders}')
    # Получение пользователей без чатов
    avaible_users = db.get_users_without_chats() # доступные клиенты

    print(f'avaible users: {avaible_users}')

    return render_template('lkStilist.html', user_info = user_info, feedbacks = feedbacks,
 average_score=average_score, completed_orders = completed_orders, current_orders = current_orders, users = avaible_users) 

@app.route('/download_resume/<int:user_id>')
def download_resume(user_id):
    resume_path = db.get_resume_path(user_id)
    return send_file(resume_path, as_attachment=True)

@app.route('/upload_resume/<int:user_id>', methods=['POST'])
def upload_resume(user_id):
    if request.method == 'POST':
        resume = request.files['resume']
        resume_path = os.path.join('./static/uploads/resumes', resume.filename)
        resume.save(resume_path)

    db.update_resume(user_id, resume_path)
    return 'Резюме успешно загружено'

@app.route('/lkOrders')
def lkOrders():
    email = session['email']
    user_info = db.get_user_info_by_email(email)
    completed_orders = db.get_completed_orders(user_info['user_id'])

    current_orders = db.get_current_orders(user_info['user_id'])
    return render_template('lkOrders.html', completed_orders = completed_orders, user_info = user_info, stylist = user_info['stylist'], current_orders = current_orders)

####### ДОДЕЛАТЬ СОЗДАНИЕ ЧАТОВ, ОТОБРАЖЕНИЕ СУЩЕСТВУЮЩИХ ЧАТОВ, СОХРАНЕНИЕ И ОТРАВКА СООБЩЕНИЙ

@app.route('/create_chat_with_user/<int:user_id>', methods = ['GET', 'POST']) # Создание чата
def create_chat_with_user(user_id):
    if 'email' not in session:
        return redirect(url_for('start_page'))  # Если нет, отправляем на index
    
    current_user = session['email']
    user_info = db.get_user_info_by_email(current_user) # Получение инфомарци о пользователе

    if not user_info:
        flash('Ошибка авторизации')
        return redirect(url_for('start_page'))
    
    current_user_id = user_info['user_id']

    chat_between_users = db.get_chat_between_users(current_user_id, user_id) # Получении информации о чатах между пользов.
    print(f'Chat between users: {chat_between_users}')

    if not chat_between_users: # Проверка на существование чата между пользователями
        print(f'\n\n user ids \n{current_user_id} - current\t {user_id} - second user')
        db.create_chat(user_ids=[current_user_id, user_id]) # Создание чата
    else:
        print(f'\n\nChat exsists\n\n')

    return redirect(url_for('chats')) # Обновление страицы по завершении

@app.route('/chatRoom/<int:chat_id>/<int:recipient_id>')
def chat_room(chat_id, recipient_id):
    if 'email' not in session:
        return redirect(url_for('home'))

    current_user = session['email']
    user_info = db.get_user_info_by_email(current_user) # Получение инфомарци о пользователе

    if not user_info:
        flash('Ошибка авторизации')
        return redirect(url_for('home'))
    
    user_id = user_info['user_id']
    current_user_chats = db.get_user_chats(user_id) # Получение информации о чатах пользователя
    # Получение информации о получателе втрором пользователе
    recipient_info = db.get_user_chats(recipient_id)
    #chat = db.get_user_chats(user1_id= user_id, user2_id=recipient_id)
    print(f'Recipient info:\n{recipient_info}')
    if current_user_chats:
        #db.create_chat(user_ids=[user_id, recipient_id]) # Создание чата
        
        #chat = db.get_chat_between_users(user1_id= user_id, user2_id=recipient_id)

        #recipient = db.get_user_info_by_id(recipient_id)
        print(f'\nUnread messages: {db.get_unread_messages(user_id, chat_id)}\n')
        messages = db.get_chat_messages(chat_id) # Получеие сообщений чата
        print(f'Open chat\nchat_id--{chat_id}\nchat messages:\n{messages}')
        return render_template('lkClientChatRoom.html', user = current_user_chats, chat_id = chat_id,
                                recipient = recipient_info, messages = messages, username = user_info['first_name'])

    #users = db.get_users()
    return redirect(url_for('chats'))

######################## СОКЕТЫ ###################################################################
################## !!обновление последнего сообщения!! ############################
@socketio.on('send_message')
def handle_send_message(data):
    user_email = session.get('email')
    chat_id = data.get('chat_id')
    message = data.get('message')

    if not user_email or not chat_id or not message:
        emit('error', {'msg': 'Invalid data: sender, chat_id, or message missing'})
        return

    user_info = db.get_user_info_by_email(user_email)
    if not user_info:
        emit('error', {'msg': 'Sender not found in the database'})
        return

    user_id = user_info['user_id']
    user_name = user_info['first_name']
    chat_info = db.get_chats(chat_id)

    for chat in chat_info:
        if chat['user_id'] != user_id:
            second_user_id = chat['user_id']
    # Сохраняем ообщение в БД
    db.save_message(chat_id, user_id, message) # Сохранение сооб��ения в базу данных

    # Отправляем сообщение в комнату чата
    room = f"chat_{chat_id}"
    date = f'{datetime.now()}'
    unreaded_messages_chat = get_unreaded(second_user_id)
    update_unreaded(unreaded_messages_chat)
    try:
        update_last_message(message, chat_id)
    except Exception as e:
        print('ne emit')
    print(f'\nSecond user unreaded: {unreaded_messages_chat}\n')
    emit('receive_message', {'sender': user_name, 'text': message, 'timestamp': date,}, room=room)
    
@socketio.on('join_chat') # Выводит сообщение о подключении
def handle_join_chat(data):
    user_email = session.get('email')
    chat_id = data.get('chat_id')

    if not user_email or not chat_id:
        emit('error', {'msg': 'Invalid data: sender or chat_id missing'})
        return

    user_info = db.get_user_info_by_email(user_email)

    if not user_info:
        emit('error', {'msg': 'Sender not found in the database'})
        return

    user_id = db.get_user_info_by_email(user_email)['user_id']
    db.mark_chat_as_read(chat_id, user_id) # Отметка о последнем входе в чат

    room = f"chat_{chat_id}"
    join_room(room)
    emit('status', {'msg': f"{user_info['first_name']} joined the chat."}, room=room)

@socketio.on('leave_chat') # Выводит сообщение о выходе пользователя поменять но обновление времени просмотра?
def handle_leave_chat(data):
    print('leave_chat')
    user_email = session.get('email')
    chat_id = data.get('chat_id')

    if not user_email or not chat_id:
        emit('error', {'msg': 'Invalid data: sender or chat_id missing'})
        return

    user_info = db.get_user_info_by_email(user_email)
    if not user_info:
        emit('error', {'msg': 'Sender not found in the database'})
        return

    user_id = db.get_user_info_by_email(user_email)['user_id']
    db.mark_chat_as_read(chat_id, user_id) # Отметка о последнем входе в чат

    room = f"chat_{chat_id}"
    leave_room(room)
    emit('status', {'msg': f"{user_info['first_name']} left the chat."}, room=room)

def update_unreaded(unreaded_messages_chat):
     # Обновление количества непрочитанных сообщений
    socketio.emit('update_unreaded', { 'unreaded': unreaded_messages_chat })

def update_last_message(message, chat_id):
     # Обновление количества последнего сообщения
    socketio.emit('last_message', { 'last_message': message, 'chat_id': chat_id })

def get_unreaded(userID):
    print('\nGets ureaded')
    user_unread_messages = db.get_user_unread_messages(userID) # Получение всех непрочитанных сообщений пользователя
    print(f'\nUnread messsages: {user_unread_messages}')

    unreaded_messages_chat = {} # Словарь непрочитанных сообщений
    number_unreaded_messsages = 0

    for message in user_unread_messages:
        if message['message'] != None:
            number_unreaded_messsages += 1
            unreaded_messages_chat = {'chat_id': message['chat_id'], 'unreaded': number_unreaded_messsages}
    
    return unreaded_messages_chat

################# АНКЕТА ########################################### АНКЕТА ###################################
########################################### АНКЕТА ############################################################

@app.route('/anket-gender', methods = ['POST', 'GET']) # выбор пола для анкеты
def anket_gender():
    # if 'email' not in session:
    #     return redirect(url_for('start_page'))
    print(session)
    if 'email' in session:
        email = session['email']
    else:
        pass

    if request.method == 'POST':
        gender = request.form.get('gender')
        print(gender)
        if gender == 'male':
            gender = 1
        elif gender == 'female':
            gender = 0
        print(f'email {email}\ngender {gender}')
        anketa[email]= {'gender': gender}
        return redirect(url_for('anket_purpose'))
    
    return render_template('gender.html') # after that target woman

@app.route('/anket-purpose', methods = ['POST', 'GET']) # первая страниц анкеты(цели)
def anket_purpose():
    email = session['email']
    print(email)
    user_gender = get_gender(email)
    print(f'\n\npurpose {user_gender}\n\n')
    if request.method == 'POST': # запись выбранных ответов
        action = request.form.get('action')
        print(f'action {action}')
        everyday1 = request.form.get('everyday1')
        everyday2 = request.form.get('everyday2')
        everyday3 = request.form.get('everyday3')
        everyday4 = request.form.get('everyday4')
        everyday5 = request.form.get('everyday5')
        everyday6 = request.form.get('everyday6')

        everyday_section = {'1': everyday1, '2': everyday2, '3': everyday3,
                            '4': everyday4, '5': everyday5, '6': everyday6}

        home1 = request.form.get('home1')
        home2 = request.form.get('home2')
        home3 = request.form.get('home3')
        home4 = request.form.get('home4')
        home5 = request.form.get('home5')
        home6 = request.form.get('home6')
        
        home_section = {'1': home1, '2': home2, '3': home3,
                            '4': home4, '5': home5, '6': home6}

        anketa[email]['purpose'] = {'everyday': everyday_section, 'home': home_section}
        print(f'\n\n{anketa}\n\n')

        if action == 'next':
            return redirect(url_for('anket_style'))
        elif action == 'prev':
            return redirect(url_for('anket_gender'))

    if user_gender == 0:
        return render_template('targetWoman.html')
    else:
        return render_template('man')

@app.route('/anket-style', methods = ['POST', 'GET']) # выбор стиля 2
def anket_style():
    email = session['email']

    if request.method == 'POST':
        action = request.form.get('action')
        style = request.form.getlist('style') # исправить
        anketa[email]['style'] = style

        if action == 'next':
                return redirect(url_for('confirmStyle'))
        elif action == 'prev':
                return redirect(url_for('anket_purpose'))
    return render_template('/chooseStyle.html')

@app.route('/anket-confirmStyle', methods = ['POST', 'GET']) # выбор стиля 4
def confirmStyle():
    email = session['email']
    
    if request.method == 'POST':   
        action = request.form.get('action')
        answer = request.form.getlist('style_choice') # исправить
        anketa[email]['style_choice'] = answer

        if action == 'next':
                return redirect(url_for('season'))
        elif action == 'prev':
                return redirect(url_for('anket_style'))
    return render_template('confirmStyle.html')

@app.route('/season', methods = ['POST', 'GET']) # сезон 5
def season(): # исправить под два пола
    email = session['email']
    if request.method == 'POST':
        action = request.form.get('action')
        season = request.form.get('season')
        anketa[email]['season'] = season
        if action == 'next':
                return redirect(url_for('anket_chooseWork'))
        elif action == 'prev':
                return redirect(url_for('confirmStyle'))
    return render_template('season.html')

@app.route('/anket-chooseWork', methods=['POST', 'GET'])  # 17
def anket_chooseWork():
    email = session['email']
    if request.method == 'POST':
        action = request.form.get('action')
        selected_professions = request.form.getlist('professions')
        anketa[email]['work'] = selected_professions
        
        if action == 'next':
            return redirect(url_for('anket_chooseHairColor'))
        elif action == 'prev':
            return redirect(url_for('season'))
    return render_template('chooseWork.html')

@app.route('/anket-chooseHairColor', methods=['POST', 'GET'])  # 18
def anket_chooseHairColor():
    email = session['email']
    if request.method == 'POST':
        action = request.form.get('action')
        selected_hair_color = request.form.getlist('hair_color')
        anketa[email]['hair_color'] = selected_hair_color
        
        if action == 'next':
            return redirect(url_for('anket_chooseSizeTopWoman'))
        elif action == 'prev':
            return redirect(url_for('anket_chooseWork'))
    return render_template('chooseHairColor.html')

@app.route('/anket-chooseSizeTopWoman', methods=['POST', 'GET'])  # 19
def anket_chooseSizeTopWoman():
    email = session['email']
    if request.method == 'POST':
        action = request.form.get('action')
        selected_size_top = request.form.getlist('size')
        anketa[email]['size_top'] = selected_size_top
        
        if action == 'next':
            return redirect(url_for('anket_chooseSizeBottomWoman'))
        elif action == 'prev':
            return redirect(url_for('anket_chooseHairColor'))
    return render_template('chooseSizeTopWoman.html')

@app.route('/anket-chooseSizeBottomWoman', methods=['POST', 'GET'])  # 20
def anket_chooseSizeBottomWoman():
    email = session['email']
    if request.method == 'POST':
        action = request.form.get('action')
        selected_size_bottom = request.form.getlist('size')
        anketa[email]['size_bottom'] = selected_size_bottom
        
        if action == 'next':
            return redirect(url_for('anket_chooseKabluck'))
        elif action == 'prev':
            return redirect(url_for('anket_chooseSizeTopWoman'))
    return render_template('chooseSizeBottomWoman.html')

@app.route('/anket-chooseKabluck', methods=['POST', 'GET'])  # 21
def anket_chooseKabluck():
    email = session['email']
    if request.method == 'POST':
        action = request.form.get('action')
        selected_kabluck = request.form.getlist('kabluck')
        anketa[email]['kabluck'] = selected_kabluck
        
        if action == 'next':
            return redirect(url_for('anket_chooseSkinnyOrNotTop'))
        elif action == 'prev':
            return redirect(url_for('anket_chooseSizeBottomWoman'))
    return render_template('chooseKabluck.html')

@app.route('/anket-chooseSkinnyOrNotTop', methods=['POST', 'GET'])  # 22
def anket_chooseSkinnyOrNotTop():
    email = session['email']
    if request.method == 'POST':
        action = request.form.get('action')
        selected_skinny_or_not_top = request.form.getlist('skinny_or_not_top')
        anketa[email]['skinny_or_not_top'] = selected_skinny_or_not_top
        
        if action == 'next':
            return redirect(url_for('anket_chooseSkinnyOrNotBottom'))
        elif action == 'prev':
            return redirect(url_for('anket_chooseKabluck'))
    return render_template('chooseSkinnyOrNotTop.html')

@app.route('/anket-chooseSkinnyOrNotBottom', methods=['POST', 'GET'])  # 23
def anket_chooseSkinnyOrNotBottom():
    email = session['email']
    if request.method == 'POST':
        action = request.form.get('action')
        selected_skinny_or_not_bottom = request.form.getlist('skinny_or_not_bottom')
        anketa[email]['skinny_or_not_bottom'] = selected_skinny_or_not_bottom
        
        if action == 'next':
            return redirect(url_for('anket_chooseJeansForm'))  # Предполагаю, что следующая страница skin1
        elif action == 'prev':
            return redirect(url_for('anket_chooseSkinnyOrNotTop'))
    return render_template('chooseSkinnyOrNotBottom.html')

@app.route('/anket-chooseJeansForm', methods=['POST', 'GET'])  # 24
def anket_chooseJeansForm():
    email = session['email']
    user_gender = get_gender(email)
    
    if request.method == 'POST':
        action = request.form.get('action')
        selected_jeans = request.form.get('selectedJeans')

        if selected_jeans:
            anketa[email]['jeans_type'] = selected_jeans
            
        if action == 'next':
            return redirect(url_for('anket_choosePosadka'))
        elif action == 'prev':
            return redirect(url_for('anket_chooseSkinnyOrNotBottom'))
            
    if user_gender == 0:
        return render_template('chooseJeansForm.html')
    else:
        return render_template('chooseJeansFormMan.html')

@app.route('/anket-choosePosadka', methods=['POST', 'GET'])  # 25
def anket_choosePosadka():
    email = session['email']
    user_gender = get_gender(email)
    
    if request.method == 'POST':
        action = request.form.get('action')
        selected_posadka = request.form.getlist('selectedPosadka')
        print(f'selected_posadka {selected_posadka}')
        anketa[email]['posadka'] = selected_posadka
        
        if action == 'next':
            return redirect(url_for('anket_chooseJeansLength'))
        elif action == 'prev':
            return redirect(url_for('anket_chooseJeansForm'))
    return render_template('choosePosadka.html')        
    # if user_gender == 0:
    #     return render_template('choosePosadka.html')
    # else:
    #     return render_template('choosePosadkaMan.html')

@app.route('/anket-chooseJeansLength', methods=['POST', 'GET'])  # 26
def anket_chooseJeansLength():
    email = session['email']
    user_gender = get_gender(email)
    print(f'request.form')
    if request.method == 'POST':
        print(f'request.form {request.form}')
        action = request.form.get('action')
        selected_jeans_length = request.form.getlist('selectedLength')
        print(f'selected_jeans_length {selected_jeans_length}')
        anketa[email]['jeans_length'] = selected_jeans_length
        
        if action == 'next':
            return redirect(url_for('anket_chooseLength'))
        elif action == 'prev':
            return redirect(url_for('anket_choosePosadka'))
    return render_template('chooseJeansLenght.html')        
    # if user_gender == 0:
    #     return render_template('chooseJeansLength.html')
    # else:
    #     return render_template('chooseJeansLengthMan.html')

@app.route('/anket-chooseLength', methods=['POST', 'GET'])  # 27
def anket_chooseLength():
    email = session['email']
    user_gender = get_gender(email)
    
    if request.method == 'POST':
        action = request.form.get('action')
        selected_length = request.form.get('selectedLength')
        
        if selected_length:
            anketa[email]['length'] = selected_length
            
        if action == 'next':
            return redirect(url_for('skin1'))
        elif action == 'prev':
            return redirect(url_for('anket_chooseJeansLength'))
            
    if user_gender == 0:
        return render_template('chooseLenght.html')
    else:
        return render_template('chooseLengthMan.html')



@app.route('/skin1', methods = ['POST', 'GET']) # 6
def skin1():
    email = session['email']
    user_gender = get_gender(email)

    if request.method == 'POST':
        action = request.form.get('action')
        checkbox_states = {
            'like1': request.form.get('likeCheckboxState1'),
            'like2': request.form.get('likeCheckboxState2'),
            'like3': request.form.get('likeCheckboxState3'),
            'like4': request.form.get('likeCheckboxState4'),
            'like5': request.form.get('likeCheckboxState5')
        }
        
        anketa[email]['skin1_likes'] = checkbox_states
        
        if action == 'next':
            return redirect(url_for('skin2'))
        elif action == 'prev':
            return redirect(url_for('anket_chooseLength'))

    if user_gender == 0:
        return render_template('skin1.html')
    else:
        return render_template('skin1man.html')

@app.route('/skin2', methods = ['POST', 'GET']) # 7
def skin2():
    email = session['email']
    user_gender = get_gender(email)
    
    if request.method == 'POST':
        action = request.form.get('action')
        checkbox_states = {
            'like1': request.form.get('likeCheckboxState1'),
            'like2': request.form.get('likeCheckboxState2'),
            'like3': request.form.get('likeCheckboxState3'),
            'like4': request.form.get('likeCheckboxState4'),
            'like5': request.form.get('likeCheckboxState5')
        }
        
        anketa[email]['skin2_likes'] = checkbox_states
        
        if action == 'next':
            return redirect(url_for('skin3'))
        elif action == 'prev':
            return redirect(url_for('skin1'))

    if user_gender == 0:
        return render_template('skin2.html')
    else:
        return render_template('skin2man.html')

@app.route('/skin3', methods = ['POST', 'GET']) # 8
def skin3():
    email = session['email']
    user_gender = get_gender(email)

    if request.method == 'POST':
        action = request.form.get('action')
        checkbox_states = {
            'like1': request.form.get('likeCheckboxState1'),
            'like2': request.form.get('likeCheckboxState2'),
            'like3': request.form.get('likeCheckboxState3'),
            'like4': request.form.get('likeCheckboxState4'),
            'like5': request.form.get('likeCheckboxState5')
        }
        
        anketa[email]['skin3_likes'] = checkbox_states
        
        if action == 'next':
            return redirect(url_for('skin4'))
        elif action == 'prev':
            return redirect(url_for('skin2'))

    if user_gender == 0:
        return render_template('skin3.html')
    else:
        return render_template('skin3man.html')
    
@app.route('/skin4', methods = ['POST', 'GET'])
def skin4():
    email = session['email']
    user_gender = get_gender(email)

    if request.method == 'POST':
        action = request.form.get('action')
        checkbox_states = {
            'like1': request.form.get('likeCheckboxState1'),
            'like2': request.form.get('likeCheckboxState2'),
            'like3': request.form.get('likeCheckboxState3'),
            'like4': request.form.get('likeCheckboxState4'),
            'like5': request.form.get('likeCheckboxState5')
        }
        
        anketa[email]['skin4_likes'] = checkbox_states
        
        if action == 'next':
            return redirect(url_for('skin5'))
        elif action == 'prev':
            return redirect(url_for('skin3'))

    if user_gender == 0:
        return render_template('skin4.html')
    else:
        return render_template('skin4man.html')

@app.route('/skin5', methods = ['POST', 'GET'])
def skin5():
    email = session['email']
    user_gender = get_gender(email)

    if request.method == 'POST':
        action = request.form.get('action')
        checkbox_states = {
            'like1': request.form.get('likeCheckboxState1'),
            'like2': request.form.get('likeCheckboxState2'),
            'like3': request.form.get('likeCheckboxState3'),
            'like4': request.form.get('likeCheckboxState4'),
            'like5': request.form.get('likeCheckboxState5')
        }
        
        anketa[email]['skin5_likes'] = checkbox_states
        
        if action == 'next':
            return redirect(url_for('skin6'))
        elif action == 'prev':
            return redirect(url_for('skin4'))

    if user_gender == 0:
        return render_template('skin5.html')
    else:
        return render_template('skin5man.html')

@app.route('/skin6', methods = ['POST', 'GET'])
def skin6():
    email = session['email']
    user_gender = get_gender(email)

    if request.method == 'POST':
        action = request.form.get('action')
        checkbox_states = {
            'like1': request.form.get('likeCheckboxState1'),
            'like2': request.form.get('likeCheckboxState2'),
            'like3': request.form.get('likeCheckboxState3'),
            'like4': request.form.get('likeCheckboxState4'),
            'like5': request.form.get('likeCheckboxState5')
        }
        
        anketa[email]['skin6_likes'] = checkbox_states
        
        if action == 'next':
            return redirect(url_for('skin7'))
        elif action == 'prev':
            return redirect(url_for('skin5'))

    if user_gender == 0:
        return render_template('skin6.html')
    else:
        return render_template('skin6man.html')
    
@app.route('/skin7', methods = ['POST', 'GET'])
def skin7():
    email = session['email']
    user_gender = get_gender(email)

    if request.method == 'POST':
        action = request.form.get('action')
        checkbox_states = {
            'like1': request.form.get('likeCheckboxState1'),
            'like2': request.form.get('likeCheckboxState2'),
            'like3': request.form.get('likeCheckboxState3'),
            'like4': request.form.get('likeCheckboxState4'),
            'like5': request.form.get('likeCheckboxState5')
        }
        
        anketa[email]['skin7_likes'] = checkbox_states
        
        if action == 'next':
            return redirect(url_for('skin8'))
        elif action == 'prev':
            return redirect(url_for('skin6'))

    if user_gender == 0:
        return render_template('skin7.html')
    else:
        return render_template('skin7man.html')
    
@app.route('/skin8', methods = ['POST', 'GET'])
def skin8():
    email = session['email']
    user_gender = get_gender(email)

    if request.method == 'POST':
        action = request.form.get('action')
        checkbox_states = {
            'like1': request.form.get('likeCheckboxState1'),
            'like2': request.form.get('likeCheckboxState2'),
            'like3': request.form.get('likeCheckboxState3'),
            'like4': request.form.get('likeCheckboxState4'),
            'like5': request.form.get('likeCheckboxState5')
        }
        
        anketa[email]['skin8_likes'] = checkbox_states
        
        if action == 'next':
            return redirect(url_for('skin9'))
        elif action == 'prev':
            return redirect(url_for('skin7'))

    if user_gender == 0:
        return render_template('skin8.html')
    else:
        return render_template('skin8man.html')
    
@app.route('/skin9', methods = ['POST', 'GET'])
def skin9():
    email = session['email']
    user_gender = get_gender(email)

    if request.method == 'POST':
        action = request.form.get('action')
        checkbox_states = {
            'like1': request.form.get('likeCheckboxState1'),
            'like2': request.form.get('likeCheckboxState2'),
            'like3': request.form.get('likeCheckboxState3'),
            'like4': request.form.get('likeCheckboxState4'),
            'like5': request.form.get('likeCheckboxState5')
        }
        
        anketa[email]['skin9_likes'] = checkbox_states
        
        if action == 'next':
            return redirect(url_for('skin10'))
        elif action == 'prev':
            return redirect(url_for('skin8'))

    if user_gender == 0:
        return render_template('skin9.html')
    else:
        return render_template('skin9man.html')
    
@app.route('/skin10', methods = ['POST', 'GET'])
def skin10():
    email = session['email']
    user_gender = get_gender(email)

    if request.method == 'POST':
        action = request.form.get('action')
        checkbox_states = {
            'like1': request.form.get('likeCheckboxState1'),
            'like2': request.form.get('likeCheckboxState2'),
            'like3': request.form.get('likeCheckboxState3'),
            'like4': request.form.get('likeCheckboxState4'),
            'like5': request.form.get('likeCheckboxState5')
        }
        
        anketa[email]['skin10_likes'] = checkbox_states
        
        if action == 'next':
            return redirect(url_for('createOrder'))  # Следующая страница после skin10
        elif action == 'prev':
            return redirect(url_for('skin9'))

    if user_gender == 0:
        return render_template('skin10.html')
    else:
        return render_template('skin10man.html')

@app.route('/createOrder', methods=['POST', 'GET'])
def createOrder():
    email = session['email']
    user_id = db.get_user_info_by_email(email)['user_id']
    if request.method == 'POST':
        price_range = request.form.getlist('price_range')
        print(f'price_range {price_range}')
        anketa[email]['price_range'] = price_range
        print(f'anketa {anketa}')
        print(f'anketa {anketa[email]}')
        db.save_user_anketa(user_id=user_id, anketa=anketa[email])
        return redirect(url_for('lkCL'))
    return render_template('createOrder.html')

@app.route('/wrkEDC') # выбор стиля 3
def wrkEDC():
    return render_template('workOrEducation.html')

##################################################################################################
####################################### ЛЕНДИНГИ #################################################

@app.route('/stylistam')
def stylistam():
    return render_template('stilistam.html')

@app.route('/capsula')
def capsula():
    return render_template('capsula.html')

@app.route('/users')
def users():
    return db.get_users()

@app.route('/stylists')
def stylists():
    return db.get_stylists()

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('email', None)
    return redirect(url_for('start_page'))

def get_gender(email):
    user_gender = anketa.get(email)
    print(f'full {user_gender}')
    print(user_gender['gender'])
    return user_gender['gender']

@app.route('/anketi')
def anketi():
    return db.get_anketi()

@app.route('/skins')
def skins():
    return db.get_skins()

if __name__ == '__main__':
    socketio.run(app, debug=True)
