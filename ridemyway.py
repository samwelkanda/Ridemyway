from app import create_app, db
from app.models import User, Ride, MessageNotification, RequestNotification, Message, Request

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Ride': Ride, 'Message': Message, 'Request': Request,
            'RequestNotification': RequestNotification, 'MessageNotification': MessageNotification}
