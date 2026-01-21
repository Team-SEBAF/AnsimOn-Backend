from sqlalchemy.orm import Session

from app.domain.user.models.user_model import User


# TODO: CRUD 같은 기본 메소드들을 BaseRepository에 뺄까 고민중... 왜 GPT는 반대하는거지?
class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        return user

    def get(self, user_sub: str) -> User | None:
        return self.db.query(User).filter(User.user_sub == user_sub).first()

    def update(
        self,
        user: User,
        values: dict[str, object],
    ) -> User:
        for key, value in values.items():
            if not hasattr(user, key):
                raise ValueError(f"Invalid field: {key}")
            setattr(user, key, value)
        return user
