from django.shortcuts     import render
from django.views.generic import TemplateView
from django               import forms
from users.models         import User
from django.contrib.auth  import authenticate, login

class RegistrationForm(forms.Form):
    login    = forms.CharField(label='login', max_length=255)
    email    = forms.EmailField(label='email', max_length=255)
    password = forms.CharField(label='password',max_length=255,widget=forms.PasswordInput)

class Registration(TemplateView):
    form_class = RegistrationForm
    template_name = 'users/registration.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            User.objects.create_user(form.cleaned_data['login'], form.cleaned_data['email'], form.cleaned_data['password'])
            user = authenticate(username=form.cleaned_data['login'], password=form.cleaned_data['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
        return render(request, self.template_name, {'form': form})