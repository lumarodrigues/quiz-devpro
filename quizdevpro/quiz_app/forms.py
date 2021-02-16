from django.forms import ModelForm

from quizdevpro.quiz_app.models import Aluno


class AlunoForm(ModelForm):
    class Meta:
        model = Aluno
        fields = ['nome', 'email']
