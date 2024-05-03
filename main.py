from fastapi import FastAPI

from database import engine
import models
from db_uploader import init_data
from routers.user_router import user_router
from routers.exam_router import exam_router
import uvicorn

models.Base.metadata.create_all(bind=engine)

init_data()

description = """
시험 일정 예약 시스템 API
고객과 어드민이 각각의 필요에 맞게 시험 일정 예약을 처리합니다.

아래와 같은 ENDPOINT를 지원합니다
## 유저

* **유저 검색**
* **로그인**

## 시험 일정
* **시험 일정 조회**
* **시험 일정 생성**
* **시험 일정 예약신청**
* **내 예약 신청 조회**
* **예약 신청 조회**
* **예약 신청 확정**
* **예약 신청 수정**
* **예약 신청 삭제**
"""

app = FastAPI(
    title='BE 개발자 과제',
    description=description,
    summary='시험 일정 예약 처리 시스템',
)

app.include_router(user_router)
app.include_router(exam_router)


@app.get('/')
def read_root():
    return {'Hello': 'World'}


if __name__ == '__main__':
    uvicorn.run('main:app')
