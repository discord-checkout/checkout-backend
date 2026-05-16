# CheckOut Backend

AI 기반 패션 가이드 앱 **CheckOut**의 백엔드 API 서버입니다.
스타일 진단 → 핀셋 추천 → 단계별 로드맵 3단계 플로우를 제공합니다.

## 기술 스택

- **Framework**: FastAPI
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2.0 (async)
- **DB**: PostgreSQL
- **Auth**: JWT
- **AI**: Gemini 2.5 Flash

## 시작하기

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일에 DATABASE_URL, SECRET_KEY, GEMINI_API_KEY 입력

# 3. 서버 실행 (DB 테이블 자동 생성)
uvicorn app.main:app --reload
```

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| POST | `/auth/register` | 회원가입 |
| POST | `/auth/login` | 로그인 |
| POST | `/onboarding/diagnose` | 스타일 진단 |
| GET | `/recommendations/first-item` | 첫 번째 아이템 추천 |
| GET | `/wardrobe` | 내 옷장 조회 |
| POST | `/wardrobe/add` | 옷장에 아이템 추가 |
| GET | `/wardrobe/roadmap` | 3개월 로드맵 |

API 문서: `http://localhost:8000/docs`

## 환경 변수

| 변수 | 설명 |
|------|------|
| `DATABASE_URL` | PostgreSQL 연결 URL |
| `SECRET_KEY` | JWT 서명 키 |
| `GEMINI_API_KEY` | Google Gemini API 키 |
| `GEMINI_MODEL` | 사용할 Gemini 모델 (기본: gemini-2.5-flash) |
