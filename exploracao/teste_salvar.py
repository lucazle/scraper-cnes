from banco import conectar, salvar_registro
from transformar import montar_registro

# Detalhe real de um estabelecimento (o mesmo que você viu no navegador)
DETALHE = {
    "id": "2606804122070",
    "cnes": "4122070",
    "noFantasia": "ACADEMIA DA SAUDE CRUZ",
    "noEmpresarial": "MUNICIPIO DE IGARASSU",
    "dsTipoEstabelecimento": "POLO DE PREVENCAO DE DOENCAS E AGRAVOS E PROMOCAO DA SAUDE",
    "noLogradouro": "R LUCIANA PAIVA DE SOUZA",
    "nuEndereco": "100",
    "cep": "53670000",
    "bairro": "CRUZ DE REBOUCAS",
    "nuTelefone": None,
    "nuLatitude": "-7.8739552",
    "nuLongitude": "-34.9072552",
}


def contagens(conexao):
    with conexao.cursor() as cur:
        resultado = {}
        for tabela in ["locations", "descriptions", "addresses", "services", "locations_services"]:
            cur.execute(f"SELECT COUNT(*) FROM {tabela}")
            resultado[tabela] = cur.fetchone()[0]
    return resultado


conexao = conectar()

registro, motivo = montar_registro(DETALHE)
print("Registro montado:", registro)

print("1ª execução:", salvar_registro(conexao, registro))
print("   contagens:", contagens(conexao))

print("2ª execução:", salvar_registro(conexao, registro))
print("   contagens:", contagens(conexao), "(não deve ter duplicado nada)")

DETALHE["noFantasia"] = "ACADEMIA DA SAUDE CRUZ (NOME NOVO)"
registro, _ = montar_registro(DETALHE)
print("3ª execução (nome mudou):", salvar_registro(conexao, registro))

with conexao.cursor() as cur:
    cur.execute("SELECT name FROM descriptions")
    print("   nome no banco:", cur.fetchone()[0])

# Estabelecimento com dados sujos: sem número, sem CEP válido, sem bairro
sujo = dict(DETALHE, cnes="0469203", noFantasia="  CLINICA   TESTE ", nuEndereco="S/N",
            cep="12", bairro=None, nuTelefone="(81) 3543-1001")
registro, motivo = montar_registro(sujo)
print("Sujo ->", registro)
print("   gravou:", salvar_registro(conexao, registro))

# Estabelecimento com coordenada errada: deve ser descartado
ruim = dict(DETALHE, cnes="9999999", nuLatitude="-8.8116050", nuLongitude="-35.9109253")
print("Coordenada errada ->", montar_registro(ruim))

print("Contagens finais:", contagens(conexao))
conexao.close()