import os

from flask_paginate import (
    Pagination,
    get_page_parameter
)

import io

from datetime import date

from flask import (
    Flask,
    render_template,
    flash,
    request,
    redirect,
    url_for,
    session,
    send_file
)
from flask_login import login_required, current_user

import markdown

import bleach
from hash import get_md5

UPLOAD_FOLDER = "./static/covers" #переменная, которая определяет путь к директории, в которую будут загружаться файлы
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'} # множество (set), которое содержит допустимые расширения файлов, которые могут быть загружены в приложение

app = Flask(__name__)
app.config.from_pyfile("config.py") #Загрузка конфигурации приложения из  config.py
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER # Переменная, которая была определена ранее в коде и указывает на путь к каталогу, куда будут загружаться файлы

from database import Database #импортируем класс Database из модуля database
db = Database(app) #Здесь создается экземпляр класса Database, и он передается экземпляру приложения Flask (app)

from auth import bp as bp_auth, init_login_manager, checkRole #Импорт элементов из модуля auth
app.register_blueprint(bp_auth) #регистрируем ранее импортированный Blueprint (bp_auth)
init_login_manager(app) #инициализирует менеджер аутентификации Flask-Login, передавая ему экземпляр приложения app

#Жанры из таблицы genres
def get_genres(): #Функция не принимает аргументов и предназначена для извлечения данных о жанрах из базы данных
    try:
        with db.connect().cursor(named_tuple=True) as cursor: #Установление соединения с базой данных
                query = ("SELECT * FROM genres") #создается SQL-запрос для получения всех записей из таблицы genres
                cursor.execute(query) #Этот метод выполняет указанный SQL-запрос. В данном случае он извлекает все записи из таблицы жанров
                genres = cursor.fetchall() # fetchall() извлекает все строки результата запроса и сохраняет их в переменной genres
                return genres # fetchall() извлекает все строки результата запроса и сохраняет их в переменной genres
    except Exception as err: #Обработка ошибок
        print(f"ERROR GET_GENRES: {err}") #Если возникает ошибка, выводится сообщение об ошибке, включая текст самой ошибки

def get_books(): #функция get_books, которая не принимает аргументов и предназначена для извлечения данных о книгах из базы данных
    try:
        with db.connect().cursor(named_tuple=True) as cursor: #Установление соединения с базой данных
                query = ("SELECT * FROM books") #Создает SQL-запрос для получения всех записей из таблицы books
                cursor.execute(query) #Выполняет указанный SQL-запрос, который извлекает все строки из таблицы books
                books = cursor.fetchall() # все строки результата запроса и сохраняет их в переменной books
                return books #Возвращает полученные данные о книгах из функции. Если запрос выполнен успешно, это будет список всех книг
    except Exception as err: #Ошибки
        print(f"ERROR GET_BOOKS: {err}") # Если возникает ошибка, выводится сообщение об ошибке, включая текст самой ошибки

def get_book(book_id): #функция get_book, которая принимает один аргумент — book_id. Этот идентификатор используется для поиска конкретной книги в базе данных
    try:
        with db.connect().cursor(named_tuple=True) as cursor: #Установление соединения с базой данных
                query = ("SELECT * FROM books WHERE book_id=%s") #Создает SQL-запрос для получения всех полей из таблицы books, где book_id соответствует переданному значению
                                                                #%s это параметр, который будет заменен на значение переменной book_id во время выполнения запроса
                cursor.execute(query, (book_id,)) #Выполняет указанный SQL-запрос, подставляя значение book_id в параметр %s.
                book = cursor.fetchone() #извлекаем  результат запроса и сохраняем её в переменную book
                return book #Возвращает полученные данные о книге из функции. Если книга найдена, это будет именованный кортеж с данными; если нет — None.
    except Exception as err: #обрабатывает любые исключения, которые могут возникнуть в блоке try. Переменная err будет содержать информацию об ошибке.
        print(f"ERROR GET_BOOK: {err}") #выводится сообщение об ошибке с указанием причины.
        return None #Если произошла ошибка, функция возвращает None, что сигнализирует о том, что данные не были успешно получены

def get_book_name(book_id): #Используется для поиска конкретной книги в базе данных
    try:
        with db.connect().cursor(named_tuple=True) as cursor:
                query = ("SELECT book_name FROM books WHERE book_id=%s") #Создает SQL-запрос для получения названия книги из таблицы books, где book_id соответствует переданному значению
                cursor.execute(query, (book_id,))# Выполняет указанный SQL-запрос
                book_name = cursor.fetchone().book_name #извлекает результат запроса и сохраняет её в переменной book_name
                return book_name #Возвращает полученное название книги из функции
    except Exception as err:# Ошибки
        print(f"ERROR GET_BOOK_NAME: {err}") #выводится сообщение об ошибке с указанием причины
        return None #Если произошла ошибка, функция возвращает None, что сигнализирует о том, что данные не были успешно получены

#Обложка
def get_cover(cover_id):  #Получает название обложки книги по идентификатору cover_id
    try:
        with db.connect().cursor(named_tuple=True) as cursor: #Устанавливаем соединение с базой данных
                query = ("SELECT cover_name FROM covers WHERE cover_id=%s") #Определяем SQL-запрос для получения названия обложки по ее идентификатору
                cursor.execute(query, (cover_id,)) #Выполняем запрос, передавая cover_id как параметр
                cover = cursor.fetchone() #Извлекаем  строку результата запроса
                return cover.cover_name #Возвращаем название обложки
    except Exception as err: 
        print(f"ERROR GET_COVER: {err}") #Обрабатываем исключения и выводим сообщение об ошибке

#Жанры книги из таблицы books_to_genres
def get_book_genres(book_id):
    try:
        with db.connect().cursor(named_tuple=True) as cursor:#
                query = ("SELECT genre_id FROM books_to_genres WHERE book_id=%s") #Определяем SQL-запрос для получения идентификаторов жанров
                cursor.execute(query, (book_id,)) #Выполняем запрос, передавая book_id как параметр
                genres_ids = cursor.fetchall() #Извлекаем все идентификаторы жанров, связанные с книгой
                
                list_of_genres = [] #Инициализируем список для хранения названий жанров
                for genre_id in genres_ids: #Проходим по всем идентификаторам жанров
                    query = ("SELECT genre_name FROM genres WHERE genre_id=%s") #Определяем SQL-запрос для получения названия жанра по его идентификатору
                    cursor.execute(query, (genre_id.genre_id,)) #Выполняем запрос, передавая genre_id как параметр
                    genre = cursor.fetchone().genre_name #Извлекаем название жанра
                    list_of_genres.append(genre) #Добавляем название жанра в список
                genres = ', '.join(list_of_genres) #Объединяем все названия жанров в одну строку, разделенную запятыми
                return genres #Возвращаем строку с названиями жанров
    except Exception as err:
        print(f"ERROR GET_BOOK_GENRES: {err}") #Обрабатываем исключения и выводим сообщение об ошибке

#Проверка допустимости расширения файла
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Сохранение файла
def save_file(file, filename):
    try:
        file.stream.seek(0) #Перемещаем указатель потока файла в начало
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename)) #Сохраняем файл в указанной папке с заданным именем
        return True #Возвращаем True, если файл успешно сохранен
    except Exception as err: 
        print(f"ERROR SAVE_FILE: {err}") #Обрабатываем исключения и выводим сообщение об ошибке
        return False #Возвращаем False в случае ошибки

#Удаление файла
def delete_file(filename):
    try:
        path_file = os.path.join(app.config["UPLOAD_FOLDER"], filename) #Определяем полный путь к файлу, который нужно удалить
        os.remove(path_file) # Удаляем файл по указанному пути
        return True #Возвращаем True, если файл успешно удален
    except Exception:
        return False #Если происходит ошибка, возвращаем False

def get_review(user_id, book_id):
    try:
        with db.connect().cursor(named_tuple=True) as cursor:
            query = ("SELECT * FROM reviews WHERE review_user=%s AND review_book=%s")
            cursor.execute(query, (user_id, book_id))
            review = cursor.fetchone()
            return review
    except Exception as err:
            print(f"GET_REVIEW: {err}")
            return False

#Отзывы пользователей
def get_reviews(book_id):
    try:
        with db.connect().cursor(named_tuple=True) as cursor: #Устанавливаем соединение с базой данных
                query = ("SELECT * FROM reviews WHERE review_book=%s") #Определяем SQL-запрос для получения отзыва по идентификаторам пользователя и книги
                cursor.execute(query, (book_id,)) #Выполняем запрос, передавая user_id и book_id как параметры
                reviews = cursor.fetchall() # Извлекаем отзыв
                return reviews # Возвращаем объект отзыва (или None, если отзыв не найден)
    except Exception as err: 
        print(f"ERROR GET_REVIEWS: {err}") #Обрабатываем исключения и выводим сообщение об ошибке
        return False #Возвращаем False в случае ошибки

#Извлекаем логин пользователя
def get_login(user_id): # получаем логин пользователя по его идентификатору
    try:
        with db.connect().cursor(named_tuple=True) as cursor: 
            query = ("SELECT user_login FROM users WHERE user_id=%s") #Определяем SQL-запрос для получения логина пользователя по его идентификатору
            cursor.execute(query, (user_id,)) # Выполняем запрос, передавая user_id как параметр
            login = cursor.fetchone() #Извлекаем логин
            return login.user_login # Возвращаем логин пользователя (или None, если логин не найден)
    except Exception as err:
            print(f"GET_LOGIN: {err}") #Обрабатываем исключения и выводим сообщение об ошибке
            return False #Возвращаем False в случае ошибки

#Возвращаем количество отзывов для книги
def get_reviews_amount(book_id):
    if get_reviews(book_id): #Проверяем, есть ли отзывы для данной книги
        return len(get_reviews(book_id)) #Если отзывы есть, возвращаем их количество
    return 0 #Если отзывов нет, возвращаем 0

#Вычисляем средний рейтинг книги
def get_rating(book_id):
    try:
        with db.connect().cursor(named_tuple=True) as cursor:
                query = ("SELECT review_rating FROM reviews WHERE review_book=%s") #Определяем SQL-запрос для получения рейтингов отзывов для указанной
                cursor.execute(query, (book_id,)) #Выполняем запрос, передавая book_id как параметр
                ratings = cursor.fetchall() #Извлекаем все рейтинги отзывов
                
                if get_reviews_amount(book_id) != 0: #Проверяем, есть ли отзывы для книги
                    score = 0 #Инициализируем переменную для суммы рейтингов
                    for rate in ratings: #Суммируем все рейтинги
                        score += rate.review_rating
                    return round(score / get_reviews_amount(book_id), 1) #Возвращаем средний рейтинг, округленный до одного знака после запятой
    except Exception as err: #
        print(f"ERROR GET_RATING: {err}") #Обрабатываем исключения и выводим сообщение об ошибке
    return '-' #Возвращаем '-' в случае ошибки или отсутствия отзывов

#Статистика посещений
def set_visit(book_id):
    try:
        with db.connect().cursor(named_tuple=True) as cursor: # Устанавливаем соединение с базой данных и создаем курсор для выполнения запроса
            if current_user.is_authenticated: #Проверяем, аутентифицирован ли текущий пользователь
                user_id = current_user.id #Получаем идентификатор текущего пользователя

                query = ("INSERT INTO statistics(statistic_user, statistic_book) VALUES (%s, %s)") #SQL-запрос для записи статистики с указанием пользователя и книги
                cursor.execute(query, (user_id, book_id)) #Выполняем запрос с параметрами
            else:
                query = ("INSERT INTO statistics(statistic_book) VALUES (%s)") #SQL-запрос для записи статистики без указания пользователя
                cursor.execute(query, (book_id,)) #Выполняем запрос с параметром
            db.connect().commit() #Фиксируем изменения в базе данных
    except Exception as err:
        db.connect().rollback() #В случае ошибки откатываем изменения
        print(f"ERROR SET_VISIT: {err}") #Выводим сообщение об ошибке
    return '' #Возвращаем пустую строку

#Фио
def get_fio(user_id):
    try:
        with db.connect().cursor(named_tuple=True) as cursor:#Устанавливаем соединение с базой данных и создаем курсор для выполнения запроса
            query = ("SELECT * FROM users WHERE user_id=%s") #SQL-запрос для получения всех данных о пользователе по его идентификатору
            cursor.execute(query, (user_id,)) # Выполняем запрос, передавая user_id как параметр
            user = cursor.fetchone() #Извлекаем запись о пользователе
            fio = user.user_surname + ' ' + user.user_name + ' ' + user.user_patronym #Формируем полное имя пользователя, объединяя фамилию, имя и отчество
            return fio #Возвращаем полное имя
    except Exception as err:
            print(f"GET_FIO: {err}") #Выводим сообщение об ошибке 
            return "Неаутентифицированный пользователь" #Возвращаем сообщение об ошибке

#экспортирует данные статистики в формате CSV,
@app.route("/export_csv")
def export_csv():
    with db.connect().cursor(named_tuple=True) as cursor:
        query = ('SELECT * FROM statistics') #SQL-запрос для получения всех записей из таблицы статистики
        cursor.execute(query) #Выполняем запрос
        statistics=cursor.fetchall() #Извлекаем все записи статистики

        statistic=[] #Создаем список для хранения отформатированных записей статистики
        for i in statistics:
            string = {"id": i.statistic_id, "ФИО": get_fio(i.statistic_user), "Название книги": get_book_name(i.statistic_book), "Время посещения": i.statistic_created_at} #Формируем словарь для каждой записи статистики
            statistic.append(string) #Добавляем словарь в список статистики

        print(statistic) #Выводим список статистики для отладки
        data = load_data(statistic, ["id", "ФИО", "Название книги", "Время посещения"]) #Загружаем данные в формате, подходящем для CSV, с указанными заголовками
        download_name = "Статистика_" + str(date.today()) + ".csv" #Определяем имя файла для загрузки с текущей датой
        return send_file(data, as_attachment=True, download_name=download_name) #Отправляем файл CSV клиенту как вложение

#    Формирует данные в формате CSV из предоставленных записей и полей
def load_data(records, fields):
    csv_data=", ".join(fields)+"\n" #Создаем заголовок CSV, соединяя названия полей через запятую, и добавляем новую строку
    for record in records: #Обрабатываем каждую запись для формирования строк CSV
        csv_data += ", ".join([str(record[field]) for field in fields]) + "\n" # Соединяем значения полей текущей записи, преобразуя их в строки
    print(csv_data) #Выводим сформированные данные CSV в консоль для отладки
    f = io.BytesIO() #Создаем объект BytesIO для хранения данных в памяти
    f.write(csv_data.encode("utf-8")) #Записываем сформированные данные CSV в объект BytesIO в кодировке UTF-8
    f.seek(0) #Устанавливаем курсор в начале объекта BytesIO
    return f #Возвращаем объект BytesIO с данными CSV


@app.route("/statistics")
@login_required #Проверка, что пользователь авторизован
@checkRole('create') #Проверка роли пользователя, чтобы убедиться, что у него есть право на доступ к этой функции
def statistics(): #Обрабатывает запрос на получение статистики и отображает её на странице
    try:
        with db.connect().cursor(named_tuple=True) as cursor: 
            query = ("SELECT * FROM statistics") #SQL-запрос для получения всех записей из таблицы статистики
            cursor.execute(query) #Выполняем запрос
            statistics = cursor.fetchall() #Извлекаем все записи статистики
    except Exception: 
        print(f"STATISTICS ERROR: {Exception}") #Логируем ошибку, если возникла проблема с получением данных
    
    search = False #Переменная для отслеживания, производился ли поиск
    q = request.args.get('q') #Получаем параметр поиска из URL
    if q:
        search = True #Если параметр поиска присутствует, устанавливаем search в True
  
    page = request.args.get(get_page_parameter(), type=int, default=1) #Получаем текущую страницу из параметров запроса
    
    per_page = 10 #Количество записей на одной странице
    offset = (page - 1) * per_page #Рассчитываем смещение для выборки записей
    if statistics != None: #Проверяем, были ли получены данные
        # Извлекаем записи для текущей страницы
        statistics_for_render = statistics[offset:offset + per_page] #
        total = len(statistics) #Общее количество записей статистики
    else:
        statistics_for_render = '' #Если данных нет, устанавливаем пустую строку
        total = 0 #Общее количество записей равно 0

    pagination = Pagination(page=page, total=total, search=search, record_name='statistics', per_page=per_page, offset=offset) #Создаем объект пагинации для навигации по страницам

    return render_template("statistics.html", pagination=pagination, statistics=statistics_for_render, get_fio=get_fio, get_book_name=get_book_name) #Отправляем данные на шаблон для рендеринга

#функции index, которая обрабатывает запросы на главную страницу приложения
@app.route("/") #Декоратор, который связывает URL-адрес главной страницы с этой функцией
def index(): #Обрабатывает запрос на главную страницу приложения и отображает список книг
    search = False #Флаг для отслеживания, производился ли поиск
    q = request.args.get('q') #Получаем параметр поиска из URL
    if q:
        search = True #Если параметр поиска присутствует, устанавливаем search в True

    page = request.args.get(get_page_parameter(), type=int, default=1) #Получаем текущую страницу из параметров запроса
    
    per_page = 10 #Количество книг на одной странице
    offset = (page - 1) * per_page #Рассчитываем смещение для выборки книг
    books = get_books() #Получаем список всех книг из базы данных
    if books != None: #Проверяем, были ли получены книги
        books_for_render = books[offset:offset + per_page] # Извлекаем книги для текущей страницы
        total = len(books) #Общее количество книг
    else:
        books_for_render = '' #Если книг нет, устанавливаем пустую строку
        total = 0 #Общее количество книг равно 0

    pagination = Pagination(page=page, total=total, search=search, record_name='books', per_page=per_page, offset=offset) #Создаем объект пагинации для навигации по страницам
    return render_template("index.html", books=books_for_render, get_cover=get_cover, get_book_genres=get_book_genres, delete_book=delete_book, pagination=pagination, get_reviews_amount=get_reviews_amount, get_rating=get_rating)
    # Отправляем данные на шаблон для рендеринга
 
 #Обрабатование запросов на страницу истории просмотров
@app.route("/history") #Декоратор, который связывает URL-адрес "/history" с  функцией
def history(): #Обрабатывает запрос на страницу истории просмотров книг
    books = [] #Инициализируем список для хранения книг из истории просмотров
    for book_id in session["history"]: #Проходим по идентификаторам книг в истории, хранящейся в сессии
        books.append(get_book(book_id)) #Получаем информацию о каждой книге по ее идентификатору и добавляем в список
    books = books[::-1] #Переворачиваем список книг, чтобы последние просмотренные книги были первыми
    return render_template("history.html", books=books, get_cover=get_cover, get_book_genres=get_book_genres, get_reviews_amount=get_reviews_amount, get_rating=get_rating) 
    #Отправляем данные на шаблон для рендеринга

#Обработка страницы рецензии для указанной книги  
@app.route("/review/<int:book_id>", methods=["GET", "POST"])
@login_required
def review(book_id):
    if request.method == "POST": #Проверяем, если метод запроса POST (т.е. форма была отправлена)
        review_text = bleach.clean(request.form.get("review")) #Очищаем текст рецензии от небезопасного содержимого с помощью bleach
        review_rating = request.form.get("rating") #Получаем рейтинг из формы
        try: 
            if not current_user.review(book_id): #Проверяем, оставлял ли текущий пользователь рецензию на данную книгу
                raise Exception("Рецензия существует")
            
            with db.connect().cursor(named_tuple=True) as cursor: #Устанавливаем соединение с базой данных
                query = ("INSERT INTO reviews (review_book, review_user, review_rating, review_text) VALUES (%s, %s, %s, %s)") #SQL-запрос для вставки новой рецензии в таблицу reviews
                cursor.execute(query, (book_id, current_user.id, review_rating, review_text)) #Выполняем запрос, подставляя значения
                db.connect().commit() #Фиксируем изменения в базе данных
            return redirect(url_for("show_book", book_id=book_id)) #Перенаправляем пользователя на страницу книги после успешного добавления рецензии

        except Exception as err: 
            print(f"ERROR REVIEW: {err}") #Обрабатываем возможные ошибки, выводим их в консоль
            db.connect().rollback() #Откатываем изменения в случае ошибки
            flash("При сохранении данных возникла ошибка. Проверьте корректность введённых данных.", "danger") #Показываем сообщение об ошибке пользователю
    return render_template("review.html", get_review=get_review)  # Если метод запроса GET или произошла ошибка, рендерим шаблон "review.html" с функцией для получения рецензии

@app.route('/show_book/<int:book_id>') 
def show_book(book_id):
    book = get_book(book_id)
    reviews = get_reviews(book_id)
    if "history" not in session:
        session["history"] = [book_id]
    else:
        history_list = session["history"] + [book_id]
        session["history"] = history_list[-5:]

    if current_user.is_authenticated:
        user_review = get_review(current_user.id, book.book_id)
    else:
        user_review = False
    
    render_reviews = []

    for i in reviews:
        if not i == user_review:
            render_reviews.append(i)

    return render_template('show_book.html', book = book, get_cover=get_cover, get_book_genres=get_book_genres, markdown=markdown, get_login=get_login, reviews=render_reviews, user_review=user_review, set_visit=set_visit)

@app.route('/delete_book/<int:book_id>')
@login_required
@checkRole("delete")
def delete_book(book_id):
    try:
        with db.connect().cursor(named_tuple=True) as cursor:
                query = ("DELETE FROM books WHERE book_id=%s")
                cursor.execute(query, (book_id,))
                db.connect().commit()
                flash("Удаление успешно", "success")
    except Exception as err:
        flash("Ошибка при удалении книги", "danger")
        db.connect().rollback()
        print(f"ERROR DELETE_BOOK: {err}")
    return redirect(url_for("index"))

@app.route("/create_book", methods=["GET", "POST"])
@login_required
@checkRole("create")
def create_book():
    genres = get_genres()

    if request.method == "POST":
        book_name = request.form.get("name")
        book_description = bleach.clean(request.form.get("description"))
        book_year = request.form.get("year")
        book_publisher = request.form.get("publisher")
        book_author = request.form.get("author")
        book_size = request.form.get("size")
        cover = request.files.get("cover")
        book_genres = request.form.getlist("genres")

        cover_data = cover.read()
        cover_MD5_hash = get_md5(cover_data)
        cover_name = cover_MD5_hash + '.' + cover.filename.rsplit('.', 1)[1].lower()
        cover_mime_type = cover.mimetype

        try:
            if not allowed_file(cover.filename):
                raise Exception("Файл недопустимого расширения")

            with db.connect().cursor(named_tuple=True) as cursor:
                #Проверка на наличие обложки в БД
                query = ("SELECT cover_id FROM covers WHERE cover_MD5_hash=%s")
                cursor.execute(query, (cover_MD5_hash,))
                cover_id = cursor.fetchone()

                if cover_id == None:
                    query = ("INSERT INTO covers (cover_name, cover_mime_type, cover_MD5_hash) VALUES (%s, %s, %s)")
                    cursor.execute(query, (cover_name, cover_mime_type, cover_MD5_hash))
                    cover_id = cursor.lastrowid

                    book_cover = cover_id
                    query = ("INSERT INTO books (book_name, book_description, book_year, book_publisher, book_author, book_size, book_cover) VALUES (%s, %s, %s, %s, %s, %s, %s)")
                    cursor.execute(query, (book_name, book_description, book_year, book_publisher, book_author, book_size, book_cover))

                    book_id = cursor.lastrowid
                    genre_ids = book_genres
                    for genre_id in genre_ids:
                        query = ("INSERT INTO books_to_genres (book_id, genre_id) VALUES (%s, %s)")
                        cursor.execute(query, (book_id, genre_id))

                    if not save_file(cover, cover_name):
                        raise Exception
                else:
                    book_cover = cover_id.cover_id
                    query = ("INSERT INTO books (book_name, book_description, book_year, book_publisher, book_author, book_size, book_cover) VALUES (%s, %s, %s, %s, %s, %s, %s)")
                    cursor.execute(query, (book_name, book_description, book_year, book_publisher, book_author, book_size, book_cover))

                    book_id = cursor.lastrowid
                    genre_ids = book_genres
                    for genre_id in genre_ids:
                        query = ("INSERT INTO books_to_genres (book_id, genre_id) VALUES (%s, %s)")
                        cursor.execute(query, (book_id, genre_id))
                db.connect().commit()
            return redirect(url_for("show_book", book_id=book_id))

        except Exception as err:
            print(f"ERROR CREATE_BOOK: {err}")
            db.connect().rollback()
            flash("При сохранении данных возникла ошибка. Проверьте корректность введённых данных.", "danger")
        return render_template("create_book.html", genres = genres, extensions = ALLOWED_EXTENSIONS, request=request)
    
    return render_template("create_book.html", genres = genres, extensions = ALLOWED_EXTENSIONS)

@app.route("/edit_book/<int:book_id>", methods=["GET", "POST"])
@login_required
@checkRole("edit")
def edit_book(book_id):
    genres = get_genres()
    book_genres = get_book_genres(book_id).split(", ")

    if request.method == "POST":
        book_name = request.form.get("name")
        book_description = bleach.clean(request.form.get("description"))
        book_year = request.form.get("year")
        book_publisher = request.form.get("publisher")
        book_author = request.form.get("author")
        book_size = request.form.get("size")
        book_genres = request.form.getlist("genres")

        try:
            with db.connect().cursor(named_tuple=True) as cursor:
                query = ("UPDATE books SET book_name=%s, book_description=%s, book_year=%s, book_publisher=%s, book_author=%s, book_size=%s WHERE book_id=%s")
                cursor.execute(query, (book_name, book_description, book_year, book_publisher, book_author, book_size, book_id))

                genre_ids = book_genres
                for genre_id in genre_ids:
                    query = ("DELETE FROM books_to_genres WHERE book_id=%s")
                    cursor.execute(query, (book_id, ))
                    query = ("INSERT INTO books_to_genres (book_id, genre_id) VALUES (%s, %s)")
                    cursor.execute(query, (book_id, genre_id))
                db.connect().commit()
            return redirect(url_for("show_book", book_id=book_id))

        except Exception as err:
            print(f"ERROR EDIT_BOOK: {err}")
            db.connect().rollback()
            flash("При сохранении данных возникла ошибка. Проверьте корректность введённых данных.", "danger")
        return render_template("edit_book.html", genres = genres, name = book_name, description = book_description, year = book_year, publisher = book_publisher, author = book_author, size = book_size, book_genres = book_genres)
    book = get_book(book_id)
    book_name = book.book_name
    book_description = book.book_description
    book_year = book.book_year
    book_publisher = book.book_publisher
    book_author = book.book_author
    book_size = book.book_size
    
    return render_template("edit_book.html", genres = genres, name = book_name, description = book_description, year = book_year, publisher = book_publisher, author = book_author, size = book_size, book_genres = book_genres)