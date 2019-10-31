from django import forms


class FileUploadForm(forms.Form):
    platform = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Platform",}))
    activity = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Activity"}))
    list_of_vars = forms.CharField(max_length=500, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "List of Variables..."}), required=False)
    AEM = forms.FileField()
    NONAEM = forms.FileField()
