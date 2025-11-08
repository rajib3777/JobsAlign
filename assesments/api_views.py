from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Test, Attempt
from .serializers import TestSerializer, AttemptSerializer, SubmitAnswersSerializer
from .permissions import IsFreelancer
from .throttles import AssessmentsBurstThrottle, AssessmentsSustainedThrottle
from .utils import shuffled_questions, grade_attempt_server_side
from accounts.utils import calculate_profile_completion

class EnglishTestInfoView(APIView):
    
    permission_classes = [IsAuthenticated, IsFreelancer]
    throttle_classes = [AssessmentsBurstThrottle, AssessmentsSustainedThrottle]

    def get(self, request):
        t = Test.objects.filter(type='english', active=True).first()
        if not t:
            return Response({"detail":"No English test found. Contact support."}, status=404)
        return Response(TestSerializer(t).data, status=200)


class StartTestView(APIView):
    
    permission_classes = [IsAuthenticated, IsFreelancer]
    throttle_classes = [AssessmentsBurstThrottle, AssessmentsSustainedThrottle]

    def post(self, request, test_id):
        test = get_object_or_404(Test, id=test_id, active=True)

        # enforce attempt limit
        used = Attempt.objects.filter(user=request.user, test=test).count()
        if used >= test.max_attempts:
            raise ValidationError("Maximum attempts reached for this test.")

        attempt_no = used + 1
        attempt = Attempt.objects.create(
            user=request.user, test=test, attempt_no=attempt_no,
            client_ip=request.META.get('REMOTE_ADDR'), user_agent=request.META.get('HTTP_USER_AGENT')
        )

        questions = shuffled_questions(test) if test.randomize else list(test.questions.values('id','text','options'))
        return Response({
            "attempt_id": str(attempt.id),
            "attempt_no": attempt_no,
            "time_limit_sec": test.time_limit_sec,
            "questions": questions
        }, status=200)


class SubmitAnswersView(APIView):
    
    permission_classes = [IsAuthenticated, IsFreelancer]
    throttle_classes = [AssessmentsBurstThrottle, AssessmentsSustainedThrottle]

    def post(self, request, test_id):
        test = get_object_or_404(Test, id=test_id, active=True)
        s = SubmitAnswersSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        attempt = get_object_or_404(Attempt, id=data['attempt_id'], user=request.user, test=test)
        if attempt.status in ('submitted','graded','invalid'):
            raise ValidationError("This attempt is already finished.")

        with transaction.atomic():
            graded = grade_attempt_server_side(attempt, data['answers'])

            changed = False
            # only if passed, flip flags
            if test.type == 'english' and graded.passed and not request.user.has_passed_basic_english_test:
                request.user.has_passed_basic_english_test = True
                changed = True
            if test.type == 'skill' and graded.passed and not request.user.has_passed_category_test:
                request.user.has_passed_category_test = True
                changed = True
            if changed:
                request.user.save(update_fields=['has_passed_basic_english_test','has_passed_category_test'])

            # recompute profile % (75 + english 5 + skill 10 + video 10)
            calculate_profile_completion(request.user)

        return Response({
            "attempt": AttemptSerializer(graded).data,
            "message": "Graded successfully",
        }, status=200)

