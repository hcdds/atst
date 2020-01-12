from sqlalchemy import String, Column

from atst.models.base import Base


class CRL(Base):
    __tablename__ = "crls"

    serial_no = Column(String, unique=True, primary_key=True)
