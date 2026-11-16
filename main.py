import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.hash import pbkdf2_sha256
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from tabelas import Jogador, Usuario

class JogadorEntrada(BaseModel):
    nome: str
    posicao: str

class JogadorSaida(JogadorEntrada):
    id: int

    model_config = ConfigDict(from_attributes=True)

app = FastAPI(
    title="Jogadores do Palmeiras",
    description="API para consultar e cadastrar jogadores do Palmeiras"
)

CHAVE_JWT = os.environ["CHAVE_JWT"]
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

def verificar_token(token: str = Depends(oauth2)):
    try:
        jwt.decode(
            token,
            CHAVE_JWT,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido ou vencido", headers={"WWW-Authenticate": "Bearer"})

@app.post("/token", tags=["Login"], responses={401: {"description": "email ou senha incorretos"}}, summary="Fazer login")
def login(formulario: OAuth2PasswordRequestForm = Depends(), banco: Session = Depends(get_db)):
    """use o email no campo username e a senha pra receber um token que vale por 30 minutos"""
    email = formulario.username.strip().lower()
    usuario = banco.query(Usuario).filter_by(email=email).first()

    if usuario is None:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    senha_correta = pbkdf2_sha256.verify(formulario.password, usuario.senha_hash)
    if not senha_correta:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    validade = datetime.now(timezone.utc) + timedelta(minutes=30)
    dados = {"sub": usuario.email, "exp": validade}
    token = jwt.encode(dados, CHAVE_JWT, algorithm="HS256")

    return {"access_token": token, "token_type": "bearer"}

@app.get("/jogadores/", tags=["Jogadores"], summary="Listar jogadores")
def listar_jogadores(posicao: str | None = None, banco: Session = Depends(get_db)) -> list[JogadorSaida]:
    """lista o elenco todo ou filtra pela posicao"""
    consulta = banco.query(Jogador)
    if posicao is None:
        return consulta.all()
    return consulta.filter(func.lower(Jogador.posicao) == posicao.lower()).all()

@app.get("/jogadores/{jogador_id}", tags=["Jogadores"], summary="Buscar jogador por ID")
def ver_jogador(jogador_id: int, banco: Session = Depends(get_db)) -> JogadorSaida | None:
    """busca pelo ID e retorna null se o jogador nao existir"""
    j = banco.get(Jogador, jogador_id)
    if j is not None:
        return j
    return None

@app.post("/jogadores/", tags=["Jogadores"], dependencies=[Depends(verificar_token)], responses={401: {"description": "faltou o token ou ele não é válido"}}, summary="Cadastrar jogador")
def criar_jogador(jogador: JogadorEntrada, banco: Session = Depends(get_db)) -> JogadorSaida:
    """adiciona um jogador ao elenco com nome e posição"""
    novo = Jogador(nome=jogador.nome, posicao=jogador.posicao.lower())
    banco.add(novo)
    banco.commit()
    banco.refresh(novo)
    return novo

@app.put("/jogadores/{jogador_id}", tags=["Jogadores"], dependencies=[Depends(verificar_token)], responses={401: {"description": "faltou o token ou ele não é válido"}}, summary="Editar jogador")
def atualizar_jogador(jogador_id: int, jogador: JogadorEntrada, banco: Session = Depends(get_db)) -> JogadorSaida | None:
    """atualiza o nome e a posicao do jogador pelo ID"""
    j = banco.get(Jogador, jogador_id)
    if j is not None:
        j.nome = jogador.nome
        j.posicao = jogador.posicao.lower()
        banco.commit()
        banco.refresh(j)
        return j
    return None

@app.delete("/jogadores/{jogador_id}", tags=["Jogadores"], dependencies=[Depends(verificar_token)], responses={401: {"description": "faltou o token ou ele não é válido"}}, summary="Excluir jogador")
def remover_jogador(jogador_id: int, banco: Session = Depends(get_db)) -> JogadorSaida | None:
    """remove o jogador do elenco pelo ID"""
    j = banco.get(Jogador, jogador_id)
    if j is not None:
        banco.delete(j)
        banco.commit()
        return j
    return None