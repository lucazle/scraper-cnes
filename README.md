# Scraper CNES

Web scraper em Python que coleta estabelecimentos de saúde do
[CNES](https://cnes.datasus.gov.br/) (Cadastro Nacional de Estabelecimentos de Saúde).
Projeto da disciplina de Recuperação de Informação.

## Como funciona

O site do CNES carrega os dados por JavaScript, então o HTML da página vem vazio.
Em vez de automatizar um navegador, o scraper chama diretamente a API JSON que a
própria página usa:

1. Busca a lista de estabelecimentos de um município.
2. Para cada estabelecimento, busca o detalhe (endereço, telefone, e-mail, coordenadas).
3. Busca também os horários de funcionamento.
4. Salva tudo em um arquivo CSV.

O script visita a página antes de chamar a API, para receber os cookies de sessão,
e faz uma pausa entre as requisições para não sobrecarregar o servidor.

## Como rodar

    pip install -r requirements.txt
    python scraper.py

Por padrão coleta os estabelecimentos de Igarassu-PE (código 260680) e gera
`estabelecimentos_igarassu.csv`.
