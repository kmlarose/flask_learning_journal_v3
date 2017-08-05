import unittest

from playhouse.test_utils import test_database
from peewee import *

import learning_journal
from models import User, JournalEntry

TEST_DB = SqliteDatabase(':memory:')
TEST_DB.connect()
TEST_DB.create_tables([User, JournalEntry], safe=True)


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
                time_spent=22,
                learned='Hopefully, I learn if this works or not!',
                resources='teamtreehouse.com'
            )
            journal_entry = JournalEntry.select().get()

            self.assertEqual(
                JournalEntry.select().count(),
                1
            )
            self.assertEqual(JournalEntry.user, user)

# Create “list” view using the route /entries.
# The list view contains a list of journal entries, which displays Title and Date for Entry.
# Title should be hyperlinked to the detail page for each journal entry.
# Include a link to add an entry.

# Create “details” view with the route “/details” displaying the journal entry with all fields:
# Title, Date, Time Spent, What You Learned, Resources to Remember.
# Include a link to edit the entry.

# Create “add/edit” view with the route “/entry”
# that allows the user to add or edit journal entry with the following fields:
# Title, Date, Time Spent, What You Learned, Resources to Remember.
# Add the ability to delete a journal entry.

# Use the supplied HTML/CSS to build and style your pages.
# Use CSS to style headings, font colors, journal entry container colors, body colors.

# Add tags to journal entries in the model.
# Add tags to journal entries on the listing page and allow the tags to be links to a list of specific tags.
# Add tags to the details page.
# Create password protection or user login (provide credentials for code review).
# Routing uses slugs.


if __name__ == '__main__':
    unittest.main()

