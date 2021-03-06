from datetime import datetime, timedelta
import unittest
from app import create_app, db
from app.models import User, Ride
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
                                         'd4c74594d841139328695756648b6bd6'
                                         '?d=identicon&s=128'))

    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'susan')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'john')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_rides(self):
        # create four users
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # create four rides
        now = datetime.utcnow()
        r1 = Ride(start="Eldoret", destination="Kakamega", time="06/01/2018 10:00 AM", seats=2, cost=200, driver=u1,
                  timestamp=now + timedelta(seconds=1))
        r2 = Ride(start="Nakuru", destination="Naivasha", time="06/01/2018 11:00 AM", seats=4, cost=100, driver=u2,
                  timestamp=now + timedelta(seconds=4))
        r3 = Ride(start="Nairobi", destination="Thika", time="06/01/2018 2:00 PM", seats=3, cost=50, driver=u3,
                  timestamp=now + timedelta(seconds=3))
        r4 = Ride(start="Narok", destination="Nairobi", time="06/01/2018 4:00 PM", seats=2, cost=80, driver=u4,
                  timestamp=now + timedelta(seconds=2)) 
        db.session.add_all([r1, r2, r3, r4])
        db.session.commit()

        # setup the followers
        u1.follow(u2)  # john follows susan
        u1.follow(u4)  # john follows david
        u2.follow(u3)  # susan follows mary
        u3.follow(u4)  # mary follows david
        db.session.commit()

        # check the followed posts of each user
        f1 = u1.followed_rides().all()
        f2 = u2.followed_rides().all()
        f3 = u3.followed_rides().all()
        f4 = u4.followed_rides().all()
        self.assertEqual(f1, [r2, r4, r1])
        self.assertEqual(f2, [r2, r3])
        self.assertEqual(f3, [r3, r4])
        self.assertEqual(f4, [r4])

if __name__ == '__main__':
    unittest.main(verbosity=2)