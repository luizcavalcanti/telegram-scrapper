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

```bash
# Busca e salva no `messages.db` as últimas mensagens dos grupos/canais
$ python extract.py

# TODO
$ python manage.py extract

# Cria word count por dia
$ python count_words.py

# TODO
$ python manage.py words

# Plota gráfico sem-vergonha de aparição de termo por dia
$ python plot.py <termo>

# TODO
$ python manage.py plot <termo>
```
