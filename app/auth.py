from flask import (
    Blueprint,
    render_template,
    flash,
    request,
    redirect,
    url_for,
    session
)

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    current_user
)

from functools import wraps

from check_rights import CheckRights

from app import db

bp = Blueprint("auth", __name__)  #Эта строка создает объект Blueprintв Flask для модуля или раздела приложения, отвечающего за аутентификацию.

ADMIN_ROLE_ID = 1
MODERATOR_ROLE_ID = 2
USER_ROLE_ID = 3

def init_login_manager(app): #
    login_manager = LoginManager() #Функция определяет LoginManager
    login_manager.init_app(app) 
    login_manager.login_view = "auth.login" #регулирует перенаправление на вход страницы auth.login
    login_manager.login_message = "Для выполнения данного действия необходимо пройти процедуру аутентификации"
    login_manager.login_message_category = "warning"
    login_manager.user_loader(load_user) #и включается load_userдля загрузки пользователя по ID.

class User(UserMixin): #Этот класс Userпредставляет собой модель пользователя и включает основные атрибуты и методы проверки ролей и прав пользователя
    def __init__(self, id, login, surname, name, patronym, role): #Функция принимает и создает атрибуты объекта
        self.id = id
        self.login = login
        self.surname = surname
        self.name = name
        self.patronym = patronym
        self.role = role

    # Проверка ролей
    def is_admin(self):  
        return ADMIN_ROLE_ID == self.role 
    
    def is_moderator(self): 
        return MODERATOR_ROLE_ID == self.role 
    
    def is_user(self): 
        return USER_ROLE_ID == self.role 
    
    # Проверка прав доступа
    def can(self, action, record=None): 
        # Создается экземпляр класса CheckRights, передавая ему запись (record), над которой будут проверяться права.
        check_rights = CheckRights(record)
        # Используя встроенную функцию getattr, из объекта check_rights извлекается метод с именем, совпадающим со значением параметра action.
        # Если у объекта check_rights есть метод с таким именем, он будет возвращен; если нет — вернется None.
        method = getattr(check_rights, action, None) 
        # Если метод существует (то есть method не равен None), то вызывается этот метод и возвращается его результат.
        if method:
            return method()
        # Если метода с указанным именем нет, возвращается False, указывая на то, что действие не разрешено.
        return False
    
    #метод reviewотвечает за проверку настоящего отзыва пользователя на конкретную книгу
    def review(self, book_id):
        try:
            #Устанавливается соединение с базой данных и создается курсор, позволяющий выполнять SQL-запросы
            with db.connect().cursor(named_tuple=True) as cursor:
                # SQL-запрос для поиска идентификатора отзыва пользователя (review_id) по его ID и ID книги.
                query = ("SELECT review_id FROM reviews WHERE review_user=%s AND review_book=%s")
                #Выполняется запрос к базе данных с подстановкой параметров (self.id - ID пользователя, book_id - ID книги)
                cursor.execute(query, (self.id, book_id))
                #Извлекам одну запись (один отзыв) из результата запроса.
                review_id = cursor.fetchone()
                #Если отзыв не найден (review_id равно None), метод возвращает True, указывая, что отзыв не существует.
                if review_id == None:
                    return True
        except Exception as err:
            #В случае возникновения ошибки выводится сообщение об ошибке и метод возвращает False.
            print(f"USER: {err}")
            return False

def load_user(user_id): #загружает пользователя из базы данных user_id и извлекает объект User
    try:
        #соединение с базой данных
        with db.connect().cursor(named_tuple=True) as cursor:
                #SQL-запрос для получения данных пользователя с заданным user_id
                query = ("SELECT * FROM users WHERE user_id=%s")
                #Выполнение запроса с подстановкой параметра user_id
                cursor.execute(query, (user_id,))
                #Извлечение данных пользователя из результата запроса
                user_data = cursor.fetchone()
                ## Если данные пользователя найдены, создается и возвращается объект User
                if user_data:
                    return User(user_data.user_id, user_data.user_login, user_data.user_surname, user_data.user_name, user_data.user_patronym, user_data.user_role)
    except Exception as err:
        # В случае ошибки выводится сообщение об ошибке
        print(f"ERROR LOAD_USER: {err}")
    return None #Метод возвращается None, если пользователь не найден или допустил ошибку при выполнении запроса


def checkRole(action): #декоратор, принимающая параметр action, который представляет собой действие, права на выполнение которого необходимо проверить
    def decorator(f): #Внутри нее определена функция decorator(f), которая принимает оригинальную функцию f, на которую будет применен декоратор
        @wraps(f) #Используется для сохранения метаданных оригинальной функции f
        def wrapper(*args, **kwargs): #функция, которая оборачивает оригинальную функцию f. Эта обертка будет храниться вместо оригинальной функции
            #Извлекается user_id 
            user_id = kwargs.get("user_id")
            user = None
            #Если user_id присутствует, появляется функция load_user(user_id), чтобы получить объект пользователя
            if user_id: 
                user = load_user(user_id) 
            #Проверка прав пользователя на выполнение действия action
            if current_user.can(action,record=user) :
                #Если права есть, вызывается оригинальная функция f
                return f(*args, **kwargs)
            # Если прав недостаточно, выводится сообщение об ошибке и происходит перенаправление
            flash("У вас недостаточно прав для выполнения данного действия", "danger")
            return redirect(url_for("index"))
        return wrapper # Возвращается обертка
    return decorator #Возвращается декоратор

#Импортируется функция get_hash, которая используется для генерации хеша-файла
from hash import get_hash
@bp.route('/login', methods=['GET', 'POST']) #Этот декоратор определяет маршрут /login, который может обрабатывать как запросы GET, так и POST
def login():
    #Проверка метода запроса. Если POST, значит, пользователь отправил форму.
    if request.method == "POST":
        user_login = request.form.get("login") #Получаем логин пользователя из формы
        user_password = request.form.get("password") #Получаем пароль пользователя из формы
        remember = request.form.get("remember") #Получаем опцию "Запомнить меня" из формы

        # Генерация хеша пароля для проверки
        user_password_hash = get_hash(user_login, user_password)

        try:
            #Устанавливается соединение с базой данных и создается курсор для выполнения SQL-запросов
            with db.connect().cursor(named_tuple=True) as cursor:
                # SQL-запрос для поиска пользователя по логину и хешу пароля.
                query = ("SELECT * FROM users WHERE user_login=%s and user_password_hash=%s")
                # Выполняем запрос
                cursor.execute(query, (user_login, user_password_hash))
                # Извлекаем данные о пользователе
                user_data = cursor.fetchone()

                # Если пользователь найден, выполняется вход
                if user_data:
                    ## Создается объект User и выполняется вход с опцией запомнить
                    login_user(User(user_data.user_id, user_data.user_login, user_data.user_surname, user_data.user_name, user_data.user_patronym, user_data.user_role), remember=remember)
                    flash("Вы успешно прошли аутентификацию", "success")
                    #Перенаправление на главную страницу
                    return redirect(url_for("index"))
            # Если пользователь не найден, выводится сообщение об ошибке    
            flash("Невозможно аутентифицироваться с указанными логином и паролем", "danger")
        except Exception as err:
            # В случае ошибки выводится сообщение об ошибке
            print(f"ERROR LOGIN: {err}")
    ## Если метод GET, или произошла ошибка, возвращаем страницу входа
    return render_template("login.html")

@bp.route('/logout')
def logout():
    session.pop("history", None) #очистка сессии
    logout_user() 
    return redirect(url_for('index')) #перенаправление на глав. страниц