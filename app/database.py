import mysql.connector
from flask import g

# class Database:
#     def __init__(self, app):
#         self.app = app
#         self.app.teardown_appcontext(self.__exit__)

#     def get_config(self):
#         try:
#             return {
#                 "host": self.app.config["DB_HOST"],
#                 "user": self.app.config["DB_USER"],
#                 "password": self.app.config["DB_PASSWORD"],
#                 "database": self.app.config["DB_NAME"]
#             }
#         except Exception as err:
#             print(f"ERROR Database get_config: {err}")
    
#     def connect(self):
#         try:
#             if 'db' not in g:
#                 g.db = mysql.connector.connect(**self.get_config())
#             return g.db
#         except Exception as err:
#             print(f"ERROR Database connection: {err}")

#     def __exit__(self, e=None):
#        db = g.pop('db', None)
#        if db is not None:
#            db.close()

#Управления подключением к базе данных в веб-приложении на Flask, с использованием программного обеспечения mysql.connector
class Database:
    def __init__(self, app): #Конструктор принимает объект app, представляющий Flask-приложение. В нем настроен teardown_appcontext, который регистрирует метод close_db
        self.app = app
        self.app.teardown_appcontext(self.close_db) #Это гарантирует, что база данных будет закрыта после завершения обработки запроса, освобождая ресурс.
        
    def get_config(self): #Этот метод возвращает конфигурацию для подключения к базе данных, полученную из настроек конфигурации приложения app.config.
        try:
            return {
                'user': self.app.config['MYSQL_USER'],
                'password': self.app.config['MYSQL_PASSWORD'],
                'host': self.app.config['MYSQL_HOST'],
                'database': self.app.config['MYSQL_DATABASE']
            }
        except Exception as err:
            print(f"ERROR: {err}") #Если возникнет ошибка (например, если один из параметров отсутствует), она будет напечатана в консоли.
    
    def connect(self): #Метод connectу станавливает связь с базовыми данными, если они еще не были созданы в текущем запросе.
        if 'db' not in g:
            g.db = mysql.connector.connect(**self.get_config()) # Для хранения соединений используется gобъект Flask, который живёт в течение запроса 
        return g.db #и автоматически очищается после его завершения
    
    def close_db(self, e=None): #Метод close_db закрывает соединение с базовыми данными. Он извлекает объект соединения db из g и закрывает его, если он существует
        db = g.pop('db', None)
        if db is not None:
            db.close()
