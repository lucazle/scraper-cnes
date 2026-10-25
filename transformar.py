import re

# Caixa geográfica do litoral norte de Pernambuco (folgada de propósito).
LAT_MIN, LAT_MAX = -8.05, -7.40
LON_MIN, LON_MAX = -35.25, -34.75

# Maior valor que cabe na coluna INT do MySQL.
INT_MAX = 2_147_483_647


def limpar_numero(valor):
    """Converte o número do endereço em int, ou None se não for numérico."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if not re.fullmatch(r"[0-9]+", texto):
        return None
    numero = int(texto)
    return numero if numero <= INT_MAX else None


def formatar_cep(valor):
    """Devolve o CEP no formato 00000-000, ou '' se não tiver 8 dígitos."""
    if valor is None:
        return ""
    digitos = re.sub(r"\D", "", str(valor))
    if len(digitos) != 8:
        return ""
    return f"{digitos[:5]}-{digitos[5:]}"


def coordenadas_validas(lat, lon):
    """True se lat/lon forem números dentro da caixa do litoral norte."""
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return False
    return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX

TEXTO_PADRAO = "Não informado"


def _texto(valor, limite=255):
    """Tira espaços repetidos/das pontas e corta no tamanho da coluna."""
    if valor is None:
        return None
    texto = " ".join(str(valor).split())
    return texto[:limite] or None


def montar_registro(detalhe):
    """Transforma o detalhe do CNES em um registro pronto para o PMS.

    Devolve (registro, None) se estiver tudo certo, ou (None, motivo)
    se o estabelecimento precisar ser descartado.
    """
    cnes = _texto(detalhe.get("cnes"), 20)
    if not cnes:
        return None, "sem código CNES"

    lat = detalhe.get("nuLatitude")
    lon = detalhe.get("nuLongitude")
    if not coordenadas_validas(lat, lon):
        return None, "coordenadas ausentes ou fora da região"

    nome = _texto(detalhe.get("noFantasia")) or _texto(detalhe.get("noEmpresarial"))
    if not nome:
        return None, "sem nome"

    registro = {
        "cnes": cnes,
        "latitude": float(lat),
        "longitude": float(lon),
        "name": nome,
        "contact": _texto(detalhe.get("nuTelefone")),
        "street": _texto(detalhe.get("noLogradouro")) or TEXTO_PADRAO,
        "number": limpar_numero(detalhe.get("nuEndereco")),
        "district": _texto(detalhe.get("bairro")) or TEXTO_PADRAO,
        "cep": formatar_cep(detalhe.get("cep")),
        "service": _texto(detalhe.get("dsTipoEstabelecimento")),
    }
    return registro, None