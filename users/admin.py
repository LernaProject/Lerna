from django                   import forms
from django.contrib           import admin, auth
from django.db.models         import F
from django.utils.translation import ugettext as _

from .models import User


class RightsFilter(admin.SimpleListFilter):
    title = _('rights')

    parameter_name = 'rights'

    def lookups(self, request, model_admin):
        return (
            (0x0, _('Contest users')),
            (0x1, _('Regular users')),
            (0x2, _('Moderators')),
            (0x4, _('Administrators')),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        mask = int(self.value())
        if mask == 0x0:
            # rights == rights & ~0x7
            return queryset.filter(rights=F('rights').bitand(~0x7))
        else:
            # rights == rights | mask
            return queryset.filter(rights=F('rights').bitor(mask))


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label=_('Password'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Password confirmation'), widget=forms.PasswordInput)
    invalidate_password = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = ('password1', 'password2', 'invalidate_password')

    def clean_password2(self):
        if not self.cleaned_data.get('invalidate_password'):
            password1 = self.cleaned_data.get('password1')
            password2 = self.cleaned_data.get('password2')
            if password1 != password2:
                raise forms.ValidationError(_("Passwords don't match"))
            return password1

    def save(self, commit=True):
        invalidate_password = self.cleaned_data.get('invalidate_password')
        password = self.cleaned_data.get('password1')
        if not invalidate_password and not password:
            return super().save(commit)

        user = super().save(commit=False)
        if invalidate_password:
            user.set_unusable_password()
        else:
            user.set_password(password)
        if commit:
            user.save()
        return user


class UserChangeForm(UserCreationForm):
    password = auth.forms.ReadOnlyPasswordHashField()
    password1 = forms.CharField(
        required=False, label=_('Password'), widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        required=False, label=_('Password confirmation'), widget=forms.PasswordInput
    )

    class Meta:
        fields = ('password', 'password1', 'password2', 'invalidate_password')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial['password']

    def clean_password2(self):
        if self.cleaned_data.get('password1') or self.cleaned_data.get('password2'):
            return super().clean_password2()


@admin.register(User)
class UserAdmin(auth.admin.UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    ordering = ['-id']
    list_display = ('id', 'login', 'username', 'last_login', 'created_at', 'rights')
    list_display_links = ('id', 'login', 'username')
    list_filter = (RightsFilter, 'last_login', 'created_at')
    date_hierarchy = 'created_at'
    search_fields = ('login', 'username', 'email')
    filter_horizontal = ()

    fieldsets = (
        (
            None, {
                'fields': ('login', 'username'),
            }
        ), (
            _('Security'), {
                'fields': (
                    'email', 'password', 'password1', 'password2', 'invalidate_password', 'rights',
                ),
                'classes': ['collapse'],
            }
        ), (
            _('Statistics'), {
                'fields': ('created_at', 'updated_at', 'last_login'),
            }
        ), (
            _('Rails trash'), {
                'description': _('Artifacts left from the previous framework'),
                'fields': ('password_salt', 'crypted_password', 'persistence_token'),
                'classes': ['collapse'],
            }
        ),
    )

    # `add_fieldsets` is not a standard `ModelAdmin` attribute. `auth.admin.UserAdmin`
    # overrides `get_fieldsets` to use this attribute when creating a user.
    add_fieldsets = (
        (
            None, {
                'fields': (
                    'login', 'username', 'password1', 'password2',
                    'invalidate_password', 'email', 'rights'
                ),
            }
        ), (
            _('Rails trash'), {
                'description': _('Artifacts left from the previous framework'),
                'fields': ('password_salt', 'crypted_password', 'persistence_token'),
                'classes': ['collapse'],
            }
        ),
    )


admin.site.unregister(auth.models.Group)
