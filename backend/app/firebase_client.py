import firebase_admin
from firebase_admin import credentials, auth, db, firestore
from app.core.config import settings


class FirebaseClient:
    """Singleton Firebase Admin client"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize()
            self.__class__._initialized = True

    def _initialize(self):
        """Initialize Firebase Admin SDK"""
        cred = credentials.Certificate(settings.firebase_credentials)
        firebase_admin.initialize_app(
            cred,
            {
                'databaseURL': settings.FIREBASE_DATABASE_URL
            }
        )

    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify Firebase ID token and return decoded token"""
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")

    @staticmethod
    def get_database_ref(path: str = '/'):
        """Get Firebase Realtime Database reference (LEGACY - use Firestore instead)"""
        return db.reference(path)

    @staticmethod
    def get_firestore():
        """Get Firestore client"""
        return firestore.client()

    @staticmethod
    def get_user(uid: str):
        """Get user by UID"""
        return auth.get_user(uid)

    @staticmethod
    def create_user(email: str, password: str, display_name: str = None):
        """Create a new user"""
        return auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )

    @staticmethod
    def update_user(uid: str, **kwargs):
        """Update user properties"""
        return auth.update_user(uid, **kwargs)

    @staticmethod
    def delete_user(uid: str):
        """Delete a user"""
        return auth.delete_user(uid)

    @staticmethod
    def generate_password_reset_link(email: str, action_code_settings=None):
        """
        Generate a password reset link for a user.
        This link can be sent via email to allow the user to set their password.
        """
        try:
            link = auth.generate_password_reset_link(email, action_code_settings)
            return link
        except Exception as e:
            raise ValueError(f"Failed to generate password reset link: {str(e)}")

    @staticmethod
    def send_password_reset_email(email: str):
        """
        Trigger Firebase to send a password reset email to the user.
        Note: This requires Firebase Auth email templates to be configured in Firebase Console.
        """
        try:
            # Firebase Admin SDK doesn't have a direct method to send emails
            # You need to use the client SDK or generate a link and send it yourself
            # For now, we'll generate the link that can be sent via custom email
            link = auth.generate_password_reset_link(email)
            return link
        except Exception as e:
            raise ValueError(f"Failed to send password reset email: {str(e)}")


# Initialize Firebase client
firebase_client = FirebaseClient()
