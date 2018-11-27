import datetime
import urllib

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

from banking_system import app

string_connection = "DRIVER={SQL Server Native Client 11.0};Server=192.168.18.36;Database=HBK_Test;UID=anushab;PWD=Welcome123;Trusted_Connection=no;"
string_connection = urllib.parse.quote_plus(string_connection)
string_connection = "mssql+pyodbc:///?odbc_connect=%s" % string_connection

app.config["SQLALCHEMY_DATABASE_URI"] = string_connection
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db = SQLAlchemy(app)


class Account(db.Model):
    __tablename__ = 'Account'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True)
    password = db.Column(db.Text)
    balance = db.Column(db.Float)
    active = db.Column(db.Boolean, default=True)

    def deposit_withdraw(self, type, amount):
        if type == 'withdraw':
            amount *= -1
        if self.balance + amount < 0:
            return False  
        else:
            self.balance += amount
            return True

    def __init__(self, name, password, balance=0):
        self.name = name
        self.password = generate_password_hash(password)
        self.balance = balance

    def __repr__(self):
        return f"Account name is {self.name} with account number {self.id}"


class Transaction(db.Model):
    __tablename__ = 'Transaction'
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.Text)
    description = db.Column(db.Text)
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.datetime.now)
    account_id = db.Column(db.Integer, db.ForeignKey('Account.id'), nullable=False)
    account = db.relationship('Account', backref=db.backref('Transaction', lazy=True))

    def __init__(self, transaction_type, description, account_id, amount=0):
        self.transaction_type = transaction_type
        self.description = description
        self.account_id = account_id
        self.amount = amount

    def __repr__(self):
        return f"Transaction {self.id}: {self.transaction_type} on {self.date}"


class Deposit(db.Model):
    __tablename__ = 'Deposit'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text)
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.datetime.now)
    account_id = db.Column(db.Integer, db.ForeignKey('Account.id'), nullable=False)

    def __init__(self, description, account_id, amount):
        self.description = description
        self.account_id = account_id
        self.amount = amount


class Withdraw(db.Model):
    __tablename__ = 'Withdraw'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text)
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.datetime.now)
    account_id = db.Column(db.Integer, db.ForeignKey('Account.id'), nullable=False)

    def __init__(self, description, account_id, amount):
        self.description = description
        self.account_id = account_id
        self.amount = amount


db.create_all()
