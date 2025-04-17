#Реализуем функции хеширования файлов и файлов с помощью библиотек argon2и hashlib
from argon2 import low_level
from hashlib import blake2b, md5

def get_hash(login, password): #Функция get_hashиспользует два аргумента — loginи password. Она безопасно использует хеш-код с помощью алгоритма Argon2
    #Преобразование строк логина и пароля в байтах
    login = bytes(login, 'utf-8')
    password = bytes(password, 'utf-8')

    #Соль формируется как хэш от логина и не хранится в ДБ
    salt = blake2b(login).hexdigest()
    #Преобразуется в байты
    salt = bytes.fromhex(salt)

    #Хэш пароля длиной 16 байт = 32 HEX символа, мешается с солью
    password_hash = low_level.hash_secret_raw(hash_len=16, salt=salt, time_cost=12, memory_cost=65536, parallelism=4, secret=password, type=low_level.Type.D) #
    password_hash = password_hash.hex()
    return password_hash # Хеш возвращается в шестнадцатеричном формате, готовом для сохранения или проверки

#Данная функция get_md5получения хеша файла с использованием алгоритма MD5.
def get_md5(file): 
    file_hash = md5(file).hexdigest()
    return file_hash

print(get_hash('chel','chel'))