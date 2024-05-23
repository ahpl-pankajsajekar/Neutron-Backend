from rest_framework import serializers
import base64

class DCSerializer(serializers.Serializer):
    pass

class EmpanelmentSerializer(serializers.Serializer):
    pass
    
class SelfEmpanelmentSerializer(serializers.Serializer):
    isConfirmCheckbox = serializers.BooleanField(default=False)
    providerType = serializers.CharField(max_length=100)
    providerName = serializers.CharField(max_length=250)
    Regi_number = serializers.CharField(max_length=250)
    Owner_name = serializers.CharField(max_length=250)
    PanCard_number = serializers.CharField(max_length=250)
    address1 = serializers.CharField(max_length=250)
    pincode = serializers.CharField(max_length=20)
    emailId = serializers.EmailField()
    accountNumber = serializers.CharField(max_length=50)
    accountName = serializers.CharField(max_length=100)
    ifscCode = serializers.CharField(max_length=50)
    FirmType = serializers.CharField(max_length=100)
    pan_image = serializers.ImageField()
    dateOnStampPaper = serializers.DateField()
    # pass

class SelfEmpanelmentVerificationSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=180)
    DCVerificationStatus = serializers.CharField(max_length=180)
    
class SelfEmpanelmentVerificationbyLegalSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=180)
    DCVerificationStatusByLegal = serializers.CharField(max_length=180)

# Change DC Status
class DCStatusChangeSerializer(serializers.Serializer):
    DCStatus = serializers.CharField(max_length=250)


# send for docusign not using 
class docusignAgreementFileSerializer(serializers.Serializer):
    agreement_file = serializers.FileField(required=True)
    id = serializers.CharField(max_length=50, required=True)  # self empanelment ID

    def validate(self, instance):
        data = super().to_representation(instance)
        # Read the file content
        file_content = instance['agreement_file'].read()

        # Convert file content to base64
        base64_content = base64.b64encode(file_content).decode('utf-8')
        file_extension = instance['agreement_file'].name.split('.')[-1]
        file_name = instance['agreement_file'].name
        file_size = instance['agreement_file'].size

        # Add base64 content, file extension, file name, and file size to the representation
        data['base64_content'] = base64_content
        data['file_extension'] = file_extension
        data['file_name'] = file_name
        data['file_size'] = file_size

        return data


class candidateDCFormSerializer(serializers.Serializer):
    providerName = serializers.CharField(max_length=250)
    providerType = serializers.CharField(max_length=100)
    Owner_name = serializers.CharField(max_length=250)
    address1 = serializers.CharField(max_length=500)
    address2 = serializers.CharField(max_length=500)
    pincode = serializers.CharField(max_length=20)
    state = serializers.CharField(max_length=50)
    city = serializers.CharField(max_length=50)
    contactName = serializers.CharField(max_length=250)
    contactEmailId = serializers.EmailField()
    contactMobileNumber = serializers.CharField(max_length=20)
    # pass
    