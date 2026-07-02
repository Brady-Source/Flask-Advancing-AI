import unittest
import time

from app import create_app, db
from app.models import User, Role, Permission


class BaseTestCase(unittest.TestCase):
    """Common setup/teardown for tests."""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


class TokenExpirationTestCase(BaseTestCase):
    """Auth token and security token tests."""

    def test_auth_token_expires(self):
        # Create a test user directly — bypasses Google OAuth
        u = User(username='testuser', email='test@example.com', confirmed=True)
        db.session.add(u)
        db.session.commit()

        # Generate a very short-lived token (5 seconds)
        token = u.generate_auth_token(expiration=5)
        self.assertIsNotNone(token, "Token should be generated successfully")

        # Token should verify immediately
        verified = User.verify_auth_token(token, expiration=5)
        self.assertIsNotNone(verified, "Token should be valid immediately after generation")
        self.assertEqual(verified.id, u.id, "Token should resolve to the correct user")

        # Wait for expiration
        time.sleep(6)

        # Token should now be expired
        expired = User.verify_auth_token(token, expiration=5)
        self.assertIsNone(expired, "Token should return None after expiration")

    def test_auth_token_generates_for_valid_user(self):
        u = User(username='tokenuser', email='token@example.com', confirmed=True)
        db.session.add(u)
        db.session.commit()

        token = u.generate_auth_token(expiration=3600)
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)

    def test_invalid_auth_token_returns_none(self):
        result = User.verify_auth_token('this.is.not.a.real.token')
        self.assertIsNone(result, "A garbage token should return None")

    def test_confirmation_token(self):
        u = User(username='confirmuser', email='confirm@example.com')
        db.session.add(u)
        db.session.commit()

        token = u.generate_confirmation_token()
        self.assertFalse(u.confirmed)
        ok = u.confirm(token)
        self.assertTrue(ok, "Valid confirmation token should return True")
        self.assertTrue(u.confirmed)

    def test_reset_password_token(self):
        u = User(username='resetuser', email='reset@example.com')
        u.password = 'oldpassword'
        db.session.add(u)
        db.session.commit()

        token = u.generate_reset_token()
        self.assertTrue(User.reset_password(token, 'newpassword'))
        self.assertTrue(u.verify_password('newpassword'))

    def test_change_email_token(self):
        u = User(username='changeuser', email='old@example.com')
        db.session.add(u)
        db.session.commit()

        token = u.generate_email_change_token('new@example.com')
        changed = u.change_email(token)
        self.assertTrue(changed)
        self.assertEqual(u.email, 'new@example.com')


class PasswordHashingTestCase(BaseTestCase):
    """Password hash + salt behavior."""

    def test_password_hash_and_salt(self):
        u1 = User(username='user1', email='u1@example.com')
        u1.password = 'catdog'
        u2 = User(username='user2', email='u2@example.com')
        u2.password = 'catdog'
        db.session.add_all([u1, u2])
        db.session.commit()

        # Same password, but different salts -> different hashes
        self.assertNotEqual(u1.password_salt, u2.password_salt)
        self.assertNotEqual(u1.password_hash, u2.password_hash)

        # verify_password should succeed for correct password
        self.assertTrue(u1.verify_password('catdog'))
        self.assertFalse(u1.verify_password('wrong'))


class ApplicantUserTestCase(BaseTestCase):
    """Applicant User account tests."""

    def test_applicant_role_exists(self):
        role = Role.query.filter_by(name='Applicant User').first()
        self.assertIsNotNone(role, "Applicant User role must exist after insert_roles()")

    def test_applicant_role_permissions(self):
        role = Role.query.filter_by(name='Applicant User').first()

        # Applicant User should only have FOLLOW
        self.assertTrue(role.has_permission(Permission.FOLLOW))
        self.assertFalse(role.has_permission(Permission.COMMENT))
        self.assertFalse(role.has_permission(Permission.WRITE))
        self.assertFalse(role.has_permission(Permission.MODERATE))
        self.assertFalse(role.has_permission(Permission.ADMIN))

    def test_applicant_user_account(self):
        role = Role.query.filter_by(name='Applicant User').first()
        u = User(
            username='applicant1',
            email='applicant@example.com',
            confirmed=True,
            role=role
        )
        db.session.add(u)
        db.session.commit()

        # Confirm role was assigned
        self.assertEqual(u.role.name, 'Applicant User')

        # Can follow but nothing else
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertFalse(u.can(Permission.COMMENT))
        self.assertFalse(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.is_administrator())

    def test_applicant_is_not_admin(self):
        role = Role.query.filter_by(name='Applicant User').first()
        u = User(
            username='applicant2',
            email='applicant2@example.com',
            confirmed=True,
            role=role
        )
        db.session.add(u)
        db.session.commit()
        self.assertFalse(u.is_administrator())

    def test_applicant_token_generation(self):
        role = Role.query.filter_by(name='Applicant User').first()
        u = User(
            username='applicant3',
            email='applicant3@example.com',
            confirmed=True,
            role=role
        )
        db.session.add(u)
        db.session.commit()

        # Applicant users can still generate API tokens
        token = u.generate_auth_token(expiration=3600)
        self.assertIsNotNone(token)

        verified = User.verify_auth_token(token)
        self.assertIsNotNone(verified)
        self.assertEqual(verified.id, u.id)

    def test_applicant_api_access(self):
        role = Role.query.filter_by(name='Applicant User').first()
        u = User(
            username='applicant4',
            email='applicant4@example.com',
            confirmed=True,
            role=role
        )
        db.session.add(u)
        db.session.commit()

        token = u.generate_auth_token(expiration=3600)
        response = self.client.get(
            f'/api/v1/users/{u.id}',
            headers={'Authorization': f'Bearer {token}'}
        )

        # Should return 200 — reading own profile is allowed
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()