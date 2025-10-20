from rest_framework import serializers
from .models import ProjectRecommendation, UserRecommendation

class RecommendationItemSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=False)
    project_id = serializers.UUIDField(required=False)
    score = serializers.FloatField()
    reason = serializers.CharField(required=False, allow_blank=True)

class ProjectRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectRecommendation
        fields = '__all__'
        read_only_fields = ('id','computed_at')

class UserRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRecommendation
        fields = '__all__'
        read_only_fields = ('id','computed_at')
