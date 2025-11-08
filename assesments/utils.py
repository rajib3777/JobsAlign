import random
from django.utils import timezone

def shuffled_questions(test):
    qs = list(test.questions.values('id','text','options'))
    random.shuffle(qs)
    return qs

def grade_attempt_server_side(attempt, answers_dict):
    test = attempt.test
    correct = 0
    total = test.questions.count()

    # persist answers + correctness
    for q in test.questions.all():
        chosen = str(answers_dict.get(str(q.id)) or answers_dict.get(q.id) or '').strip()
        ok = chosen == q.correct_answer
        attempt.answers.update_or_create(question=q, defaults={'chosen': chosen, 'is_correct': ok})
        if ok:
            correct += 1

    attempt.finished_at = timezone.now()
    attempt.duration_sec = int((attempt.finished_at - attempt.started_at).total_seconds())

    # time-limit enforcement
    if attempt.duration_sec > test.time_limit_sec:
        attempt.mark_invalid('time_limit_exceeded')
        attempt.score = 0.0
        attempt.percent_cached = 0.0
        attempt.passed = False
        attempt.save(update_fields=['finished_at','duration_sec','score','percent_cached','passed'])
        return attempt

    # score & pass
    attempt.status = 'graded'
    attempt.score = (correct / max(1,total)) * test.total_marks
    attempt.passed = attempt.score >= test.pass_marks
    # contribution to profile (weight) — english=5.0
    attempt.percent_cached = round((attempt.score / test.total_marks) * test.weight, 2)
    attempt.save(update_fields=['finished_at','duration_sec','status','score','passed','percent_cached'])
    return attempt
