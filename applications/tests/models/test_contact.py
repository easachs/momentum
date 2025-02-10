from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from applications.models import Contact

class ContactModelTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = get_user_model().objects.create_user(
            username='otheruser',
            password='testpass123'
        )

    def test_contact_creation(self):
        """Test basic contact creation with all fields"""
        contact = Contact.objects.create(
            user=self.user,
            name="John Doe",
            company="Test Corp",
            role="hiring_manager",
            email="john@test.com",
            phone="123-456-7890",
            notes="Test notes"
        )
        
        self.assertEqual(contact.name, "John Doe")
        self.assertEqual(contact.company, "Test Corp")
        self.assertEqual(contact.get_role_display(), "Hiring Manager")
        self.assertEqual(contact.email, "john@test.com")
        self.assertEqual(contact.phone, "123-456-7890")
        self.assertEqual(contact.notes, "Test notes")

    def test_contact_minimal_creation(self):
        """Test contact creation with only required fields"""
        contact = Contact.objects.create(
            user=self.user,
            name="Jane Smith"
        )
        
        self.assertEqual(contact.name, "Jane Smith")
        self.assertEqual(contact.get_role_display(), "Hiring Manager")  # default
        self.assertIsNone(contact.company)
        self.assertIsNone(contact.email)
        self.assertIsNone(contact.phone)
        self.assertEqual(contact.notes, "")

    def test_string_representation(self):
        """Test the string representation of contacts"""
        # With company
        contact1 = Contact.objects.create(
            user=self.user,
            name="John Doe",
            company="Test Corp",
            role="recruiter"
        )
        self.assertEqual(str(contact1), "John Doe (Recruiter at Test Corp)")

        # Without company
        contact2 = Contact.objects.create(
            user=self.user,
            name="Jane Smith",
            role="reference"
        )
        self.assertEqual(str(contact2), "Jane Smith (Reference)")

    def test_email_uniqueness(self):
        """Test email uniqueness constraints"""
        # Create first contact with email
        Contact.objects.create(
            user=self.user,
            name="John Doe",
            email="john@test.com"
        )

        # Try to create another contact with same email for same user
        with self.assertRaises(IntegrityError):
            Contact.objects.create(
                user=self.user,
                name="Different Name",
                email="john@test.com"
            )

        # Should allow same email for different user
        Contact.objects.create(
            user=self.other_user,
            name="John Doe",
            email="john@test.com"
        )

        # Should allow multiple contacts with no email
        Contact.objects.create(
            user=self.user,
            name="No Email 1"
        )
        Contact.objects.create(
            user=self.user,
            name="No Email 2"
        )

    def test_phone_uniqueness(self):
        """Test phone uniqueness constraints"""
        # Create first contact with phone
        Contact.objects.create(
            user=self.user,
            name="John Doe",
            phone="123-456-7890"
        )

        # Try to create another contact with same phone for same user
        with self.assertRaises(IntegrityError):
            Contact.objects.create(
                user=self.user,
                name="Different Name",
                phone="123-456-7890"
            )

        # Should allow same phone for different user
        Contact.objects.create(
            user=self.other_user,
            name="John Doe",
            phone="123-456-7890"
        )

        # Should allow multiple contacts with no phone
        Contact.objects.create(
            user=self.user,
            name="No Phone 1"
        )
        Contact.objects.create(
            user=self.user,
            name="No Phone 2"
        )

    def test_ordering(self):
        """Test contacts are ordered by name"""
        Contact.objects.create(user=self.user, name="Charlie")
        Contact.objects.create(user=self.user, name="Alice")
        Contact.objects.create(user=self.user, name="Bob")

        contacts = Contact.objects.all()
        self.assertEqual(contacts[0].name, "Alice")
        self.assertEqual(contacts[1].name, "Bob")
        self.assertEqual(contacts[2].name, "Charlie")
