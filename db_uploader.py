from sqlalchemy.engine.interfaces import DBAPICursor

from database import engine
import csv


def _insert_user(data, cursor: DBAPICursor):
    query = "INSERT INTO users(id, user_id, password, role) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;"

    cursor.execute(query, data)


def init_data():
    with open('data/users.csv', "r", encoding='utf-8') as data:
        print("---inserting user data started---")
        conn = engine.raw_connection()

        cursor = conn.cursor()
        data = csv.reader(data)

        for line in data:
            _insert_user(line, cursor)

        print("---inserting user data ended---")
        conn.commit()
