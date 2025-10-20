from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Review, ReviewReply
from marketplace.models import Contract

User = get_user_model()

class ReviewSerializer(serializers.ModelSerializer):
    reviewer = serializers.StringRelatedField()
    reviewee = serializers.StringRelatedField()
    average_score = serializers.ReadOnlyField()

    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ("reviewer","reviewee","contract","created_at","updated_at")

class ReviewCreateSerializer(serializers.ModelSerializer):
    contract_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Review
        fields = ("contract_id","rating","title","comment","professionalism","communication","quality","recommended")

    def validate(self, attrs):
        user = self.context["request"].user
        try:
            contract = Contract.objects.get(id=attrs["contract_id"])
        except Contract.DoesNotExist:
            raise serializers.ValidationError("Invalid contract.")

        if contract.review.exists():
            raise serializers.ValidationError("Review already exists for this contract.")
        if user not in [contract.buyer, contract.freelancer]:
            raise serializers.ValidationError("You are not part of this contract.")
        if contract.status != "completed":
            raise serializers.ValidationError("Contract not completed yet.")
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        contract = Contract.objects.get(id=validated_data.pop("contract_id"))
        reviewee = contract.freelancer if contract.buyer == user else contract.buyer
        review = Review.objects.create(
            reviewer=user,
            reviewee=reviewee,
            contract=contract,
            **validated_data
        )
        return review

class ReviewReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewReply
        fields = ("id","review","responder","message","created_at")
        read_only_fields = ("id","responder","created_at")
