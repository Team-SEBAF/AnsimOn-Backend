from sqlalchemy.orm import Session

from app.domain.user.models.user_model import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        return user

    def get(self, user_sub: str) -> User | None:
        return self.db.query(User).filter(User.user_sub == user_sub).first()

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def update(
        self,
        user: User,  # sub로 조회해서 업데이트 하는 게 PostgreSQL에 적절하지 않다나 뭐라나...
        values: dict[str, object],
    ) -> User:
        for key, value in values.items():
            if not hasattr(user, key):
                raise ValueError(f"Invalid field: {key}")
            setattr(user, key, value)
        return user

    def delete_by_user_sub(self, user_sub: str):
        user = self.db.query(User).filter(User.user_sub == user_sub).one_or_none()
        if user:
            self.db.delete(user)
