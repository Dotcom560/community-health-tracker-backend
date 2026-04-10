from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, SymptomLog, TriageResult, 
    Medication, MedicationRecommendation, OutbreakAlert
)

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.USER_ROLES, default='patient')
    phone_number = serializers.CharField(required=False, allow_blank=True)
    region = serializers.CharField(required=False, allow_blank=True)
    age_group = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 
                  'role', 'phone_number', 'region', 'age_group']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        # Remove profile fields from user data
        role = validated_data.pop('role', 'patient')
        phone_number = validated_data.pop('phone_number', '')
        region = validated_data.pop('region', '')
        age_group = validated_data.pop('age_group', '')
        validated_data.pop('password_confirm', None)
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        
        # Create profile
        UserProfile.objects.create(
            user=user,
            role=role,
            phone_number=phone_number,
            region=region,
            age_group=age_group
        )
        
        return user

class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']
    
    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'role': profile.role,
                'phone_number': profile.phone_number,
                'region': profile.region,
                'age_group': profile.age_group,
            }
        except UserProfile.DoesNotExist:
            return None

class SymptomLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = SymptomLog
        fields = '__all__'
        read_only_fields = ['user', 'user_id', 'created_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'

class MedicationRecommendationSerializer(serializers.ModelSerializer):
    medication_details = MedicationSerializer(source='medication', read_only=True)
    
    class Meta:
        model = MedicationRecommendation
        fields = ['id', 'medication', 'medication_details', 'notes', 'created_at']

class TriageResultSerializer(serializers.ModelSerializer):
    symptom_log_details = SymptomLogSerializer(source='symptom_log', read_only=True)
    medication_recommendations = MedicationRecommendationSerializer(
        source='medication_recommendations', 
        many=True, 
        read_only=True
    )
    
    class Meta:
        model = TriageResult
        fields = '__all__'
        read_only_fields = ['created_at']

class OutbreakAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutbreakAlert
        fields = '__all__'