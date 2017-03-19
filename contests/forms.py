from django                 import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator

from core.models import Attempt, Clarification


class ModelListChoiceField(forms.ChoiceField):
    def __init__(self, objects, *args, **kwargs):
        super().__init__(
            choices=[(obj.pk, self.label_from_instance(obj)) for obj in objects],
            *args, **kwargs
        )
        self.objects = { obj.pk: obj for obj in objects }

    def label_from_instance(self, obj):
        return str(obj)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            return self.objects[type(next(iter(self.objects)))(value)]
        except (StopIteration, ValueError, KeyError):
            raise ValidationError(
                self.error_messages['invalid_choice'],
                params={'value': value},
                code='invalid',
            )

    def validate(self, value):
        super().validate(None if value is None else value.pk)


class PICChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, pic):
        return '{0.letter}. {0.problem.name}'.format(pic)


class BytesMaxLengthValidator(MaxLengthValidator):
    def clean(self, s):
        return len(s.encode())


class SubmitForm(forms.Form):
    def __init__(self, compilers, pics, initial_compiler, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields.update([
            ('compiler', ModelListChoiceField(
                compilers,
                initial=initial_compiler,
                label='Компилятор',
            )),
            ('problem', PICChoiceField(queryset=pics, empty_label=None, label='Задача')),
            ('source', forms.CharField(
                max_length=65536,
                validators=[BytesMaxLengthValidator(65536)],
                widget=forms.Textarea,
                label='Код',
            )),
            # TODO: Allow uploading a source file.
        ])

    def submit(self, user):
        return Attempt.objects.create(
            user=user,
            compiler=self.cleaned_data['compiler'],
            problem_in_contest=self.cleaned_data['problem'],
            source=self.cleaned_data['source'],
        )


class ClarificationForm(forms.Form):
    question = forms.CharField(widget=forms.Textarea)

    def ask(self, user, contest):
        return Clarification.objects.create(
            contest=contest,
            user=user,
            question=self.cleaned_data['question'],
        )
