from bcrypt import gensalt, hashpw, checkpw

from src.config import db, ma


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    pwd = db.Column(db.String(255), nullable=False)
    fullname = db.Column(db.String(255), nullable=False)
    activated = db.Column(db.Boolean, nullable=False)

    def __init__(self,
                 email: str,
                 pwd: str,
                 fullname: str,
                 activated: bool = True,
                 keep_tmp_pwd_raw: bool = False):
        self.email = email
        self.pwd = hashpw(pwd.encode('utf-8'), gensalt()).decode('utf-8')
        self.fullname = fullname
        self.activated = activated

        if keep_tmp_pwd_raw:
            self.pwd_tmp_raw = pwd

    def verify_password(self, pwd):
        return checkpw(pwd.encode('utf-8'), self.pwd.encode('utf-8'))


class UserSchema(ma.Schema):
    class Meta:
        model = User
        fields = ("id",
                  "email",
                  "fullname",
                  )
