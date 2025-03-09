from django.test import TestCase
from django.contrib.auth import get_user_model
from videos.models import Video, VideoViewing

User = get_user_model()

class VideoViewingModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com')
        self.video = Video.objects.create(title='Test Video')

    def test_create_video_viewing(self):
        """Testet das Erstellen eines VideoViewing-Objekts."""
        viewing = VideoViewing.objects.create(user=self.user, video=self.video)
        self.assertEqual(viewing.user, self.user)
        self.assertEqual(viewing.video, self.video)
        self.assertEqual(viewing.watched_duration, 0.0) 
        self.assertFalse(viewing.is_finished) 

    def test_unique_user_video_constraint(self):
        """Testet die unique_together Constraint für user und video."""
        VideoViewing.objects.create(user=self.user, video=self.video)
        with self.assertRaises(Exception): 
            VideoViewing.objects.create(user=self.user, video=self.video)

    def test_video_viewing_str_representation(self):
        """Testet die __str__ Repräsentation des VideoViewing Modells."""
        viewing = VideoViewing.objects.create(user=self.user, video=self.video)
        expected_str = f"{self.user.username} viewed {self.video.title} at {viewing.viewed_at.strftime('%Y-%m-%d %H:%M:%S')}" # Format anpassen falls nötig
        self.assertTrue(expected_str in str(viewing)) 


    def test_watched_duration_default_value(self):
        """Testet, ob watched_duration standardmäßig auf 0.0 gesetzt ist."""
        viewing = VideoViewing.objects.create(user=self.user, video=self.video)
        self.assertEqual(viewing.watched_duration, 0.0)

    def test_is_finished_default_value(self):
        """Testet, ob is_finished standardmäßig auf False gesetzt ist."""
        viewing = VideoViewing.objects.create(user=self.user, video=self.video)
        self.assertFalse(viewing.is_finished)