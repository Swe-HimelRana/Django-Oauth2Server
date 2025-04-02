from django import forms
from django.contrib.auth.forms import AuthenticationForm

class OAuthLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add hidden fields for OAuth parameters
        self.fields['client_id'] = forms.CharField(
            widget=forms.HiddenInput(),
            required=False
        )
        self.fields['redirect_uri'] = forms.CharField(
            widget=forms.HiddenInput(),
            required=False
        )
        self.fields['state'] = forms.CharField(
            widget=forms.HiddenInput(),
            required=False
        )