from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, ProjectAttachment, Bid, Contract, Milestone, Skill, ProjectActivityLog
from .models import Portfolio

User = get_user_model()

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ("id", "name", "slug")


class ProjectAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAttachment
        fields = ("id", "name", "file", "uploaded_at")


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    attachments = ProjectAttachmentSerializer(many=True, read_only=True)
    recommended_freelancers = serializers.JSONField(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id","owner","title","description","budget_min","budget_max",
            "currency","skills","is_featured","status","created_at","updated_at",
            "recommended_freelancers","recommended_score","view_count","attachments"
        ]
        read_only_fields = ("owner","created_at","updated_at","recommended_freelancers","recommended_score","view_count")


class ProjectCreateSerializer(serializers.ModelSerializer):
    skill_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    attachments = serializers.ListField(child=serializers.FileField(), write_only=True, required=False)

    class Meta:
        model = Project
        fields = ("title","description","budget_min","budget_max","currency","skill_ids","attachments","is_featured")

    def create(self, validated_data):
        skill_ids = validated_data.pop("skill_ids", [])
        attachments = validated_data.pop("attachments", [])
        user = self.context["request"].user
        project = Project.objects.create(owner=user, **validated_data)
        if skill_ids:
            skills = Skill.objects.filter(id__in=skill_ids)
            project.skills.set(skills)
        for f in attachments:
            ProjectAttachment.objects.create(project=project, file=f, name=getattr(f, "name", None))
        return project


class BidSerializer(serializers.ModelSerializer):
    freelancer = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Bid
        fields = ("id","project","freelancer","amount","delivery_days","cover_letter","suggested_by_ai","status","created_at")
        read_only_fields = ("freelancer","status","created_at")


class BidCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bid
        fields = ("project","amount","delivery_days","cover_letter")

    def validate(self, attrs):
        user = self.context["request"].user
        project = attrs["project"]
        if project.owner == user:
            raise serializers.ValidationError("Owner cannot bid on own project.")
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        bid = Bid.objects.create(freelancer=user, **validated_data)
        return bid


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = "__all__"
        read_only_fields = ("id","created_at","updated_at")


class ContractSerializer(serializers.ModelSerializer):
    buyer = serializers.StringRelatedField(read_only=True)
    freelancer = serializers.StringRelatedField(read_only=True)
    project = ProjectSerializer(read_only=True)

    class Meta:
        model = Contract
        fields = "__all__"
        read_only_fields = ("id","buyer","freelancer","started_at","escrow_reference")




class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = "__all__"
        read_only_fields = ["user", "created_at"]


def validate(self, attrs):
    user = self.context['request'].user
    if user.profile_completion_score < 80:
        raise serializers.ValidationError("Your profile must be 80% complete to place a bid.")
    return attrs