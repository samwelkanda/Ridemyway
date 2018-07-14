from flask import render_template, flash, redirect, url_for,request
from app import app, db
from app.forms  import LoginForm, RegistrationForm, EditProfileForm, RideForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Ride
from werkzeug.urls import url_parse
from datetime import datetime
from app.email import send_password_reset_email

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])

@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Index')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = RideForm()
    if form.validate_on_submit():
        ride = Ride(start=form.start.data, destination=form.destination.data, time=form.time.data, seats=form.seats.data, cost=form.cost.data, driver=current_user)
        db.session.add(ride)
        db.session.commit()
        flash('Your ride is now live!')
        return redirect(url_for('dashboard'))
    page = request.args.get('page', 1, type=int)
    rides = current_user.followed_rides().paginate(
        page, app.config['RIDES_PER_PAGE'], False)
    next_url = url_for('index', page=rides.next_num) \
        if rides.has_next else None
    prev_url = url_for('dashboard', page=rides.prev_num) \
        if rides.has_prev else None
    return render_template('dashboard.html', title='Home', form=form, rides=rides.items, next_url=next_url,
                           prev_url=prev_url)

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

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('dashboard'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    rides = user.rides.order_by(Ride.timestamp.desc()).paginate(
        page, app.config['RIDES_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=rides.next_num) \
        if rides.has_next else None
    prev_url = url_for('user', username=user.username, page=rides.prev_num) \
        if rides.has_prev else None
    return render_template('user.html', user=user, rides=rides.items,
                           next_url=next_url, prev_url=prev_url)
    

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

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('user', username=username))

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
    page = request.args.get('page', 1, type=int)
    rides = Ride.query.order_by(Ride.timestamp.desc()).paginate(
        page, app.config['RIDES_PER_PAGE'], False)
    next_url = url_for('index', page=rides.next_num) \
        if rides.has_next else None
    prev_url = url_for('dashboard', page=rides.prev_num) \
        if rides.has_prev else None
    return render_template('dashboard.html', title='Available rides', rides=rides.items, next_url=next_url, prev_url=prev_url)



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


