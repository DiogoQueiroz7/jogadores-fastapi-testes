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