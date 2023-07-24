import mysql.connector as mysql
import streamlit as st

user = st.secrets["DB_USER"]
pswd = st.secrets["DB_PSWD"]
host = st.secrets["DB_HOST"]
dbname = st.secrets["DB_NAME"]

def get_connection():
    return mysql.connect(
        host = host,
        user = user,
        passwd = pswd,
        database = "tradedb"
    )

def get_user():
    return user

if __name__ == "__main__":
    mydb = get_connection()
    mycursor = mydb.cursor()
    # type in the query here (create/edit a DB, etc.)