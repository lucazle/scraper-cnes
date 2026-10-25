import argparse
import difflib
import time
import unicodedata
import csv
from collections import Counter

import pymysql
import requests

from banco import conectar, salvar_registro
from transformar import montar_registro

PAGINA = "https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp"
BASE = "https://cnes.datasus.gov.br/services"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": PAGINA,
}

ESTADO_PE = 26
NATUREZA_ADMIN_PUBLICA = "1"   # é aqui que ficam as UBS
PAUSA = 0.5                    # segundos entre requisições
MUNICIPIOS_PADRAO = ["Igarassu", "Goiana", "Itamaracá"]
CAMINHO_DESCARTADOS = "descartados.csv"
COLUNAS_DESCARTADOS = [
    "municipio", "cnes", "nome", "tipo", "logradouro", "numero",
    "bairro", "cep", "telefone", "latitude", "longitude", "motivo",
]


def criar_sessao():
    sessao = requests.Session()
    sessao.get(PAGINA, headers=HEADERS, timeout=30)  # pega os cookies
    return sessao


def buscar_municipios(sessao):
    """Devolve {código: nome} dos municípios de Pernambuco."""
    resposta = sessao.get(f"{BASE}/municipios", params={"estado": ESTADO_PE},
                          headers=HEADERS, timeout=30)
    resposta.raise_for_status()
    return resposta.json()


def buscar_lista(sessao, codigo_municipio, codigo_natureza=NATUREZA_ADMIN_PUBLICA):
    resposta = sessao.get(f"{BASE}/estabelecimentos",
                          params={"municipio": codigo_municipio, "natureza": codigo_natureza},
                          headers=HEADERS, timeout=30)
    resposta.raise_for_status()
    return resposta.json()


def buscar_detalhe(sessao, id_estabelecimento):
    resposta = sessao.get(f"{BASE}/estabelecimentos/{id_estabelecimento}",
                          headers=HEADERS, timeout=30)
    resposta.raise_for_status()
    return resposta.json()


def normalizar(texto):
    """MAIÚSCULAS, sem acento e sem espaços repetidos, para comparar nomes."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.upper().split())


def resolver_municipio(nome, municipios):
    """Descobre o código de um município a partir do nome digitado."""
    por_nome = {normalizar(n): (c, n) for c, n in municipios.items()}
    alvo = normalizar(nome)

    if alvo in por_nome:
        return por_nome[alvo]

    contem = [n for n in por_nome if alvo in n]
    if len(contem) == 1:
        return por_nome[contem[0]]

    sugestoes = difflib.get_close_matches(alvo, por_nome, n=3) or contem[:3]
    raise ValueError(
        f"Município '{nome}' não encontrado ou ambíguo. "
        f"Sugestões: {', '.join(sugestoes) or 'nenhuma'}"
    )

def salvar_descartados(descartados, caminho=CAMINHO_DESCARTADOS):
    """Grava os estabelecimentos descartados, para a equipe tratar depois."""
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS_DESCARTADOS)
        escritor.writeheader()
        escritor.writerows(descartados)


def coletar_municipio(sessao, conexao, codigo, nome, resumo,descartados, limite=None):
    lista = buscar_lista(sessao, codigo_municipio=codigo)
    if limite:
        lista = lista[:limite]
    print(f"\n{nome} ({codigo}): {len(lista)} estabelecimentos")

    for i, item in enumerate(lista, start=1):
        prefixo = f"[{i}/{len(lista)}]"

        try:
            detalhe = buscar_detalhe(sessao, item["id"])
        except requests.RequestException as erro:
            resumo["erro: requisição ao CNES"] += 1
            print(f"{prefixo} ERRO ao buscar {item['id']}: {erro}")
            continue

        registro, motivo = montar_registro(detalhe)
        if registro is None:
            resumo[f"descartado: {motivo}"] += 1
            print(f"{prefixo} descartado ({motivo}): {detalhe.get('noFantasia')} "
                  f"[lat={detalhe.get('nuLatitude')}, lon={detalhe.get('nuLongitude')}]")
            descartados.append({
                "municipio": nome,
                "cnes": detalhe.get("cnes"),
                "nome": detalhe.get("noFantasia") or detalhe.get("noEmpresarial"),
                "tipo": detalhe.get("dsTipoEstabelecimento"),
                "logradouro": detalhe.get("noLogradouro"),
                "numero": detalhe.get("nuEndereco"),
                "bairro": detalhe.get("bairro"),
                "cep": detalhe.get("cep"),
                "telefone": detalhe.get("nuTelefone"),
                "latitude": detalhe.get("nuLatitude"),
                "longitude": detalhe.get("nuLongitude"),
                "motivo": motivo,
            })
        else:
            try:
                acao = salvar_registro(conexao, registro)
            except pymysql.MySQLError as erro:
                resumo["erro: banco de dados"] += 1
                print(f"{prefixo} ERRO ao gravar {registro['name']}: {erro}")
            else:
                resumo[acao] += 1
                print(f"{prefixo} {acao:10} {registro['name']}")

        time.sleep(PAUSA)


def main():
    parser = argparse.ArgumentParser(
        description="Preenche o banco do PMS com estabelecimentos de administração "
                    "pública do CNES."
    )
    parser.add_argument("municipios", nargs="*", default=MUNICIPIOS_PADRAO,
                        help="nomes dos municípios (padrão: Igarassu, Goiana, Itamaracá)")
    parser.add_argument("--listar-municipios", action="store_true",
                        help="mostra os municípios de PE e sai")
    parser.add_argument("--limite", type=int,
                        help="processa só os N primeiros de cada município (para testes)")
    args = parser.parse_args()

    sessao = criar_sessao()
    municipios = buscar_municipios(sessao)

    if args.listar_municipios:
        for codigo, nome in sorted(municipios.items(), key=lambda item: item[1]):
            print(codigo, nome)
        return

    # Resolve todos os nomes ANTES de gravar qualquer coisa
    escolhidos = []
    for nome in args.municipios:
        try:
            escolhidos.append(resolver_municipio(nome, municipios))
        except ValueError as erro:
            print(erro)
            return

        resumo = Counter()
    descartados = []
    conexao = conectar()
    try:
        for codigo, nome in escolhidos:
            coletar_municipio(sessao, conexao, codigo, nome, resumo, descartados, args.limite)
    finally:
        conexao.close()

    if descartados:
        salvar_descartados(descartados)
        print(f"\n{len(descartados)} descartados salvos em {CAMINHO_DESCARTADOS}")

    print("\n=== Resumo ===")
    for chave, quantidade in resumo.most_common():
        print(f"{quantidade:5}  {chave}")


if __name__ == "__main__":
    main()