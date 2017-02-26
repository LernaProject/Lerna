from django.shortcuts     import render, redirect
from django.views.generic import View, TemplateView
from django               import forms
from users.models         import User
from django.contrib.auth  import authenticate, login, logout


class RegistrationForm(forms.Form):
    login    = forms.CharField(label='Логин', max_length=255)
    username = forms.CharField(label='Отображаемое имя', max_length=255)
    email    = forms.EmailField(label='E-mail', max_length=255)
    password = forms.CharField(label='Пароль', max_length=255, widget=forms.PasswordInput)


class Registration(TemplateView):
    form_class = RegistrationForm
    template_name = 'users/registration.html'

    def get(self, request, *args, **kwargs):
        request.session['back'] = request.GET.get('back', '/')
        return render(request, self.template_name, {'form': self.form_class()})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        back = request.session['back']
        if form.is_valid():
            user_login = form.cleaned_data['login']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            User.objects.create_user(user_login, username, password, email)
            user = authenticate(username=user_login, password=password)
            if user is not None and user.is_active:
                login(request, user)
                return redirect(back)

        return render(request, self.template_name, {'form': form})


class LoginForm(forms.Form):
    login    = forms.CharField(label='Логин', max_length=255)
    password = forms.CharField(label='Пароль', max_length=255, widget=forms.PasswordInput)


class Login(TemplateView):
    form_class = LoginForm
    template_name = 'users/login.html'

    def get(self, request, *args, **kwargs):
        request.session['next'] = request.GET.get('next', '/')
        return render(request, self.template_name, {'form': self.form_class()})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        next = request.session['next']
        if form.is_valid():
            user_login = form.cleaned_data['login']
            password = form.cleaned_data['password']
            user = authenticate(username=user_login, password=password)
            if user is not None and user.is_active:
                login(request, user)
                return redirect(next)

        return render(request, self.template_name, {'form': form})


class Logout(View):
    def get(self, request, *args, **kwargs):
        back = request.GET.get('back', '/')
        logout(request)
        return redirect(back)
