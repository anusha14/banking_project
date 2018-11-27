from flask import session, render_template, url_for, redirect, jsonify
from werkzeug.security import check_password_hash

from banking_system import app
from .forms import CreateForm, LoginForm, WithdrawForm, DepositForm, TransferForm, DeleteForm
from .models import Account, Transaction, db, Deposit, Withdraw


@app.route('/')
def index():
    session.clear()
    return render_template('index.html')


@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    form = CreateForm()
    if form.validate_on_submit():
        name = form.name.data
        password = form.password.data
        if form.balance.data > 0:
            balance = form.balance.data
        else:
            balance = 0
        new_account = Account(name, password, balance)
        db.session.add(new_account)
        db.session.commit()
        new_transaction = Transaction('deposit', 'account opening', new_account.id, balance)
        new_deposit = Deposit('account opening', new_account.id, balance)
        db.session.add(new_transaction)
        db.session.add(new_deposit)
        db.session.commit()
        session['username'] = new_account.name
        return redirect(url_for('my_account'))
    return render_template('create_account.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        id = form.id.data
        password = form.password.data
        account = Account.query.get(id)
        if check_password_hash(account.password, password):
            session['username'] = account.name
            return redirect(url_for('my_account'))
        else:
            return '<h1>Invalid Account ID & Password combination</h1>'
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET'])
def logout():
    session['username'] = None
    return redirect(url_for('index'))


@app.route('/json/account/name/<name>')
def json_names(name):
    if Account.query.filter_by(name=name).first():
        return jsonify({'name': 'taken'})
    else:
        return jsonify({'name': 'available'})


@app.route('/json/account/id/<account_id>')
def json_account_id(account_id):
    if Account.query.filter_by(id=account_id).first():
        return jsonify({'account': 'valid account ID'})
    else:
        return jsonify({'account': 'invalid account ID'})


@app.route('/list_accounts')
def list_accounts():
    accounts = Account.query.filter_by(active=True)
    return render_template('list_accounts.html', accounts=accounts)


@app.route('/my_account', methods=['GET', 'POST'])
def my_account():
    withdraw_form = WithdrawForm()
    deposit_form = DepositForm()
    transfer_form = TransferForm()
    if session['username'] is None:
        return redirect(url_for('index'))
    user = session['username']
    account = Account.query.filter_by(name=user).first()
    transactions = Transaction.query.filter_by(account_id=account.id).order_by(Transaction.date.desc())
    return render_template('my_account.html', user=user, account=account, transactions=transactions,
                           withdraw_form=withdraw_form, deposit_form=deposit_form, transfer_form=transfer_form)


@app.route('/my_deposit', methods=['GET', 'POST'])
def my_deposit():
    deposit_form = DepositForm()
    if session['username'] is None:
        return redirect(url_for('index'))
    user = session['username']
    account = Account.query.filter_by(name=user).first()
    transactions = Transaction.query.filter_by(account_id=account.id).order_by(Transaction.date.desc())
    if deposit_form.deposit.data and deposit_form.validate():
        id = account.id
        amount = deposit_form.amount.data
        account = Account.query.get(id)
        if account.deposit_withdraw('deposit', amount):
            new_transaction = Transaction('deposit', 'self deposit', account.id, amount)
            new_deposit = Deposit('self deposit', account.id, amount)
            db.session.add(new_transaction)
            db.session.add(new_deposit)
            db.session.commit()
            return render_template('transaction_msg.html', user=user, account=account, transactions=transactions,
                                   deposit_form=deposit_form)
        else:
            return redirect(url_for('my_account'))
    return render_template('my_deposit.html', user=user, account=account, transactions=transactions,
                           deposit_form=deposit_form)


@app.route('/my_withdraw', methods=['GET', 'POST'])
def my_withdraw():
    withdraw_form = WithdrawForm()
    if session['username'] is None:
        return redirect(url_for('index'))
    user = session['username']
    account = Account.query.filter_by(name=user).first()
    transactions = Transaction.query.filter_by(account_id=account.id).order_by(Transaction.date.desc())
    if withdraw_form.withdraw.data and withdraw_form.validate():
        id = account.id
        amount = withdraw_form.amount.data
        account = Account.query.get(id)
        if account.deposit_withdraw('withdraw', amount):
            new_transaction = Transaction('withdraw', 'self withdraw', account.id, (amount * (-1)))
            new_withdraw = Withdraw('self withdraw', account.id, (amount * (-1)))
            db.session.add(new_transaction)
            db.session.add(new_withdraw)
            db.session.commit()
            return render_template('transaction_msg.html', user=user, account=account, transactions=transactions,
                                   withdraw_form=withdraw_form)
        else:

            return render_template('withdraw_not.html', user=user, account=account, transactions=transactions,
                                   withdraw_form=withdraw_form)
    return render_template('my_withdraw.html', user=user, account=account, transactions=transactions,
                           withdraw_form=withdraw_form)


@app.route('/my_transfer', methods=['GET', 'POST'])
def my_transfer():
    transfer_form = TransferForm()
    if session['username'] is None:
        return redirect(url_for('index'))
    user = session['username']
    account = Account.query.filter_by(name=user).first()
    transactions = Transaction.query.filter_by(account_id=account.id).order_by(Transaction.date.desc())
    if transfer_form.transfer.data and transfer_form.validate():
        id = account.id
        amount = transfer_form.amount.data
        account_id = transfer_form.account_id.data
        password = transfer_form.password.data
        account = Account.query.get(id)
        if check_password_hash(account.password, password):
            if account.deposit_withdraw('withdraw', amount):
                new_transaction = Transaction('transfer out', f'transfer to account {account_id}', account.id,
                                              (amount * (-1)))
                new_withdraw = Withdraw(f'transfer to account {account_id}', account.id,
                                        (amount * (-1)))
                db.session.add(new_transaction)
                db.session.add(new_withdraw)
                recipient = Account.query.get(account_id)
                if recipient.deposit_withdraw('deposit', amount):
                    new_transaction2 = Transaction('transfer in', f'transfer from account {account.id}', account_id,
                                                   amount)
                    new_deposit = Deposit(f'transfer from account {account.id}', account_id,
                                          amount)
                    db.session.add(new_transaction2)
                    db.session.add(new_deposit)
                    db.session.commit()
                    return render_template('transaction_msg.html', user=user, account=account,
                                           transactions=transactions, transfer_form=transfer_form)
                else:

                    return render_template('withdraw_not.html', user=user, account=account,
                                           transactions=transactions, transfer_form=transfer_form)
            else:

                return render_template('withdraw_not.html', user=user, account=account,
                                       transactions=transactions, transfer_form=transfer_form)
        else:
            return '<h1>Invalid Account Password</h1>'

    return render_template('my_transfer.html', user=user, account=account, transactions=transactions,
                           transfer_form=transfer_form)


@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    form = DeleteForm()
    if form.validate_on_submit():
        id = form.id.data
        password = form.password.data
        account = Account.query.get(id)
        if check_password_hash(account.password, password):
            account.active = False
            db.session.commit()
            return redirect(url_for('list_accounts'))
        else:
            return redirect(url_for('list_accounts'))
    return render_template('delete_account.html', form=form)
