from src.infrastructure.databases import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Boolean



class ServiceContext(declarative_base):
    __tablename__ = 'service_context'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    maintenance: Mapped[bool] = mapped_column(Boolean, default=False)
