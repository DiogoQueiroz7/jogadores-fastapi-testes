from fastapi.testclient import TestClient
from main import app

cliente = TestClient(app)

def test_listar_jogadores():
    resposta = cliente.get("/jogadores/")
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)


def test_cadastrar_sem_token():
    jogador = {"nome": "Carlos Miguel", "posicao": "goleiro"}
    resposta = cliente.post("/jogadores/", json=jogador)
    assert resposta.status_code == 401

def test_buscar_com_id_invalido():
    resposta = cliente.get("/jogadores/abc")
    assert resposta.status_code == 422

def test_login_com_usuario_inexistente():
    dados = {"username": "naocadastrado@exemplo.invalido", "password": "senha123"}
    resposta = cliente.post("/token", data=dados)
    assert resposta.status_code == 401

def test_excluir_com_token_invalido():
    cabecalho = {"Authorization": "Bearer token-invalido"}
    resposta = cliente.delete("/jogadores/-1", headers=cabecalho)
    assert resposta.status_code == 401