import datetime
import unittest

from playhouse.test_utils import test_database
from peewee import *

import learning_journal
from models import User, JournalEntry, Tag, JournalEntryTag

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

    # def test_edit_view_loads_data(self):
    #     """Edit view allows the user to edit Title, Date, Time Spent, What You Learned, Resources to Remember."""
    #     journal_entry_data = {
    #         'title': 'testing_title',
    #         'date': '1980-01-01',
    #         'time_spent': 'testing_time',
    #         'what_i_learned': 'testing_learned',
    #         'resources_to_remember': 'testing_resources'
    #     }
    #     with test_database(TEST_DB, (User, JournalEntry)):
    #         UserModelTestCase.create_users(1)
    #         journal_entry_data['user'] = User.select().get()
    #         JournalEntry.create(**journal_entry_data)
    #         self.app.post('/login', data=USER_DATA)
    #         rv = self.app.get('/entry/{}'.format(JournalEntry.get().id))
    #         self.assertIn('testing_title', rv.get_data(as_text=True))
    #         self.assertIn('01/01/1980', rv.get_data(as_text=True))
    #         self.assertIn('testing_time', rv.get_data(as_text=True))
    #         self.assertIn('testing_learned', rv.get_data(as_text=True))
    #         self.assertIn('testing_resources', rv.get_data(as_text=True))
    #
    # def test_edit_not_found(self):
    #     """Test redirect when edit entry not found"""
    #     with test_database(TEST_DB, (User, JournalEntry)):
    #         rv = self.app.get('/edit/1')
    #         self.assertNotEqual(rv.status_code, 404)
    #         self.assertIn('Redirecting...', rv.get_data(as_text=True))


class TagModelTestCase(unittest.TestCase):
    """Tests to make sure the Tag Model works"""

    def test_create_tag(self):
        """Test creating tag"""
        with test_database(TEST_DB, (Tag,)):
            Tag.create(tag='test_tag')
            self.assertEqual(Tag.select().count(), 1)

    def test_create_duplicate_tag(self):
        """Make sure duplicate tags cannot be created"""
        with test_database(TEST_DB, (Tag,)):
            Tag.create_tag(tag='test_tag')
            with self.assertRaises(ValueError):
                Tag.create_tag(tag='test_tag')

    def test_many_to_many_relationships(self):
        """Make sure JournalEntries and Tags can have many to many relationships"""
        journal_entry_data_1 = {
            'title': 'entry 1',
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'time_spent': '111',
            'what_i_learned': 'many to many relationships',
            'resources_to_remember': 'docs.peewee-orm.com'
        }
        journal_entry_data_2 = {
            'title': 'entry 2',
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'time_spent': '222',
            'what_i_learned': 'many to many relationships',
            'resources_to_remember': 'docs.peewee-orm.com'
        }
        with test_database(TEST_DB, (User, JournalEntry, Tag, JournalEntryTag)):
            # create the user
            UserModelTestCase.create_users(1)

            # create the journal entries
            journal_entry_data_1['user'] = User.select().get()
            journal_entry_data_2['user'] = User.select().get()
            JournalEntry.create(**journal_entry_data_1)
            JournalEntry.create(**journal_entry_data_2)
            entry1 = JournalEntry.get(JournalEntry.title == 'entry 1')
            entry2 = JournalEntry.get(JournalEntry.title == 'entry 2')

            # create the tags
            Tag.create_tag(tag='first')
            Tag.create_tag(tag='both')
            Tag.create_tag(tag='second')
            tag1 = Tag.get(Tag.tag == 'first')
            tag2 = Tag.get(Tag.tag == 'both')
            tag3 = Tag.get(Tag.tag == 'second')

            # tie tags to entries
            entry1.tags.add([Tag.get(Tag.tag == 'first'),
                             Tag.get(Tag.tag == 'both')])

            entry2.tags.add([Tag.get(Tag.tag == 'second'),
                             Tag.get(Tag.tag == 'both')])

            # assertions
            self.assertIn(tag1, entry1.tags)
            self.assertIn(tag2, entry1.tags)
            self.assertNotIn(tag3, entry1.tags)

            self.assertNotIn(tag1, entry2.tags)
            self.assertIn(tag2, entry2.tags)
            self.assertIn(tag3, entry2.tags)

            self.assertIn(entry1, tag1.journal_entries)
            self.assertNotIn(entry2, tag1.journal_entries)

            self.assertIn(entry1, tag2.journal_entries)
            self.assertIn(entry2, tag2.journal_entries)

            self.assertNotIn(entry1, tag3.journal_entries)
            self.assertIn(entry2, tag3.journal_entries)



                # tag model works

# journal entry can have multiple tags
# tag can have multiple journal entries

    # model class for adding / editing tags
    # Add tags to journal entries in the model.

# Add the ability to delete a journal entry.


# Add tags to journal entries on the listing page and allow the tags to be links to a list of specific tags.
# Add tags to the details page.
# (provide credentials for code review).
# Routing uses slugs.


if __name__ == '__main__':
    unittest.main()

