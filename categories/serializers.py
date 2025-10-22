from rest_framework import serializers
from .models import Category, SubCategory, Skill, FreelancerCategory, CategoryMetric, CategoryNotificationPreference

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'

class SubCategorySerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    class Meta:
        model = SubCategory
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)
    class Meta:
        model = Category
        fields = '__all__'

class FreelancerCategorySerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    class Meta:
        model = FreelancerCategory
        fields = '__all__'
        read_only_fields = ('verified','verification_meta','created_at')

class CategoryMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryMetric
        fields = '__all__'

class CategoryNotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNotificationPreference
        fields = '__all__'
        read_only_fields = ('last_sent',)
