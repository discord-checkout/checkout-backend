import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    style_profile: Mapped["StyleProfile"] = relationship(  # noqa: F821
        "StyleProfile", back_populates="user", uselist=False
    )
    wardrobe_items: Mapped[list["WardrobeItem"]] = relationship(  # noqa: F821
        "WardrobeItem", back_populates="user"
    )
