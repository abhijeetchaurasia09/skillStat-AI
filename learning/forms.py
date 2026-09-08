from django import forms
from .models import LearningMaterial
from competency.models import Skill

class PDFUploadForm(forms.ModelForm):
    class Meta:
        model = LearningMaterial
        fields = ['title', 'skill', 'course', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., MoSPI Sampling Methodology Guidebook'}),
            'skill': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,application/pdf'}),
        }

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')
        if uploaded_file:
            if not uploaded_file.name.lower().endswith('.pdf'):
                raise forms.ValidationError("Invalid file type. Only PDF documents (.pdf) are permitted.")
            # 20MB limit
            if uploaded_file.size > 20 * 1024 * 1024:
                raise forms.ValidationError("File size exceeds the 20MB maximum limit.")
        return uploaded_file
