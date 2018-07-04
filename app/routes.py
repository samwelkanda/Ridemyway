from flask import render_template, flash, redirect, url_for
from app import app
from app.forms  import LoginForm

@app.route('/')
@app.route('/dashboard')
def dashboard():
    user = {'username': 'Kanda'}
    rides = [
        {
            'driver': {'username': 'Pogba'},
            'time': '05/21/2018 09:00 AM',
            'from': 'Karen',
            'destination': 'Statehouse',
            'cost':'100'
        },
        {
            'driver': {'username': 'Rashford'},
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
    return render_template('dashboard.html', title='Home', user=user, rides=rides)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('dashboard'))
    return render_template('sign_in.html', title='Sign In', form=form)

@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route('/create')
def create():
    return render_template('offer.html', title='Create Ride')

@app.route('/all')
def all():
    return render_template('available.html', title='All Rides')

@app.route('/logout')
def logout():
    return render_template('about.html', title='Logout')

@app.route('/history')
def history():
    return render_template('history.html', title='History')

@app.route('/messages')
def messages():
    return render_template('about.html', title='Messages')

@app.route('/requests')
def requests():
    return render_template('about.html', title='Requests')

@app.route('/profile')
def profile():
    return render_template('profile.html', title='Profile')

