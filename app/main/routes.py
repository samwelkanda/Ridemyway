from flask import render_template, flash, redirect, url_for,request, jsonify, current_app, g
from app import db
from app.main.forms  import EditProfileForm, RideForm, SearchForm, MessageForm, RequestForm
from flask_login import current_user, login_required
from app.models import User, Ride, Message, Request, RequestNotification, MessageNotification
from datetime import datetime
from app.main import bp

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()

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

@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_popup.html', user=user)

@bp.route('/send_message/<message_recipient>', methods=['GET', 'POST'])
@login_required
def send_message(message_recipient):
    user = User.query.filter_by(username=message_recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(driver=current_user, message_recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_messagenotification('unread_message_count', user.new_messages())
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('main.user', username=message_recipient))
    return render_template('send_message.html', title='Send Message',
                           form=form, message_recipient=message_recipient)

@bp.route('/send_request/<request_recipient>', methods=['GET', 'POST'])
@login_required
def send_request(request_recipient):
    user = User.query.filter_by(username=request_recipient).first_or_404()
    form = RequestForm()
    if form.validate_on_submit():
        rqst = Request(driver=current_user, request_recipient=user,
                      pickup=form.pickup.data, time=form.time.data, seats=form.seats.data)
        db.session.add(rqst)
        user.add_requestnotification('unread_request_count', user.new_requests())
        db.session.commit()
        flash('Your request has been sent.')
        return redirect(url_for('main.dashboard'))
    return render_template('send_request.html', title='Send Request',
                           form=form, request_recipient=request_recipient)

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
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_messagenotification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['RIDES_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/message_notifications')
@login_required
def message_notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.message_notifications.filter(
        MessageNotification.timestamp > since).order_by(MessageNotification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])

@bp.route('/requests')
@login_required
def requests():
    current_user.last_request_read_time = datetime.utcnow()
    current_user.add_requestnotification('unread_request_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    requests = current_user.requests_received.order_by(
        Request.timestamp.desc()).paginate(
            page, current_app.config['RIDES_PER_PAGE'], False)
    next_url = url_for('main.requests', page=requests.next_num) \
        if requests.has_next else None
    prev_url = url_for('main.requests', page=requests.prev_num) \
        if requests.has_prev else None
    return render_template('requests.html', requests=requests.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/request_notifications')
@login_required
def request_notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.request_notifications.filter(
        RequestNotification.timestamp > since).order_by(RequestNotification.timestamp.asc())
    return jsonify([{
        'name': r.name,
        'data': r.get_data(),
        'timestamp': r.timestamp
    } for r in notifications])

@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.dashboard'))
    page = request.args.get('page', 1, type=int)
    rides, total = Ride.search(g.search_form.q.data, page,
                               current_app.config['RIDES_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['RIDES_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search', rides=rides,
                           next_url=next_url, prev_url=prev_url)
