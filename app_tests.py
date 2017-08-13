import datetime
import unittest

from playhouse.test_utils import test_database
from peewee import *

import learning_journal
from models import User, JournalEntry

TEST_DB = SqliteDatabase(':memory:')
TEST_DB.connect()
TEST_DB.create_tables([User, JournalEntry], safe=True)

USER_DATA = {
    'email': 'test_0@example.com',
    'password': 'password'
}


class UserModelTestCase(unittest.TestCase):
    """Test the User Model"""
    @staticmethod
    def create_users(count=2):
        """Create users for testing"""
        for i in range(count):
            User.create_user(
                email='test_{}@example.com'.format(i),
                password='password'
            )

    def test_create_user(self):
        """Test creating users"""
        with test_database(TEST_DB, (User,)):
            self.create_users()
            self.assertEqual(User.select().count(), 2)
            self.assertNotEqual(
                User.select().get().password,
                'password'
            )

    def test_create_duplicate_user(self):
        """Test creating a user that already exists"""
        with test_database(TEST_DB, (User,)):
            self.create_users()
            with self.assertRaises(ValueError):
                User.create_user(
                    email='test_1@example.com',
                    password='password'
                )


class JournalEntryModelTestCase(unittest.TestCase):
    """Test the JournalEntry Model"""
    def test_journal_entry_creation(self):
        """Test creating a JournalEntry"""
        with test_database(TEST_DB, (User, JournalEntry)):
            UserModelTestCase.create_users()
            user = User.select().get()
            JournalEntry.create(
                user=user,
                title='Testing Journal Entries',
                date=datetime.datetime.now().strftime('%Y-%m-%d'),
                time_spent='22',
                what_i_learned='Hopefully, I learn if this works or not!',
                resources_to_remember='teamtreehouse.com'
            )
            self.assertEqual(JournalEntry.select().count(), 1)
            self.assertEqual(JournalEntry.user, user)


class ViewTestCase(unittest.TestCase):
    """Parent class for testing app views. This sets up a test app."""
    def setUp(self):
        learning_journal.app.config['TESTING'] = True
        learning_journal.app.config['WTF_CSRF_ENABLED'] = False
        self.app = learning_journal.app.test_client()


class UserViewsTestCase(ViewTestCase):
    def test_registration(self):
        data = {
            'email': 'test@example.com',
            'password': 'password',
            'password2': 'password'
        }
        with test_database(TEST_DB, (User,)):
            rv = self.app.post(
                '/register',
                data=data)
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, 'http://localhost/')

    def test_good_login(self):
        with test_database(TEST_DB, (User,)):
            UserModelTestCase.create_users(1)
            rv = self.app.post('/login', data=USER_DATA)
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, 'http://localhost/')

    def test_bad_login(self):
        with test_database(TEST_DB, (User,)):
            rv = self.app.post('/login', data=USER_DATA)
            self.assertEqual(rv.status_code, 200)

    def test_logout(self):
        with test_database(TEST_DB, (User,)):
            # Create and login the user
            UserModelTestCase.create_users(1)
            self.app.post('/login', data=USER_DATA)

            rv = self.app.get('/logout')
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, 'http://localhost/')

    def test_logged_out_menu(self):
        rv = self.app.get('/')
        self.assertIn("register", rv.get_data(as_text=True).lower())
        self.assertIn("log in", rv.get_data(as_text=True).lower())

    def test_logged_in_menu(self):
        with test_database(TEST_DB, (User,)):
            UserModelTestCase.create_users(1)
            self.app.post('/login', data=USER_DATA)
            rv = self.app.get('/')
            self.assertIn("new entry", rv.get_data(as_text=True).lower())
            self.assertIn("log out", rv.get_data(as_text=True).lower())


class JournalEntryViewsTestCase(ViewTestCase):
    """Test Journal Entry Views"""
    def test_empty_db(self):
        """Message displays when there are no entries"""
        with test_database(TEST_DB, (User, JournalEntry)):
            UserModelTestCase.create_users(1)
            self.app.post('/login', data=USER_DATA)
            rv = self.app.get('/')
            self.assertIn("no entries", rv.get_data(as_text=True).lower())

    def test_journal_entry_create(self):
        """Test can create new JournalEntry, redirects to homepage, and adds to the database."""
        journal_entry_data = {
            'title': 'testing new journal entries',
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'time_spent': '2',
            'what_i_learned': 'how to test flask views',
            'resources_to_remember': 'teamtreehouse.com, stackoverflow.com, flask.pocoo.org'
        }
        with test_database(TEST_DB, (User, JournalEntry)):
            UserModelTestCase.create_users(1)
            self.app.post('/login', data=USER_DATA)

            journal_entry_data['user'] = User.select().get()
            rv = self.app.post('/entry', data=journal_entry_data)
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, 'http://localhost/')
            self.assertEqual(JournalEntry.select().count(), 1)

    def test_journal_entry_list(self):
        """Test new Journal Entries display on the home page, and the 'no entries' message does not."""
        journal_entry_data = {
            'title': 'testing new journal entries',
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'time_spent': '2',
            'what_i_learned': 'how to test flask views',
            'resources_to_remember': 'teamtreehouse.com, stackoverflow.com, flask.pocoo.org'
        }
        with test_database(TEST_DB, (User, JournalEntry)):
            UserModelTestCase.create_users(1)
            journal_entry_data['user'] = User.select().get()
            JournalEntry.create(**journal_entry_data)
            self.app.post('/login', data=USER_DATA)

            rv = self.app.get('/')
            self.assertNotIn('No Entries...', rv.get_data(as_text=True))
            self.assertIn(journal_entry_data['title'], rv.get_data(as_text=True))

    def test_list_view(self):
        """The list view contains a list of journal entries, which displays Title and Date for Entry."""
        journal_entry_data_1 = {
            'title': 'testing 1',
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'time_spent': '4',
            'what_i_learned': 'how to test flask views',
            'resources_to_remember': 'teamtreehouse.com, stackoverflow.com, flask.pocoo.org'
        }
        journal_entry_data_2 = {
            'title': 'testing 123',
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'time_spent': '8',
            'what_i_learned': 'how to test flask views',
            'resources_to_remember': 'teamtreehouse.com, stackoverflow.com, flask.pocoo.org'
        }
        with test_database(TEST_DB, (User, JournalEntry)):
            UserModelTestCase.create_users(1)
            user = User.select().get()
            journal_entry_data_1['user'] = user
            journal_entry_data_2['user'] = user
            JournalEntry.create(**journal_entry_data_1)
            JournalEntry.create(**journal_entry_data_2)

            self.app.post('/login', data=USER_DATA)
            rv = self.app.get('/entries')
            self.assertNotIn('No Entries...', rv.get_data(as_text=True))
            self.assertIn(journal_entry_data_1['title'], rv.get_data(as_text=True))
            self.assertIn(journal_entry_data_1['date'], rv.get_data(as_text=True))
            self.assertIn(journal_entry_data_2['title'], rv.get_data(as_text=True))
            self.assertIn(journal_entry_data_2['date'], rv.get_data(as_text=True))

    def test_empty_entries(self):
        """Message displays on Entries page when there are no entries"""
        with test_database(TEST_DB, (User, JournalEntry)):
            UserModelTestCase.create_users(1)
            self.app.post('/login', data=USER_DATA)
            rv = self.app.get('/entries')
            self.assertIn("no entries", rv.get_data(as_text=True).lower())

    def test_list_view_hyperlink(self):
        """The list view Title should be hyperlinked to the detail page for each journal entry."""
        journal_entry_data = {
            'title': 'testing hyperlink',
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'time_spent': '4',
            'what_i_learned': 'how to test flask views',
            'resources_to_remember': 'teamtreehouse.com, stackoverflow.com, flask.pocoo.org'
        }
        with test_database(TEST_DB, (User, JournalEntry)):
            UserModelTestCase.create_users(1)
            user = User.select().get()
            journal_entry_data['user'] = user
            JournalEntry.create(**journal_entry_data)

            self.app.post('/login', data=USER_DATA)
            hyperlink = 'href="/details/{}"'.format(JournalEntry.get().id)
            rv = self.app.get('/entries')
            self.assertIn(hyperlink, rv.get_data(as_text=True))

    def test_more_entries_button(self):
        """If there's more than 5 entries, the home page should display a More Entries button"""
        journal_entry_data = {
            'title': 'testing more entries',
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'time_spent': '4',
            'what_i_learned': 'how to test flask views',
            'resources_to_remember': 'teamtreehouse.com, stackoverflow.com, flask.pocoo.org'
        }
        with test_database(TEST_DB, (User, JournalEntry)):
            UserModelTestCase.create_users(1)
            user = User.select().get()
            journal_entry_data['user'] = user
            for _ in range(6):
                JournalEntry.create(**journal_entry_data)

            self.app.post('/login', data=USER_DATA)
            rv = self.app.get('/')
            self.assertIn('More Entries', rv.get_data(as_text=True))

    def test_details_view(self):
        """Details page displays all the fields Title, Date, Time Spent, What You Learned, Resources to Remember."""
        journal_entry_data = {
            'title': 'testing new journal entries',
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'time_spent': '2',
            'what_i_learned': 'how to test flask views',
            'resources_to_remember': 'teamtreehouse.com, stackoverflow.com, flask.pocoo.org'
        }
        with test_database(TEST_DB, (User, JournalEntry)):
            UserModelTestCase.create_users(1)
            journal_entry_data['user'] = User.select().get()
            JournalEntry.create(**journal_entry_data)
            self.app.post('/login', data=USER_DATA)
            rv = self.app.get('/details/{}'.format(JournalEntry.get().id))
            self.assertIn(journal_entry_data['title'], rv.get_data(as_text=True))
            self.assertIn(journal_entry_data['date'], rv.get_data(as_text=True))
            self.assertIn(journal_entry_data['time_spent'], rv.get_data(as_text=True))
            self.assertIn(journal_entry_data['what_i_learned'], rv.get_data(as_text=True))
            self.assertIn(journal_entry_data['resources_to_remember'], rv.get_data(as_text=True))

    def test_details_not_found(self):
        """Test redirect when details not found"""
        with test_database(TEST_DB, (User, JournalEntry)):
            rv = self.app.get('/details/1')
            self.assertNotEqual(rv.status_code, 404)
            self.assertIn('Redirecting...', rv.get_data(as_text=True))

    def test_details_link_to_edit(self):
        """Details page includes a link to edit the entry"""
        journal_entry_data = {
            'title': 'testing new journal entries',
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'time_spent': '2',
            'what_i_learned': 'how to test flask views',
            'resources_to_remember': 'teamtreehouse.com, stackoverflow.com, flask.pocoo.org'
        }
        with test_database(TEST_DB, (User, JournalEntry)):
            UserModelTestCase.create_users(1)
            journal_entry_data['user'] = User.select().get()
            JournalEntry.create(**journal_entry_data)
            self.app.post('/login', data=USER_DATA)
            rv = self.app.get('/details/{}'.format(JournalEntry.get().id))
            self.assertIn('href="/entry/', rv.get_data(as_text=True))


# Create “edit” view with the route “/entry”
# that allows the user to add or edit journal entry with the following fields:
# Title, Date, Time Spent, What You Learned, Resources to Remember.

# Add the ability to delete a journal entry.

# Add tags to journal entries in the model.
# Add tags to journal entries on the listing page and allow the tags to be links to a list of specific tags.
# Add tags to the details page.
# Create password protection or user login (provide credentials for code review).
# Routing uses slugs.


if __name__ == '__main__':
    unittest.main()

