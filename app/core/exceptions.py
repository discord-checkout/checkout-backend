from fastapi import HTTPException, status

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="인증 정보를 확인할 수 없습니다.",
    headers={"WWW-Authenticate": "Bearer"},
)

not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="리소스를 찾을 수 없습니다.",
)
