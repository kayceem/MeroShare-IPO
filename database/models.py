from database.database import Base, DIR_PATH, get_db, engine
from sqlalchemy.sql.expression import  text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    dp = Column(String(255), nullable=False)
    boid = Column(String(255), nullable=False)
    passsword = Column(String(255), nullable=False)
    crn = Column(String(255), nullable=False)
    pin = Column(String(255), nullable=False)
    account = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),server_default=text('CURRENT_TIMESTAMP'), nullable=False)

with get_db() as db:
    users = [user.name for user in db.query(User).all()]

class Result(Base):
    __tablename__ = 'result'
    id = Column(Integer, primary_key=True, autoincrement=True)
    script = Column(String(255), unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),server_default=text('CURRENT_TIMESTAMP'), nullable=False)

    @declared_attr
    def __table_args__(cls):
        return tuple([Column(user, String(255), default="NA") for user in users])



class Applied(Base):
    __tablename__ = 'applied'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    ipo_name = Column(String(255), nullable=False)
    ipo = Column(String(255), nullable=False)
    share_type = Column(String(255), nullable=False)
    button = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    
    __table_args__ = (UniqueConstraint('name', 'ipo', name='uq_name_ipo'),)
    
# with open(f"{DIR_PATH}/Source Files/dataBase.txt", "r", encoding="utf-8") as fp:
#     lines = fp.read().splitlines()
#     with get_db() as db:
#         for line in lines:
#             data = line.split(",")
#             if len(data) != 7:
#                 continue
#             user = User(name=data[0], boid=data[2], dp=data[1], passsword=data[3], crn=data[4], pin=data[5], account=data[6])
#             db.add(user)
#             db.commit()
Base.metadata.create_all(engine)