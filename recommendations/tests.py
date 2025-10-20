from django.test import TestCase
from django.contrib.auth import get_user_model
from marketplace.models import Project, Skill
from .utils import compute_candidate_score

User = get_user_model()

class RecommendationsBasicTests(TestCase):
    def setUp(self):
        self.f = User.objects.create_user(email='freelancer@example.com', full_name='F', password='pass', user_type='freelancer')
        self.f.skills = ['python','django']
        self.f.rating = 4.5
        self.f.trust_score = 80
        self.f.save()

        self.owner = User.objects.create_user(email='owner@example.com', full_name='O', password='pass', user_type='buyer')
        # create a project
        self.s1 = Skill.objects.create(name='Python', slug='python')
        self.s2 = Skill.objects.create(name='Django', slug='django')
        self.project = Project.objects.create(owner=self.owner, title='Test', description='x', budget_min=100, budget_max=200)
        self.project.skills.set([self.s1, self.s2])

    def test_score_positive(self):
        score = compute_candidate_score(self.project, self.f)
        self.assertGreater(score, 0)

