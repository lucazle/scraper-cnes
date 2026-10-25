from transformar import limpar_numero, formatar_cep, coordenadas_validas

assert limpar_numero("100") == 100
assert limpar_numero("05") == 5
assert limpar_numero(" 41 ") == 41
assert limpar_numero("S/N") is None
assert limpar_numero("") is None
assert limpar_numero(None) is None

assert formatar_cep("53670000") == "53670-000"
assert formatar_cep("53670-000") == "53670-000"
assert formatar_cep(None) == ""
assert formatar_cep("123") == ""

assert coordenadas_validas("-7.8739552", "-34.9072552") is True
assert coordenadas_validas(None, None) is False
assert coordenadas_validas("", "") is False
assert coordenadas_validas("abc", "x") is False
assert coordenadas_validas("-8.8116050", "-35.9109253") is False

print("Todos os testes passaram")