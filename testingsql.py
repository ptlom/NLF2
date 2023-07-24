import mysql.connector as mysql
from sqlaccess import get_connection as get_db_connection

mydb = get_db_connection()
mycursor = mydb.cursor()

mycursor.execute("SHOW TABLES")

for tb in mycursor:
    print(tb)