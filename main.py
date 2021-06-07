from flask import Flask, request, abort, Response, render_template, url_for, flash, redirect
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from email_validator import validate_email, EmailNotValidError
from pytimeparse import parse as parse_timeframe
from datetime import datetime, timedelta
import timeago
import json
import yaml
from database import db_session, init_db
from models import User, Device, Token
from mails import mail_user_verification, mail_user_login

with open("config.yml","r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)

app = Flask(__name__)
Bootstrap(app)
# Use local bootstrap resources instead of CDN
app.config["BOOTSTRAP_SERVE_LOCAL"] = True
app.secret_key = config["general"]["secret_key"]
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@login_manager.user_loader
def load_user(user_id):
    return db_session.query(User).filter(User.email == user_id).one()

@app.template_filter('timeago')
def filter_timeago(timestamp):
    now = datetime.utcnow()
    return timeago.format(timestamp, now)

@app.template_filter('timeframe2str')
def filter_timeframe2str(timeframe):
    return str(timedelta(seconds=timeframe))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        try:
            email = request.form.get('email')
            valid = validate_email(email)
            email = valid.email
        except (EmailNotValidError, AttributeError) as e:
            flash("Please provide a valid email address", "danger")
            return render_template('login.html')

        user = db_session.query(User).filter(User.email == email).one_or_none()
        if user:
            token_obj = Token(user, Token.TYPE_USER_LOGIN)
            db_session.add(token_obj)
            db_session.commit()
            mail_user_login(user, token_obj)
        flash("If a user exists with the given email address, we sent a login link to that address. Please check your email inbox to complete your login.")
        #if not is_safe_url(next):
        #    return flask.abort(400)
        #return flask.redirect(next or flask.url_for('index'))

    return render_template('login.html')

@app.route('/login/<token>')
def user_login(token):
    token_obj = Token.query.filter(
            Token.token == token,
            Token.valid_until >= datetime.utcnow(),
            Token.used == False,
            Token.type == Token.TYPE_USER_LOGIN
        ).one_or_none()

    if token_obj == None:
        flash("The token you provided was not valid. Please try again.","error")
        return redirect(url_for("login")), 400

    else:
        flash("You're now logged in")
        token_obj.used = True
        db_session.commit()
        login_user(token_obj.user)
        return redirect(url_for("user_overview"))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/user/me')
@login_required
def user_overview():
    user = current_user
    return render_template('user.html', user = user)

@app.route('/api/v1/ping/<email>/<timeframe>', methods=['POST'])
@app.route('/api/v1/ping/<email>', methods=['POST'], defaults={"timeframe": None})
def ping(email, timeframe):
    try:
        # Validate.
        valid = validate_email(email)

        # Update with the normalized form.
        email = valid.email
    except EmailNotValidError as e:
        # email is not valid, exception message is human-readable
        print(str(e))
        abort(400)

    if not request.is_json:
        print("no valid json")
        abort(400)

    if timeframe:
        try:
            timeframe = parse_timeframe(timeframe)
        except:
            print("invalid timeframe")
            abort(400)

    data = request.get_json()
    app.logger.debug(data)

    try:
        app_id = data["end_device_ids"]["application_ids"]["application_id"]
        dev_id = data["end_device_ids"]["device_id"]
        received_at = data["received_at"]
    except:
        print("error")
        abort(400)

    user = User.query.filter(User.email == email).one_or_none()
    if user == None:
        user = User(email)
        db_session.add(user)
        token_obj = Token(user, Token.TYPE_USER_VERIFICATION)
        db_session.add(token_obj)
        db_session.commit()
        app.logger.info(f"New user created: {email}")
        mail_user_verification(user, token_obj)
        return json.dumps({"success": True, "message": "User created, needs verification."}), 200

    if user.verified == False:
        print("meh")
        return json.dumps({"success": False, "error": "Email address not yet verified."}), 400

    device = Device.query.filter(Device.user == user, Device.app_id == app_id, Device.dev_id == dev_id).one_or_none()
    if device == None:
        device = Device(user, app_id, dev_id)
        db_session.add(device)

    if timeframe and device.timeframe != timeframe:
        device.timeframe = timeframe

    device.last_seen = datetime.utcnow()
    db_session.commit()

    app.logger.info(f"PING: {app_id} - {dev_id} - {received_at}")

    return json.dumps({"success": True}), 201

@app.route('/user/verify/<token>')
def user_verification(token):
    token_obj = Token.query.filter(
            Token.token == token,
            Token.valid_until >= datetime.utcnow(),
            Token.used == False,
            Token.type == Token.TYPE_USER_VERIFICATION
        ).one_or_none()

    if token_obj == None:
        return json.dumps({"success": False, "error": "invalid token"}), 400

    else:
        token_obj.user.verified = True
        token_obj.used = True
        db_session.commit()
        return json.dumps({"success": True, "message": f"Email address {token_obj.user.email} successfully verified"}), 201

@app.cli.command("check-devices")
def check_devices():
    devices = Device.query.all()
    app.logger.info(f"Found {len(devices)} devices")
    for device in devices:
        device.update_status()
    db_session.commit()

@app.cli.command("init-db")
def cli_init_db():
    init_db()
