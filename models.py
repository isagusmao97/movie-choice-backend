"""
Modelos do banco de dados.

Mapeamento direto do que o app Flutter precisa:
- Sala: o que é criado em criar_sala.dart
- Membro: cada usuário que entrou (login.dart pede só o nome)
- Filme: cada sugestão (botão "Sugerir um Filme" em sala.dart)
- Voto: relação N:N entre Membro e Filme (um membro só pode votar uma vez por filme)
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import json

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _uuid() -> str:
    """Gera um UUID4 em string. Usado como ID público (não-sequencial)."""
    return str(uuid4())


def _agora_utc() -> datetime:
    """Sempre salvar em UTC. Conversão para fuso do usuário é responsabilidade do cliente."""
    return datetime.now(timezone.utc)


class Sala(db.Model):
    __tablename__ = "salas"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    codigo = db.Column(db.String(6), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(120), nullable=False)
    tipo_sessao = db.Column(db.String(20), nullable=False)  # 'Cinema' | 'Streaming'
    criada_em = db.Column(db.DateTime(timezone=True), nullable=False, default=_agora_utc)
    expira_em = db.Column(db.DateTime(timezone=True), nullable=False)
    # criador_id aponta para o membro que criou (preenchido depois que o primeiro membro é criado)
    criador_id = db.Column(db.String(36), nullable=True)
    encerrada = db.Column(db.Boolean, default=False, nullable=False)

    membros = db.relationship(
        "Membro", backref="sala", cascade="all, delete-orphan", lazy="dynamic"
    )
    filmes = db.relationship(
        "Filme", backref="sala", cascade="all, delete-orphan", lazy="dynamic"
    )

    def esta_expirada(self) -> bool:
        if self.encerrada:
            return True
        agora = _agora_utc()
        expira = self.expira_em
        if expira.tzinfo is None:
            expira = expira.replace(tzinfo=timezone.utc)
        return agora >= expira

    def to_dict(self, incluir_relacoes: bool = True) -> dict:
        data = {
            "id": self.id,
            "codigo": self.codigo,
            "nome": self.nome,
            "tipo_sessao": self.tipo_sessao,
            "criada_em": self.criada_em.isoformat(),
            "expira_em": self.expira_em.isoformat(),
            "expirada": self.esta_expirada(),
            "encerrada": self.encerrada,
            "criador_id": self.criador_id,
        }
        if incluir_relacoes:
            data["membros"] = [m.to_dict() for m in self.membros.all()]
            data["filmes"] = [f.to_dict() for f in self.filmes.all()]
        return data


class Membro(db.Model):
    __tablename__ = "membros"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    sala_id = db.Column(db.String(36), db.ForeignKey("salas.id"), nullable=False, index=True)
    nome = db.Column(db.String(80), nullable=False)
    entrou_em = db.Column(db.DateTime(timezone=True), nullable=False, default=_agora_utc)

    votos = db.relationship("Voto", backref="membro", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "entrou_em": self.entrou_em.isoformat(),
        }


class CatalogoFilme(db.Model):
    """Catálogo global de filmes (vindo do movies.json).
    Estes filmes podem ser sugeridos em qualquer sala.
    """
    __tablename__ = "catalogo_filmes"

    id = db.Column(db.Integer, primary_key=True)  # ID numérico do JSON
    titulo = db.Column(db.String(200), nullable=False)
    titulo_original = db.Column(db.String(200))
    ano = db.Column(db.Integer, nullable=False)
    diretor = db.Column(db.String(200))
    generos = db.Column(db.String(500))  # JSON string: ["Ação", "Drama"]
    avaliacao = db.Column(db.Float)  # Rating
    duracao_minutos = db.Column(db.Integer)
    sinopse = db.Column(db.Text)
    idioma = db.Column(db.String(100))
    pais = db.Column(db.String(100))
    poster_url = db.Column(db.String(500))
    backdrop_url = db.Column(db.String(500))
    trailer_url = db.Column(db.String(500))
    elenco = db.Column(db.Text)  # JSON string: ["Ator1", "Ator2"]
    classificacao_etaria = db.Column(db.String(10))
    disponivel = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime(timezone=True), default=_agora_utc)
    
    def to_dict(self, incluir_detalhes: bool = False) -> dict:
        """Converte para dicionário compatível com o app Flutter"""
        data = {
            "id": str(self.id),  # Converte para string para compatibilidade
            "title": self.titulo,
            "year": self.ano,
            "genre": json.loads(self.generos) if self.generos else [],
            "platform": self._get_plataformas(),  # Define baseado no tipo
            "duration_min": self.duracao_minutos,
            "rating": self.avaliacao,
            "poster_url": self.poster_url,
            "synopsis": self.sinopse,
        }
        
        if incluir_detalhes:
            data.update({
                "original_title": self.titulo_original,
                "director": self.diretor,
                "language": self.idioma,
                "country": self.pais,
                "backdrop_url": self.backdrop_url,
                "trailer_url": self.trailer_url,
                "cast": json.loads(self.elenco) if self.elenco else [],
                "age_rating": self.classificacao_etaria,
            })
        
        return data
    
    def _get_plataformas(self) -> list:
        """Define em quais plataformas o filme está disponível.
        Por enquanto, retorna uma lista padrão baseada no tipo.
        Em produção, isso viria de uma tabela de disponibilidade.
        """
        # TODO: Implementar lógica real de disponibilidade por plataforma
        plataformas_padrao = ["Netflix", "Max", "Disney+"]
        
        # Para filmes brasileiros ou específicos, pode ajustar
        if self.pais == "Brasil":
            return ["Netflix", "Amazon Prime"]
        
        return plataformas_padrao
    
    @staticmethod
    def from_json(data: dict) -> "CatalogoFilme":
        """Cria uma instância a partir do JSON do movies.json"""
        return CatalogoFilme(
            id=data.get('id'),
            titulo=data.get('title'),
            titulo_original=data.get('original_title'),
            ano=data.get('year'),
            diretor=data.get('director'),
            generos=json.dumps(data.get('genres', [])),
            avaliacao=data.get('rating'),
            duracao_minutos=data.get('duration_minutes'),
            sinopse=data.get('synopsis'),
            idioma=data.get('language'),
            pais=data.get('country'),
            poster_url=data.get('poster_url'),
            backdrop_url=data.get('backdrop_url'),
            trailer_url=data.get('trailer_url'),
            elenco=json.dumps(data.get('cast', [])),
            classificacao_etaria=data.get('age_rating'),
            disponivel=data.get('available', True)
        )


class Filme(db.Model):
    """Filme sugerido em uma sala específica.
    Este é um filme DO CATÁLOGO que foi sugerido por um membro.
    """
    __tablename__ = "filmes"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    sala_id = db.Column(db.String(36), db.ForeignKey("salas.id"), nullable=False, index=True)
    catalogo_id = db.Column(db.Integer, db.ForeignKey("catalogo_filmes.id"), nullable=False)
    titulo_personalizado = db.Column(db.String(200), nullable=True)  # Permite título customizado
    sugerido_por_id = db.Column(db.String(36), db.ForeignKey("membros.id"), nullable=False)
    sugerido_em = db.Column(db.DateTime(timezone=True), nullable=False, default=_agora_utc)

    # Relacionamentos
    sugerido_por = db.relationship("Membro", foreign_keys=[sugerido_por_id])
    catalogo = db.relationship("CatalogoFilme", backref="sugestoes")
    votos = db.relationship("Voto", backref="filme", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self, incluir_detalhes_catalogo: bool = False) -> dict:
        """Retorna os dados do filme + detalhes do catálogo"""
        dados_base = {
            "id": self.id,
            "sala_id": self.sala_id,
            "titulo": self.titulo_personalizado or self.catalogo.titulo,
            "sugerido_por": {
                "id": self.sugerido_por.id,
                "nome": self.sugerido_por.nome,
            } if self.sugerido_por else None,
            "sugerido_em": self.sugerido_em.isoformat(),
            "total_votos": self.votos.count(),
        }
        
        if incluir_detalhes_catalogo and self.catalogo:
            dados_base["detalhes"] = self.catalogo.to_dict(incluir_detalhes=True)
        
        return dados_base


class Voto(db.Model):
    """Tabela de relação N:N entre Membro e Filme.
    Restrição (membro_id, filme_id) impede voto duplicado.
    """
    __tablename__ = "votos"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    membro_id = db.Column(db.String(36), db.ForeignKey("membros.id"), nullable=False)
    filme_id = db.Column(db.String(36), db.ForeignKey("filmes.id"), nullable=False)
    votado_em = db.Column(db.DateTime(timezone=True), nullable=False, default=_agora_utc)

    __table_args__ = (
        db.UniqueConstraint("membro_id", "filme_id", name="uq_voto_unico_por_filme"),
    )


# Helpers usados pelas rotas ---------------------------------------------------

EXPIRACOES_VALIDAS = {"24h": 24, "48h": 48, "72h": 72}
TIPOS_SESSAO_VALIDOS = {"Cinema", "Streaming"}


def calcular_expira_em(expiracao: str) -> datetime:
    """Converte '24h'/'48h'/'72h' em datetime UTC futuro."""
    horas = EXPIRACOES_VALIDAS[expiracao]
    return _agora_utc() + timedelta(hours=horas)