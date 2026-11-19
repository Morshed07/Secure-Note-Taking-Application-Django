from rest_framework import serializers

class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(min_length=6, write_only=True, required=True)
    role = serializers.ChoiceField(choices=['user', 'admin'], default='user')
    interests = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list
    )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False)
    role = serializers.ChoiceField(choices=['user', 'admin'], required=False)
    interests = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False
    )
