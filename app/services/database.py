import sqlite3
db_file='app/data/users.db'
def get_connection():
    conn=sqlite3.connect(db_file)
    cursor=conn.cursor()
    cursor.execute("""
                   create table if not exists users(
                   id integer primary key autoincrement,
                   name text not null,
                   email text unique not null,
                   password text not null,
                   city text not null,
                   salary integer not null
                   )
                   """)
    conn.commit()
    conn.close()
def add_user(name,email,password,city,salary):
    conn=sqlite3.connect(db_file)
    cursor=conn.cursor()
    cursor.execute(""" 
                   insert into users(name,email,password,city,salary) values(?,?,?,?,?)
                   """,(name,email,password,city,salary))
    conn.commit()
    conn.close()
def email_exists(email):

    conn = sqlite3.connect(db_file)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    )

    user = cursor.fetchone()

    conn.close()

    return user
def check_user(email,password):
    conn=sqlite3.connect(db_file)
    cursor=conn.cursor()
    cursor.execute("""
                   select * from users where email=? and password=?
                   """,(email,password))
    user=cursor.fetchone()
    conn.close()
    return user
