""""
테스트용 유저 데이터를 만드는 데 사용됩니다. `users.csv`에서 데이터를 가져옵니다.
"""

from sqlalchemy.dialects.postgresql import insert
from db.database import engine, Base
import csv
from dotenv import load_dotenv
import os
import datetime

load_dotenv()


def init_data():
    # 테스트 실행 시에는 사전 데이터 실행 스킵
    if os.environ.get('environment', 'dev') == 'test':
        return

    with open('../data/users.csv', 'r', encoding='utf-8') as data:
        print('---inserting user data started---')
        conn = engine.connect()

        data = csv.reader(data)

        users = []
        for line in data:
            users.append({
                'id': line[0],
                'user_id': line[1],
                'password': line[2],
                'role': line[3]
            })

        user_table = Base.metadata.tables['users']

        stmt = insert(user_table).values(users).on_conflict_do_nothing()
        conn.execute(stmt)

        conn.commit()
        conn.close()

    # with engine.connect() as conn:
    #     exam_table = Base.metadata.tables['exam_schedules']
    #
    #     exam1_insert_stmt = insert(exam_table).values(name='exam 1',
    #                                                   date_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
    #                                                       days=2)).on_conflict_do_nothing()
    #     exam2_insert_stmt = insert(exam_table).values(name='exam 2',
    #                                                   date_time=datetime.datetime.now(datetime.UTC) + datetime.timedelta(
    #                                                       days=5)).on_conflict_do_nothing()
    #
    #     conn.execute(exam1_insert_stmt)
    #     conn.execute(exam2_insert_stmt)
    #     conn.commit()

    print('---inserting user data ended---')
