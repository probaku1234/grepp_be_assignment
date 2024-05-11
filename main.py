from fastapi import FastAPI

from db.database import engine
from db import models
from db.db_uploader import init_data
from routers import api
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
tags_metadata = [
    {
        'name': '유저',
        'description': '유저와 관련된 API. **로그인** API도 여기에 있습니다'
    },
    {
        'name': '시험 일정',
        'description': '시험 일정과 관련된 API. 시험 일정 관리에 관련된 API들이 있습니다'
    }
]

app = FastAPI(
    title='BE 개발자 과제 API 문서',
    description=description,
    summary='시험 일정 예약 처리 시스템',
    openapi_tags=tags_metadata
)

app.include_router(api.router)


@app.get('/', name="Hello World!")
def read_root():
    """
    테스트용 API 입니다.
    """
    return {'Hello': 'World'}


if __name__ == '__main__':
    uvicorn.run('main:app')
