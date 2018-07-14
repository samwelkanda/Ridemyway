from flask import render_template, flash, redirect, url_for,request
from app import app, db
from app.forms  import LoginForm, RegistrationForm, EditProfileForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from werkzeug.urls import url_parse
from datetime import datetime

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Index')

@app.route('/dashboard')
@login_required
def dashboard():
    rides = [
        {
            'driver': {'username': 'king'},
            'time': '05/21/2018 09:00 AM',
            'from': 'Karen',
            'destination': 'Statehouse',
            'cost':'100'
        },
        {
            'driver': {'username': 'susan'},
            'time': '05/21/2018 12:00 AM',
            'from': 'JKIA',
            'destination': 'Lavington',
            'cost':'150'
        },
        {
            'driver': {'username': 'Lingard'},
            'time': '05/21/2018 05:00 PM',
            'from': 'Upperhill',
            'destination': 'Syokimau',
            'cost':'50'
        },

    ]
    return render_template('dashboard.html', title='Home', rides=rides)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard')
        return redirect(next_page)
    return render_template('sign_in.html', title='Sign In', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('sign_up.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    rides = [
        {
            'driver': user,
            'time': '04/01/2018 06:30 AM',
            'from': 'Juja',
            'destination': 'Upperhill',
            'cost':'150'
        },
        {
            'driver': user,
            'time': '04/01/2018 05:30 PM',
            'from': 'Upperhill',
            'destination': 'Juja',
            'cost':'150'
        },
    ]
    
    return render_template('user.html', user=user, rides=rides)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.car_details = form.car_details.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.car_details.data = current_user.car_details
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route('/create')
@login_required
def create():
    return render_template('offer.html', title='Create Ride')

@app.route('/all')
@login_required
def all():
    return render_template('available.html', title='All Rides')



@app.route('/history')
@login_required
def history():
    return render_template('history.html', title='History')

@app.route('/messages')
@login_required
def messages():
    return render_template('about.html', title='Messages')

@app.route('/requests')
@login_required
def requests():
    return render_template('about.html', title='Requests')


