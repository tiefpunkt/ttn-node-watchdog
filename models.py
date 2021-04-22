from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid

from database import Base

from mails import *

def uuid_gen():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True)
    verified = Column(Boolean, default=False)

    devices =relationship("Device", back_populates="user")

    def __init__(self, email=None):
        self.email = email

    @property
    def is_active(self):
        return self.verified

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.email

    def start_login(self):
        token = Token(user, Token.TYPE_USER_LOGIN)
        db_session.add(token)
        db_session.commit()
        mail_user_login(self, token)

    def verify(self):
        token = Token(user, Token.TYPE_USER_VERIFICATION)
        db_session.add(token)
        db_session.commit()
        mail_user_verification(self, token)

    def __repr__(self):
        return '<User %r>' % (self.email)

class Device(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    dev_id = Column(String(120))
    app_id = Column(String(120))
    created = Column(DateTime())
    last_seen = Column(DateTime())
    status = Column(Integer)
    timeframe = Column(Integer)

    user = relationship("User", back_populates="devices")

    STATUS_UNKOWN = 0
    STATUS_ALIVE = 1
    STATUS_OFFLINE = 2
    STATUS_OFFLINE_NOTIFIED = 3

    def __init__(self, user, app_id , dev_id):
        self.user = user
        self.app_id = app_id
        self.dev_id = dev_id
        self.created = datetime.utcnow()
        self.status = self.STATUS_UNKOWN
        self.timeframe = 86400 # 24h



    def update_status(self):
        delta = timedelta(seconds=self.timeframe)
        if self.last_seen + delta <= datetime.utcnow():
            # Device is offline
            if self.status in [self.STATUS_OFFLINE, self.STATUS_OFFLINE_NOTIFIED]:
                return
            else:
                self.status = self.STATUS_OFFLINE
                mail_device_offline(self)
        else:
            if self.status == self.STATUS_ALIVE:
                return
            else:
                self.status = self.STATUS_ALIVE
                mail_device_online(self)


    def __repr__(self):
        return '<Device %r>' % (self.dev_id)

class Token(Base):
    __tablename__ = 'tokens'
    token = Column(String, primary_key=True, default = uuid_gen)
    user_id = Column(Integer, ForeignKey('users.id'))
    type = Column(Integer)
    valid_until = Column(DateTime())
    used = Column(Boolean, default=False)

    user = relationship("User")

    TYPE_USER_VERIFICATION = 1
    TYPE_USER_LOGIN = 2

    def __init__(self, user, type , delta = None):
        if delta:
            self.valid_until = datetime.utcnow() + delta
        else:
            if type == self.TYPE_USER_VERIFICATION:
                self.valid_until = datetime.utcnow() + timedelta(days=1)
            elif type == self.TYPE_USER_LOGIN:
                self.valid_until = datetime.utcnow() + timedelta(minutes=15)
        self.user = user
        self.type = type

    def __repr__(self):
        return '<Token %r>' % (self.token)
