"""
MovieChoice — Backend Flask.

Ponto de entrada da aplicação. Usamos o padrão "application factory"
(recomendado pela documentação oficial do Flask) para facilitar testes
e separar configuração de instanciação.

Referência: https://flask.palletsprojects.com/en/stable/patterns/appfactories/
"""
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from models import db
from routes import api

# Carrega variáveis do .env (se existir) ANTES de criar o app.
load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True, static_folder='static', static_url_path='/static')

    

    # ---- Configuração --------------------------------------------------------
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-troque-em-prod")

    # Em SQLite, instance_relative_config=True faz o banco ir para ./instance/
    database_url = os.environ.get("DATABASE_URL", "sqlite:///moviechoice.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    

    # ---- Extensões -----------------------------------------------------------
    db.init_app(app)

    # CORS: em produção restrinja para o domínio do seu app
    cors_origins = os.environ.get("CORS_ORIGINS", "*")
    CORS(app, resources={r"/api/*": {"origins": cors_origins},r"/static/*": {"origins": cors_origins}})

    # ---- Blueprints ----------------------------------------------------------
    app.register_blueprint(api)

    # ---- Rota raiz (sanity check) -------------------------------------------
    @app.get("/")
    def index():
        return jsonify({
            "app": "MovieChoice API",
            "status": "online",
            "endpoints_principais": [
                "GET  /api/health",
                "POST /api/salas",
                "GET  /api/salas/<codigo>",
                "POST /api/salas/<codigo>/entrar",
                "POST /api/salas/<codigo>/filmes",
                "POST /api/filmes/<filme_id>/votar",
            ],
        })

    # ---- Tratadores globais de erro -----------------------------------------
    @app.errorhandler(404)
    def nao_encontrado(_):
        return jsonify({"erro": "Recurso não encontrado."}), 404

    @app.errorhandler(405)
    def metodo_nao_permitido(_):
        return jsonify({"erro": "Método HTTP não permitido para esta rota."}), 405

    @app.errorhandler(500)
    def erro_interno(_):
        return jsonify({"erro": "Erro interno do servidor."}), 500

    # ---- Criação automática das tabelas em dev ------------------------------
    # Para projeto de matéria isto é ok. Em produção, prefira migrations (Flask-Migrate).
    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
        db.create_all()


    # Rota para servir imagens (opcional, mas mais explícita)
    @app.route('/images/<path:filename>')
    def serve_image(filename):
        return send_from_directory('static/images', filename)
    
    return app


# Instância para `flask run` e para gunicorn
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    # debug=True só em desenvolvimento. NUNCA em produção.
    app.run(host="0.0.0.0", port=port, debug=True)
