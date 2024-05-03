# [감독솔루션팀] BE 개발자 과제

시험 일정 예약 시스템 API 개발

## 개요

Python과 FastApi를 이용한 온라인 시험 플랫폼에서 고객과 어드민이 각각의 필요에 맞게 시험 일정 예약을 처리하는 시스템

### 사용한 Framework / library

* `FastApi` - RestApi Framework
* `Pydantic` - data validation
* `SqlAlchemy` - ORM
* `Postgres` - DB (docker를 이용해 호스팅)

### 프로젝트 폴더 구조

📂 BE Assignment  
|_📁 auth - jwt 인증 미들웨어  
|_📁 data  - 사전 데이터  
|_📁 docs  - api 문서를 위한 index.html 파일  
|_📁 routers  - endpoint들이 모인 router  
|_📁 tests  - 테스트 파일  
|_📄 .env.template  
|_📄 database.py  - DB 연결  
|_📄 db_uploader.py  - 사전 데이터 업로드를 위한 파일  
|_📄 docker-compose.yml  - postgres 호스팅  
|_📄 main.py  
|_📄 models.py  - DB Table 정의  
|_📄 pytest.ini  - 테스트 설정 파일   
|_📄 README.md  
|_📄 requirements.txt  
|_📄 schemas.py  endpoint들의 response와 request format을 정의하는 파일  
|_📄 util.py  

### DB 구조

* 유저 - 고객과 어드민 유저로 나뉩니다. (`role` column의 값으로 구분합니다. `client`/`admin`)
* 시험 일정
* 시험 일정 예약 - `confirmed` column으로 확정 여부를 표현합니다

### 사전 데이터

구현과 테스트를 쉽게 하기 위해 서버 시작시 사전 데이터를 삽입합니다.  (유저 생성 API는 따로 구현하지 않았습니다.)
1. 50000개의 고객 유저와 10개의 어드민 유저를 삽입합니다.
    * 고객 유저의 `user_id`는 1부터 50000까지 순서대로 `user {i}`를 가집니다. ex) user 1, user 2, user 3,....  
    * 어드민 유저의 `user_id`는 1부터 10까지 순서대로 `admin {i}`를 가집니다. ex) admin 1, admin 2, admin 3,....  
2. 2개의 시험 일정을 삽입합니다.
    * 하나는 현재 시간으로부터 2일 후를, 다른 하나는 5일 후를 시험 시간으로 가지는 시험 일정을 삽입합니다.



### API DOC

아래 링크에서 API 문서를 확인할 수 있습니다.

https://probaku1234.github.io/grepp_be_assignment/

### API 사용
* 로컬에서 실행 시, port 8000 사용합니다.
* [로그인 API](https://probaku1234.github.io/grepp_be_assignment/#tag/%EC%9C%A0%EC%A0%80/operation/%EB%A1%9C%EA%B7%B8%EC%9D%B8_users_login_post)를 사용해, 임의로 유저로 token을 발급 받아야 합니다.
* API에 따라 고객 유저만 사용가능하거나 어드민 유저만 사용 가능한 경우도 있습니다.

## 로컬에서 프로젝트 실행

### Dependencies

* 프로젝트를 실행하려는 컴퓨터에 최신 버전의 python과 docker engine이 설치되어있어야 합니다.

### 프로젝트 셋업 및 실행

* [`.env.template`](https://github.com/probaku1234/grepp_be_assignment/blob/master/.env.template)파일을 참고해서 .env 파일을
  생성합니다.
    * 임의의 jwt secret key를 생성해서 `JWT_SECRET`값으로 설정합니다.
    * `SQLALCHEMY_DATABASE_URL`는 template 파일에 있는 값을 그대로 사용합니다
  

* 아래 명령어를 사용해 가상 환경을 설정합니다.
    ```commandline
    python -m venv venv
    ```
* 아래 명령어를 사용해 가상환경모드로 진입합니다.
    ```commandline
  venv\Scripts\activate
    ```
* 아래 명령어를 사용해 프로젝트 실행에 필요한 파일들을 설치합니다.
    ```commandline
    pip install -r requirements.txt
    ```
* 아래 명령어를 실행해 postgres 도커를 실행합니다
    ```commandline
    docker-compose up
    ```
* `main.py` 파일을 실행합니다.
    ```commandline
  python main.py
    ```
  
## 로컬에서 테스트 실행
아래 명령어로 테스트를 실행할 수 있습니다
```commandline
pytest
```

