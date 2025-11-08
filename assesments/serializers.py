from rest_framework import serializers
from .models import Test, Question, Attempt

class QuestionPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id','text','options']

class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ['id','name','type','total_marks','pass_marks','weight','time_limit_sec','randomize','active','max_attempts']

class AttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt
        fields = ['id','attempt_no','status','started_at','finished_at','duration_sec','score','percent_cached','passed']

class SubmitAnswersSerializer(serializers.Serializer):
    attempt_id = serializers.UUIDField()
    answers = serializers.DictField(child=serializers.CharField(), allow_empty=False)
