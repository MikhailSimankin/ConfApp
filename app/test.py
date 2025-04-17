# from argon2 import low_level
# from hashlib import blake2b

# def get_hash(login, password):
#     login = bytes(login, 'utf-8')
#     password = bytes(password, 'utf-8')

#     #Соль формируется как хэш от логина и не хранится в ДБ
#     salt = blake2b(login).hexdigest()
#     #Преобразуется в байты
#     salt = bytes.fromhex(salt)

#     #Хэш пароля длиной 16 байт = 32 HEX символа, мешается с солью
#     password_hash = low_level.hash_secret_raw(hash_len=16, salt=salt, time_cost=12, memory_cost=65536, parallelism=4, secret=password, type=low_level.Type.D)
#     password_hash = password_hash.hex()
#     return password_hash

# def check_hash(login, password, db_password_hash):
#     password_hash = get_hash(login, password)
#     if password_hash == db_password_hash:
#         return True
#     return False

# login = input("Login\n")
# password = input("Password\n")

# print(get_hash(login, password))

# from app import db

# def set_book_genres(book_id, genre_ids):
#     try:

#         with db.connect().cursor(named_tuple=True) as cursor:
#                 for genre_id in genre_ids:
#                     query = ("INSERT INTO books_to_genres (book_id, genre_id) VALUES (%s, %s)")
#                     cursor.execute(query, (book_id, genre_id))
#                 print("SUCCESS")
#                 db.connect().commit()
#                 return 
#     except Exception as err:
#         db.connect().rollback()
#         print(f"ERROR GET_GENRES: {err}")


# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
# #Проверка расширения файла
# def allowed_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

import mimetypes

filename = input()

mime_type = mimetypes.guess_type(filename)

print(mime_type)