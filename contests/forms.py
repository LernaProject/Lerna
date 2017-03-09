from django import forms

from core.models import ProblemInContest, Clarification, Compiler


class SubmitForm(forms.Form):
    def __init__(self, contest, *args, **kwargs):
        super().__init__(*args, **kwargs)

        compilers = (
            Compiler
            .objects
            .filter(obsolete=False)
            .only('name')
            .order_by('name')
        )
        self.fields['compiler'] = forms.ChoiceField(
            choices=[(compiler.id, compiler.name) for compiler in compilers]
        )
        for compiler in compilers:
            if 'C++' in compiler.name:  # Rather sensible default.
                self.initial['compiler'] = compiler.id
                break

        pics = (
            ProblemInContest
            .objects
            .filter(contest=contest)
            .select_related('problem')
            .only('number', 'problem__name')
            .order_by('number')
        )
        self.fields['problem'] = forms.ChoiceField(
            choices=[(pic.id, '%d. %s' % (pic.number, pic.problem.name)) for pic in pics],
        )

        self.fields['source'] = forms.CharField(widget=forms.Textarea)


class ClarificationForm(forms.Form):
    question = forms.CharField(widget=forms.Textarea)

    def ask(self, user, contest):
        return Clarification.objects.create(
            contest=contest,
            user=user,
            question=self.cleaned_data['question'],
        )
