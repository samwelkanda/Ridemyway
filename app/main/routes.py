from flask import render_template, flash, redirect, url_for,request, jsonify, current_app
from app import db
from app.main.forms  import EditProfileForm, RideForm
from flask_login import current_user, login_required
from app.models import User, Ride
from datetime import datetime
from app.main import bp

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Index')
@bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = RideForm()
    if form.validate_on_submit():
        ride = Ride(start=form.start.data, destination=form.destination.data, time=form.time.data, seats=form.seats.data, cost=form.cost.data, driver=current_user)
        db.session.add(ride)
        db.session.commit()
        flash('Your ride is now live!')
        return redirect(url_for('main.dashboard'))
    page = request.args.get('page', 1, type=int)
    rides = current_user.followed_rides().paginate(
        page, current_app.config['RIDES_PER_PAGE'], False)
    next_url = url_for('main.dashboard', page=rides.next_num) \
        if rides.has_next else None
    prev_url = url_for('main.dashboard', page=rides.prev_num) \
        if rides.has_prev else None
    return render_template('dashboard.html', title='Home', form=form, rides=rides.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    rides = user.rides.order_by(Ride.timestamp.desc()).paginate(
        page, current_app.config['RIDES_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page=rides.next_num) \
        if rides.has_next else None
    prev_url = url_for('main.user', username=user.username, page=rides.prev_num) \
        if rides.has_prev else None
    return render_template('user.html', user=user, rides=rides.items,
                           next_url=next_url, prev_url=prev_url)
    

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.car_details = form.car_details.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.car_details.data = current_user.car_details
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.dashboard'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('main.user', username=username))

@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.dashboard'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('main.user', username=username))

@bp.route('/about')
def about():
    return render_template('about.html', title='About')

@bp.route('/all')
@login_required
def all():
    page = request.args.get('page', 1, type=int)
    rides = Ride.query.order_by(Ride.timestamp.desc()).paginate(
        page, current_app.config['RIDES_PER_PAGE'], False)
    next_url = url_for('main.all', page=rides.next_num) \
        if rides.has_next else None
    prev_url = url_for('main.all', page=rides.prev_num) \
        if rides.has_prev else None
    return render_template('dashboard.html', title='Available rides', rides=rides.items, next_url=next_url, prev_url=prev_url)

@bp.route('/history')
@login_required
def history():
    return render_template('history.html', title='History')

@bp.route('/messages')
@login_required
def messages():
    return render_template('about.html', title='Messages')

@bp.route('/requests')
@login_required
def requests():
    return render_template('about.html', title='Requests')


