# Telegram Scrapper

## Dependências

* Python 3.9
* [Pipenv](https://pipenv.pypa.io/)

## Instalação

Instale as dependências com o [Pipenv](https://pipenv.pypa.io/) e ative o ambiente virtual :

```console
$ pipenv install
$ pipenv shell
```

Crie as configurações locais com o [Createnv](https://github.com/cuducos/createnv):

```console
$ createnv
```

Execute as migrações do [Django](https://www.djangoproject.com/):

```console
$ python manage.py migrate
```

## Comandos

Busca mensagens no grupo e salva no banco de dados:

```console
$ python manage.py extract <numero de mensagens por grupo>
```

Gerar dataset de frequência de termos/palavras por dia:

```console
$ python manage.py words
```

### TODO

```bash
# Plota gráfico sem-vergonha de aparição de termo por dia
$ python plot.py <termo>

# TODO
$ python manage.py plot <termo>
```
