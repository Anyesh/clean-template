from src.infrastructure.databases import Base as SQLAlchemyBase, sqlalchemy_db as db
from sqlalchemy.orm import MappedAsDataclass, Mapped, mapped_column



class ServiceContext(MappedAsDataclass, SQLAlchemyBase):
    __tablename__ = 'service_context'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, init=False)
    maintenance: Mapped[bool] = mapped_column(db.Boolean, default=False)