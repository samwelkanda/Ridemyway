from flask import render_template
from app import app
from app.forms  import LoginForm

@app.route('/')
@app.route('/dashboard')
def dashboard():
    user = {'username': 'Kanda'}
    rides = [
        {
            'driver': {'username': 'Paul Pogba'},
            'time': '05/21/2018 09:00 AM',
            'from': 'Karen',
            'destination': 'Statehouse'
        },
        {
            'driver': {'username': 'Marcus Rashford'},
            'time': '05/21/2018 12:00 AM',
            'from': 'JKIA',
            'destination': 'Lavington'
        },
        {
            'driver': {'username': 'Jesse Lingard'},
            'time': '05/21/2018 05:00 PM',
            'from': 'Upperhill',
            'destination': 'Syokimau'
        },

    ]
    return render_template('dashboard.html', title='Home', user=user, rides=rides)

@app.route('/login')
def login():
    form = LoginForm()
    return render_template('sign_in.html', title='Sign In', form=form)
