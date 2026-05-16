# CLAUDE.md — CheckOut Backend

## 프로젝트 개요

**CheckOut**은 옷장이 빈 대학생을 타겟으로 한 AI 기반 패션 가이드 앱입니다.
스타일 진단 → 핀셋 추천 → 단계별 로드맵 3단계 플로우로 구성됩니다.

---

## 기술 스택

| 항목        | 선택                                    |
| ----------- | --------------------------------------- |
| 프레임워크  | FastAPI                                 |
| 언어        | Python 3.11+                            |
| ORM         | SQLAlchemy 2.0 (async)                  |
| DB          | PostgreSQL                              |
| 인증        | JWT (python-jose)                       |
| 패키지 관리 | pip + requirements.txt                  |
| AI          | Gemini 2.5 Flash (Google Generative AI) |
| 배포        | Railway / Render (무료 플랜)            |

---

## 디렉토리 구조

```
checkout-backend/
├── app/
│   ├── main.py                  # FastAPI 앱 생성, 라우터 등록
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # async engine, get_db 의존성
│   │   └── security.py          # JWT 생성/검증
│   ├── models/                  # SQLAlchemy ORM 모델
│   │   ├── user.py
│   │   └── style_profile.py
│   ├── schemas/                 # Pydantic v2 스키마
│   │   ├── user.py
│   │   └── style_profile.py
│   ├── routers/
│   │   ├── auth.py              # POST /auth/register, /auth/login
│   │   ├── onboarding.py        # POST /onboarding/diagnose
│   │   ├── recommendations.py   # GET /recommendations/first-item
│   │   └── wardrobe.py          # GET /wardrobe/roadmap
│   ├── services/
│   │   └── ai.py                # Gemini 2.5 Flash 호출 로직
│   └── dependencies.py          # get_current_user 등 공통 의존성
├── .env.example
└── requirements.txt
```

---

## 핵심 도메인 모델

### User

```python
# 필드: id, nickname, created_at
# 별도 회원가입 없음 — 클라이언트가 생성한 UUID로 자동 생성
```

### StyleProfile

```python
# 필드: id, user_id(FK),
#        style_mood        # "minimal" | "casual" | "cityboy" | "amekaji" | "sports" | "vintage"
#        fit_preference    # "slim" | "regular" | "overfit" | "unknown"
#        lifestyle         # "campus" | "office" | "daily" | "freelance"
#        budget_range      # "under_5" | "5_to_10" | "10_to_20" | "over_20"  (만원 단위)
#        current_wardrobe  # JSONB: { "top": [...], "bottom": [...], "outer": [...], "shoes": [...] }
#        profile_summary   # Gemini가 생성한 한 줄 요약
#        created_at, updated_at
```

---

## API 엔드포인트 명세

### 인증

별도 로그인/회원가입 없음. 모든 요청에 `X-User-ID` 헤더(클라이언트 생성 UUID)를 포함하면 자동으로 유저가 생성됩니다.

```
X-User-ID: 550e8400-e29b-41d4-a716-446655440000
```

### 온보딩 (스타일 진단)

```
POST /onboarding/diagnose
  Auth: Bearer token
  Body: {
    "style_mood": "minimal" | "casual" | "cityboy" | "amekaji" | "sports" | "vintage",
    "fit_preference": "slim" | "regular" | "overfit" | "unknown",
    "lifestyle": "campus" | "office" | "daily" | "freelance",
    "current_wardrobe": {
      "top": ["white_black_tee", "hoodie", "knit", ...],   # 없으면 빈 배열
      "bottom": ["black_slacks", "wide_denim", ...],
      "outer": ["coach_jacket", "windbreaker", ...],
      "shoes": ["white_sneakers", "new_balance", ...]
    },
    "budget_range": "under_5" | "5_to_10" | "10_to_20" | "over_20"
  }
  Returns: {
    "profile_id": "uuid",
    "profile_summary": "캠퍼스 라이프 · 월 10만원 · 미니멀 캐주얼",
    "current_combination_count": 3,   # 현재 옷장 기준 조합 수
    "style_mood": "minimal"
  }

  # 내부 동작:
  # 1. StyleProfile DB 저장
  # 2. ai.analyze_wardrobe(current_wardrobe) → 현재 조합 수 계산
  # 3. profile_summary 생성 후 응답
```

### 첫 번째 옷 핀셋 추천

```
GET /recommendations/first-item
  Auth: Bearer token
  Returns: {
    "item_name": "오버핏 화이트 서츠",
    "price": 29000,
    "brand": "무신사 스탠다드",
    "reason": "미니멀 캐주얼의 핵심 아이템. 가진 청바지·카고 모두와 바로 연결됩니다.",
    "search_url": "https://musinsa.com/search?q=오버핏+화이트+셔츠",
    "combinations": [
      { "label": "조합 1", "description": "화이트 셔츠 + 청바지 + 흰 스니커즈" },
      { "label": "조합 2", "description": "화이트 셔츠 + 카고 팬츠 + 뉴발란스" },
      { "label": "조합 3", "description": "화이트 셔츠 + 슬랙스 + 로퍼" }
    ],
    "current_combination_count": 3,
    "after_combination_count": 12
  }

  # 내부 동작:
  # 1. user의 StyleProfile 조회
  # 2. ai.recommend_first_item(style_profile) 호출 → 추천 아이템 + 이유 + 조합 반환
  # 3. 무신사 검색 URL 생성 (search_url)
  # 4. 응답 조립
```

### 옷장 & 로드맵

```
GET /wardrobe
  Auth: Bearer token
  Returns: { items: [...], total_combination_count: 12 }

POST /wardrobe/add
  Auth: Bearer token
  Body: { "item_id": "uuid" }
  Returns: {
    "added_item": {...},
    "new_combination_count": 12,
    "delta": +9   # 추가로 생긴 조합 수
  }

GET /wardrobe/roadmap
  Auth: Bearer token
  Returns: {
    "months": [
      {
        "month": 1,
        "recommended_item": { ... },
        "reason": "지난달 아이템과 엮이면 조합이 2배",
        "projected_combination_count": 6
      },
      {
        "month": 2,
        "recommended_item": { ... },
        "projected_combination_count": 12
      }
    ]
  }
```

---

## 환경 변수 (.env.example)

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/checkout
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

---

## 개발 시작 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. .env 파일 작성 (.env.example 복사)
cp .env.example .env

# 3. 서버 실행 (DB 테이블은 시작 시 자동 생성)
uvicorn app.main:app --reload
```

## 배포 (Railway 기준)

1. GitHub 레포 연결
2. PostgreSQL 플러그인 추가 → `DATABASE_URL` 자동 주입
3. 환경 변수에 `.env` 내용 입력
4. 배포 완료

---

## 코딩 컨벤션

- **모든 DB 쿼리는 async** — `AsyncSession` 사용, sync 드라이버 금지
- **스키마 분리** — Request용 `XxxIn`, Response용 `XxxOut`, DB용 ORM 모델 각각 분리
- **서비스 레이어** — 비즈니스 로직은 `services/`에, 라우터는 얇게 유지
- **에러 처리** — `HTTPException` 직접 raise, 커스텀 예외는 `app/core/exceptions.py`에 정의
- **타입 힌트 필수** — 모든 함수에 input/output 타입 명시

---
