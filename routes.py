# routes.py
from flask import Blueprint, request, jsonify
from models import db, Sala, Membro, Filme, Voto, CatalogoFilme
from models import calcular_expira_em, EXPIRACOES_VALIDAS, TIPOS_SESSAO_VALIDOS
import random
import string

# Define o Blueprint
api = Blueprint('api', __name__, url_prefix='/api')


# ========== ROTA DE HEALTH CHECK ==========

@api.route('/health', methods=['GET'])
def health_check():
    """Verifica se a API está funcionando"""
    return jsonify({
        "status": "ok",
        "message": "MovieChoice API está online!"
    }), 200


# ========== ROTAS DE CATÁLOGO DE FILMES ==========

@api.route('/catalogo/filmes', methods=['GET'])
def listar_catalogo():
    """Lista todos os filmes do catálogo disponíveis"""
    try:
        genero = request.args.get('genero')
        busca = request.args.get('busca')
        
        query = CatalogoFilme.query.filter_by(disponivel=True)
        
        # Filtro por gênero
        if genero and genero != 'Todos':
            query = query.filter(CatalogoFilme.generos.like(f'%{genero}%'))
        
        # Busca por título
        if busca:
            query = query.filter(CatalogoFilme.titulo.ilike(f'%{busca}%'))
        
        filmes = query.all()
        
        # Converte para o formato esperado pelo Flutter
        filmes_formatados = []
        for f in filmes:
            dados = f.to_dict()
            filmes_formatados.append(dados)
        
        return jsonify({
            'movies': filmes_formatados,
            'total': len(filmes_formatados)
        }), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@api.route('/catalogo/filmes/<int:filme_id>', methods=['GET'])
def detalhes_catalogo(filme_id):
    """Retorna detalhes completos de um filme do catálogo"""
    try:
        filme = CatalogoFilme.query.get_or_404(filme_id)
        return jsonify(filme.to_dict(incluir_detalhes=True)), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 404


# ========== ROTAS DE SALAS ==========

@api.route('/salas', methods=['POST'])
def criar_sala():
    """Cria uma nova sala"""
    try:
        dados = request.json
        
        # Validações
        if not dados.get('nome'):
            return jsonify({'erro': 'Nome da sala é obrigatório'}), 400
        
        tipo_sessao = dados.get('tipo_sessao', 'Streaming')
        if tipo_sessao not in TIPOS_SESSAO_VALIDOS:
            return jsonify({'erro': f'Tipo de sessão inválido. Use: {TIPOS_SESSAO_VALIDOS}'}), 400
        
        expiracao = dados.get('expiracao', '24h')
        if expiracao not in EXPIRACOES_VALIDAS:
            return jsonify({'erro': f'Expiração inválida. Use: {list(EXPIRACOES_VALIDAS.keys())}'}), 400
        
        # Gera código único de 6 caracteres
        while True:
            codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Sala.query.filter_by(codigo=codigo).first():
                break
        
        # Calcula data de expiração
        expira_em = calcular_expira_em(expiracao)
        
        # Cria a sala
        sala = Sala(
            codigo=codigo,
            nome=dados['nome'],
            tipo_sessao=tipo_sessao,
            expira_em=expira_em
        )
        
        db.session.add(sala)
        db.session.commit()
        
        # Se o criador foi informado, cria o membro
        nome_criador = dados.get('nome_criador')
        if nome_criador:
            membro = Membro(
                sala_id=sala.id,
                nome=nome_criador
            )
            db.session.add(membro)
            db.session.commit()
            
            # Atualiza o criador_id da sala
            sala.criador_id = membro.id
            db.session.commit()
            
            return jsonify({
                'sala': sala.to_dict(incluir_relacoes=False),
                'membro': membro.to_dict(),
                'codigo': codigo
            }), 201
        
        return jsonify({
            'sala': sala.to_dict(incluir_relacoes=False),
            'codigo': codigo
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@api.route('/salas/<codigo>', methods=['GET'])
def obter_sala(codigo):
    """Retorna detalhes da sala pelo código"""
    try:
        sala = Sala.query.filter_by(codigo=codigo).first_or_404()
        
        if sala.esta_expirada():
            return jsonify({'erro': 'Sala expirada'}), 400
        
        return jsonify(sala.to_dict()), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 404


@api.route('/salas/<codigo>/entrar', methods=['POST'])
def entrar_sala(codigo):
    """Adiciona um membro à sala"""
    try:
        sala = Sala.query.filter_by(codigo=codigo).first_or_404()
        
        if sala.esta_expirada():
            return jsonify({'erro': 'Sala expirada'}), 400
        
        dados = request.json
        nome = dados.get('nome')
        
        if not nome:
            return jsonify({'erro': 'Nome é obrigatório'}), 400
        
        # Verifica se já existe membro com este nome na sala
        membro_existente = Membro.query.filter_by(sala_id=sala.id, nome=nome).first()
        if membro_existente:
            return jsonify({
                'membro': membro_existente.to_dict(),
                'aviso': 'Você já está nesta sala'
            }), 200
        
        # Cria novo membro
        membro = Membro(
            sala_id=sala.id,
            nome=nome
        )
        
        db.session.add(membro)
        db.session.commit()
        
        return jsonify(membro.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500



# ========== ROTAS DE SUGESTÕES ==========

@api.route('/salas/<codigo>/sugestoes', methods=['GET'])
def listar_sugestoes(codigo):
    """Lista todas as sugestões de filmes de uma sala"""
    try:
        sala = Sala.query.filter_by(codigo=codigo).first_or_404()
        
        sugestoes = Filme.query.filter_by(sala_id=sala.id).all()
        
        # Converter para o formato esperado pelo Flutter
        resultados = []
        for filme in sugestoes:
            resultados.append({
                'id': filme.id,
                'titulo': filme.titulo_personalizado or filme.catalogo.titulo,
                'total_votos': filme.votos.count(),
                'sugerido_por': {
                    'id': filme.sugerido_por.id,
                    'nome': filme.sugerido_por.nome
                } if filme.sugerido_por else None,
                'detalhes': filme.catalogo.to_dict(incluir_detalhes=True) if filme.catalogo else None
            })
        
        return jsonify({
            'sugestoes': resultados,
            'total': len(resultados)
        }), 200
    except Exception as e:
        print(f"❌ Erro em listar_sugestoes: {e}")
        return jsonify({'erro': str(e)}), 500


@api.route('/salas/<codigo>/sugestoes', methods=['POST'])
def sugerir_filme(codigo):
    """Sugere um filme do catálogo para a sala"""
    try:
        print(f"🔵 POST /salas/{codigo}/sugestoes")
        print(f"📦 Dados recebidos: {request.json}")
        
        sala = Sala.query.filter_by(codigo=codigo).first_or_404()
        
        if sala.esta_expirada():
            return jsonify({'erro': 'Sala expirada'}), 400
        
        dados = request.json
        catalogo_id = dados.get('catalogo_id')
        titulo_personalizado = dados.get('titulo_personalizado')
        sugerido_por_id = dados.get('sugerido_por_id')
        
        # Validações
        if not catalogo_id:
            return jsonify({'erro': 'catalogo_id é obrigatório'}), 400
        
        if not sugerido_por_id:
            return jsonify({'erro': 'sugerido_por_id é obrigatório'}), 400
        
        # Verifica se o filme existe no catálogo
        catalogo = CatalogoFilme.query.get_or_404(catalogo_id)
        
        # Verifica se o membro existe
        membro = Membro.query.get_or_404(sugerido_por_id)
        
        # Verifica se o membro está na sala
        if membro.sala_id != sala.id:
            return jsonify({'erro': 'Membro não pertence a esta sala'}), 400
        
        # Verifica se já foi sugerido nesta sala
        existe = Filme.query.filter_by(
            sala_id=sala.id,
            catalogo_id=catalogo_id
        ).first()
        
        if existe:
            return jsonify({'erro': 'Este filme já foi sugerido nesta sala'}), 400
        
        # Cria a sugestão
        filme = Filme(
            sala_id=sala.id,
            catalogo_id=catalogo_id,
            titulo_personalizado=titulo_personalizado,
            sugerido_por_id=sugerido_por_id
        )
        
        db.session.add(filme)
        db.session.commit()
        
        print(f"✅ Filme sugerido com sucesso: {filme.id}")
        
        return jsonify({
            'id': filme.id,
            'titulo': filme.titulo_personalizado or filme.catalogo.titulo,
            'total_votos': 0,
            'sugerido_por': {
                'id': membro.id,
                'nome': membro.nome
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro em sugerir_filme: {e}")
        return jsonify({'erro': str(e)}), 500


# ========== ROTAS DE VOTOS ==========

@api.route('/filmes/<filme_id>/votar', methods=['POST'])
def votar(filme_id):
    """Registra um voto em um filme"""
    try:
        dados = request.json
        membro_id = dados.get('membro_id')
        
        if not membro_id:
            return jsonify({'erro': 'membro_id é obrigatório'}), 400
        
        # Verifica se o filme existe
        filme = Filme.query.get_or_404(filme_id)
        
        # Verifica se o membro existe
        membro = Membro.query.get_or_404(membro_id)
        
        # Verifica se o membro está na mesma sala
        if membro.sala_id != filme.sala_id:
            return jsonify({'erro': 'Membro não pertence a esta sala'}), 400
        
        # Verifica se o voto já existe
        voto_existente = Voto.query.filter_by(
            filme_id=filme_id,
            membro_id=membro_id
        ).first()
        
        if voto_existente:
            return jsonify({'erro': 'Você já votou neste filme'}), 400
        
        # Cria o voto
        voto = Voto(
            filme_id=filme_id,
            membro_id=membro_id
        )
        
        db.session.add(voto)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Voto registrado com sucesso!',
            'total_votos': filme.votos.count()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@api.route('/filmes/<filme_id>/votos/<membro_id>', methods=['DELETE'])
def remover_voto(filme_id, membro_id):
    """Remove um voto (caso o membro queira mudar de ideia)"""
    try:
        voto = Voto.query.filter_by(
            filme_id=filme_id,
            membro_id=membro_id
        ).first_or_404()
        
        db.session.delete(voto)
        db.session.commit()
        
        filme = Filme.query.get(filme_id)
        
        return jsonify({
            'mensagem': 'Voto removido com sucesso!',
            'total_votos': filme.votos.count() if filme else 0
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


# ========== ROTAS DE RESULTADOS ==========

@api.route('/salas/<codigo>/resultados', methods=['GET'])
def resultados_sala(codigo):
    """Retorna os resultados da votação da sala"""
    try:
        sala = Sala.query.filter_by(codigo=codigo).first_or_404()
        
        if not sala.esta_expirada():
            return jsonify({'aviso': 'Votação ainda não terminou'}), 200
        
        sugestoes = Filme.query.filter_by(sala_id=sala.id).all()
        
        # Ordena por número de votos (decrescente)
        resultados = sorted(
            [f.to_dict(incluir_detalhes_catalogo=True) for f in sugestoes],
            key=lambda x: x['total_votos'],
            reverse=True
        )
        
        return jsonify({
            'resultados': resultados,
            'sala': sala.to_dict(incluir_relacoes=False)
        }), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    
    
@api.route('/salas/<codigo>/encerrar', methods=['POST'])
def encerrar_sala(codigo):
    """Encerra a sala manualmente"""
    try:
        sala = Sala.query.filter_by(codigo=codigo).first_or_404()

        sala.encerrada = True
        db.session.commit()

        sugestoes = Filme.query.filter_by(sala_id=sala.id).all()

        if not sugestoes:
            return jsonify({'success': False, 'message': 'Nenhum filme sugerido'}), 200

        # Ordena por número de votos (decrescente)
        resultados = sorted(
            [f.to_dict(incluir_detalhes_catalogo=True) for f in sugestoes],
            key=lambda x: x['total_votos'],
            reverse=True
        )

        return jsonify({
            'success': True,
            'resultados': resultados,
            'sala': sala.to_dict(incluir_relacoes=False)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500