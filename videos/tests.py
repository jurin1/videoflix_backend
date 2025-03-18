from django.test import TestCase
from django.contrib.auth import get_user_model
from videos.models import Video, VideoViewing

User = get_user_model()

class VideoViewingModelTest(TestCase):
    """
    Test suite for the VideoViewing model.

    This class contains tests to verify the functionality of the VideoViewing model,
    including creation, unique constraints, string representation, and default values
    of its fields.
    """

    def setUp(self):
        """
        Set up method to create a test user and a test video.

        This method is executed before each test method in this class.
        It creates a user and a video instance that are used across the test methods.
        """
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com')
        self.video = Video.objects.create(title='Test Video')

    def test_create_video_viewing(self):
        """
        Tests the creation of a VideoViewing object.

        This test ensures that a VideoViewing instance can be created and that
        its attributes are correctly set to the provided user and video, and
        default values for watched_duration and is_finished.
        """
        viewing = VideoViewing.objects.create(user=self.user, video=self.video)
        self.assertEqual(viewing.user, self.user)
        self.assertEqual(viewing.video, self.video)
        self.assertEqual(viewing.watched_duration, 0.0)
        self.assertFalse(viewing.is_finished)

    def test_unique_user_video_constraint(self):
        """
        Tests the unique_together constraint for user and video.

        This test verifies that attempting to create a second VideoViewing instance
        with the same user and video raises an exception, enforcing the
        unique_together constraint defined in the model.
        """
        VideoViewing.objects.create(user=self.user, video=self.video)
        with self.assertRaises(Exception):
            VideoViewing.objects.create(user=self.user, video=self.video)

    def test_video_viewing_str_representation(self):
        """
        Tests the __str__ representation of the VideoViewing model.

        This test checks that the string representation of a VideoViewing instance
        correctly includes the username, video title, and viewing timestamp,
        providing a human-readable string for object identification.
        """
        viewing = VideoViewing.objects.create(user=self.user, video=self.video)
        expected_str = f"{self.user.username} viewed {self.video.title} at {viewing.viewed_at.strftime('%Y-%m-%d %H:%M:%S')}"
        self.assertTrue(expected_str in str(viewing))


    def test_watched_duration_default_value(self):
        """
        Tests if watched_duration defaults to 0.0.

        This test confirms that when a VideoViewing instance is created without
        explicitly setting the watched_duration, it defaults to 0.0 as defined in the model.
        """
        viewing = VideoViewing.objects.create(user=self.user, video=self.video)
        self.assertEqual(viewing.watched_duration, 0.0)

    def test_is_finished_default_value(self):
        """
        Tests if is_finished defaults to False.

        This test ensures that the is_finished field of a newly created VideoViewing
        instance is set to False by default, indicating that the video is not finished
        upon initial viewing.
        """
        viewing = VideoViewing.objects.create(user=self.user, video=self.video)
        self.assertFalse(viewing.is_finished)