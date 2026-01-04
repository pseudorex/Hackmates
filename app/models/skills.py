from app.database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.models.user_skills import user_skills


class Skills(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)

    users = relationship(
        "Users",
        secondary=user_skills,
        back_populates="skills"
    )