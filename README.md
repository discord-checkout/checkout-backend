# CheckOut Backend

AI 기반 패션 가이드 앱 **CheckOut**의 백엔드 API 서버입니다.
스타일 진단 → 핀셋 추천 → 단계별 로드맵 3단계 플로우를 제공합니다.

## 기술 스택

- **Framework**: FastAPI
- **Language**: Python 3.9+
- **ORM**: SQLAlchemy 2.0 (async)
- **DB**: PostgreSQL
- **AI**: Gemini 2.5 Flash

## 인증 방식

로그인/회원가입 없이 클라이언트가 생성한 UUID를 `X-User-ID` 헤더로 전송합니다.

```js
// 앱 최초 실행 시
const userId = localStorage.getItem('user_id') || crypto.randomUUID();
localStorage.setItem('user_id', userId);

// 모든 요청에 헤더 포함
headers: { 'X-User-ID': userId }
```

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| POST | `/onboarding/diagnose` | 스타일 진단 |
| GET | `/recommendations/first-item` | 첫 번째 아이템 추천 |
| GET | `/wardrobe` | 내 옷장 조회 |
| POST | `/wardrobe/add` | 옷장에 아이템 추가 |
| GET | `/wardrobe/roadmap` | 3개월 로드맵 |

API 문서 (Swagger): `http://서버주소:8000/docs`

> Swagger에서 테스트할 때는 **Authorize** 버튼 클릭 → UUID 입력

## 시작하기

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일에 DATABASE_URL, GEMINI_API_KEY 입력

# 3. 서버 실행 (DB 테이블 자동 생성)
uvicorn app.main:app --reload
```

## 환경 변수

| 변수 | 설명 |
|------|------|
| `DATABASE_URL` | PostgreSQL 연결 URL |
| `SECRET_KEY` | 서버 시크릿 키 |
| `GEMINI_API_KEY` | Google Gemini API 키 |
| `GEMINI_MODEL` | 사용할 Gemini 모델 (기본: gemini-2.5-flash) |
