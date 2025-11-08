from django.core.management.base import BaseCommand
from assessments.models import Test, Question

QUESTIONS = [
    ("Choose the correct form: She ____ to school every day.", {"A":"go","B":"goes","C":"going","D":"gone"}, "B"),
    ("Find the synonym of 'rapid'.", {"A":"slow","B":"quick","C":"late","D":"dull"}, "B"),
    ("Choose the correct preposition: I will see you ___ Monday.", {"A":"in","B":"on","C":"at","D":"by"}, "B"),
    ("Fill in the blank: They ____ finished the project.", {"A":"has","B":"have","C":"had","D":"having"}, "B"),
    ("Which is correct?", {"A":"Its a good day","B":"It's a good day","C":"Its' a good day","D":"It is a good day"}, "B"),
    ("Choose the antonym of 'expand'.", {"A":"enlarge","B":"broaden","C":"contract","D":"extend"}, "C"),
    ("Identify the error: He don't like tea.", {"A":"He","B":"don't","C":"like","D":"tea"}, "B"),
    ("Choose the correct article: She is ___ honest person.", {"A":"a","B":"an","C":"the","D":"no article"}, "B"),
    ("Select the correct sentence.", {"A":"I have saw it","B":"I seen it","C":"I have seen it","D":"I am see it"}, "C"),
    ("Choose the correct word: Please ____ the lights.", {"A":"off","B":"turn off","C":"put","D":"shut"}, "B"),
]

class Command(BaseCommand):
    help = "Seed default English test with 10 MCQs"

    def handle(self, *args, **kwargs):
        test, created = Test.objects.get_or_create(
            type='english',
            defaults=dict(
                name="Basic English (Level 1)",
                total_marks=100,
                pass_marks=60,
                weight=5.0,
                time_limit_sec=900,  # 15 min
                randomize=True,
                active=True,
                max_attempts=3
            )
        )
        if not created:
            self.stdout.write(self.style.WARNING("English test already exists. Updating questions..."))

        # wipe old questions and add fresh ones
        test.questions.all().delete()
        for text, opts, corr in QUESTIONS:
            Question.objects.create(test=test, text=text, options=opts, correct_answer=corr)

        self.stdout.write(self.style.SUCCESS("Seeded English test with 10 questions."))
