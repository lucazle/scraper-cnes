import csv
import time
import requests

PAGINA = "https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp"
BASE = "https://cnes.datasus.gov.br/services/estabelecimentos"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": PAGINA,
}

CAMPOS = [
    "id", "cnes", "noFantasia", "noEmpresarial", "dsTipoEstabelecimento",
    "noLogradouro", "nuEndereco", "bairro", "cep", "noMunicipio", "uf",
    "nuTelefone", "noEmail", "tpSempreAberto", "nuLatitude", "nuLongitude",
]


def criar_sessao():
    sessao = requests.Session()
    sessao.get(PAGINA, headers=HEADERS, timeout=30)  # pega os cookies
    return sessao


def buscar_lista(sessao, codigo_municipio):
    resposta = sessao.get(BASE, params={"municipio": codigo_municipio},
                          headers=HEADERS, timeout=30)
    resposta.raise_for_status()
    return resposta.json()


def buscar_detalhe(sessao, id_estabelecimento):
    resposta = sessao.get(f"{BASE}/{id_estabelecimento}",
                          headers=HEADERS, timeout=30)
    resposta.raise_for_status()
    return resposta.json()

def buscar_horarios(sessao, id_estabelecimento):
    resposta = sessao.get(f"{BASE}/atendimento/{id_estabelecimento}",
                          headers=HEADERS, timeout=30)
    resposta.raise_for_status()
    return resposta.json()


def formatar_horarios(horarios):
    partes = [
        f"{h['diaSemana']} {h['hrInicioAtendimento']}-{h['hrFimAtendimento']}"
        for h in horarios
    ]
    return "; ".join(partes)

def main():
    sessao = criar_sessao()
    lista = buscar_lista(sessao, "260680")  # Igarassu
    print(f"{len(lista)} estabelecimentos encontrados")

    linhas = []
    for i, item in enumerate(lista, start=1):
        try:
            detalhe = buscar_detalhe(sessao, item["id"])
        except requests.RequestException as erro:
            print(f"Falhou para o id {item['id']}: {erro}")
            continue

        linha = {campo: detalhe.get(campo) for campo in CAMPOS}

        try:
            horarios = buscar_horarios(sessao, item["id"])
            linha["horarios"] = formatar_horarios(horarios)
        except requests.RequestException as erro:
            print(f"  Sem horários para {item['id']}: {erro}")
            linha["horarios"] = ""

        linhas.append(linha)

        print(f"[{i}/{len(lista)}] {detalhe.get('noFantasia')}")
        time.sleep(0.5)  # pausa para não sobrecarregar o servidor

    with open("estabelecimentos_igarassu.csv", "w", newline="",
              encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS + ["horarios"])
        escritor.writeheader()
        escritor.writerows(linhas)

    print(f"Salvo: {len(linhas)} linhas em estabelecimentos_igarassu.csv")


if __name__ == "__main__":
    main()