from django.shortcuts import render, redirect
from django.db.models import Sum
from django.utils.timezone import now

from quizdevpro.quiz_app.forms import AlunoForm
from quizdevpro.quiz_app.models import Pergunta, Aluno, Resposta


def indice(requisicao):
    if requisicao.method == 'POST':
        # Email da requisicao
        email = requisicao.POST['email']
        # Busca se este email existe no banco de dados
        try:
            aluno = Aluno.objects.get(email=email)
        # Se o email nao existir, valida os dados e salva no banco, redirecionando para as perguntas depois
        except Aluno.DoesNotExist:
            form = AlunoForm(requisicao.POST)
            if form.is_valid():
                aluno = form.save()
                requisicao.session['aluno_id'] = aluno.id
                return redirect('/perguntas/1')

            # Se os dados nao forem validos, retorna para a pagina inicial, com os dados sendo mostrados e os erros
            contexto = {'form': form}
            return render(requisicao, 'quiz_app/indice.html', contexto)
        # Se o aluno ja existir no banco, o id sera salvo e o usuario redirecionado para as perguntas
        else:
            requisicao.session['aluno_id'] = aluno.id
            return redirect('/perguntas/1')

    return render(requisicao, 'quiz_app/indice.html')


def perguntas(requisicao, indice):
    aluno_id = requisicao.session['aluno_id']
    try:
        pergunta = Pergunta.objects.filter(disponivel=True).order_by('id')[indice - 1]
    except IndexError:
        redirect('/fim')
    else:
        contexto = {'indice': indice, 'pergunta': pergunta}
        if requisicao.method == 'POST':
            alternativa_escolhida = int(requisicao.POST['alternativa'])

            if alternativa_escolhida == pergunta.alternativa_correta:

                try:
                    primeira = Resposta.objects.filter(pergunta=pergunta).order_by('criacao')[0]
                except IndexError:
                    pontos = 100
                else:
                    tempo_primeira_resposta = primeira.criacao
                    diferenca = now() - tempo_primeira_resposta
                    pontos = 100 - int(diferenca.total_seconds())
                    pontos = max(pontos, 1)

                Resposta(aluno_id=aluno_id, pergunta=pergunta, pontos=pontos).save()
                return redirect(f'/perguntas/{indice + 1}')
            contexto['alternativa_escolhida'] = alternativa_escolhida

        return render(requisicao, 'quiz_app/perguntas.html', contexto)


def fim(requisicao):
    aluno_id = requisicao.session['aluno_id']
    dct = Resposta.objects.filter(aluno_id=aluno_id).aggregate(Sum(pontos))
    pontos_aluno = dct['pontos__sum']

    aluno_com_pontuacao_maior = Resposta.objects.values('aluno').annotate(Sum(pontos)).filter(pontos__sum__gt=pontos_aluno).count()

    primeiros_5_alunos = Resposta.objects.values('aluno', 'aluno__nome').annotate(Sum(pontos)).order_by('-pontos__sum')[:5]

    contexto = {'pontos': pontos_aluno, 'posicao': aluno_com_pontuacao_maior + 1, 'primeiros_5_alunos': primeiros_5_alunos}

    return render(requisicao, 'quiz_app/fim.html', contexto)
