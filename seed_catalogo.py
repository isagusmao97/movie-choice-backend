# seed_catalogo.py
import json
import sys

# Importa diretamente a função create_app
from app import create_app
from models import db, CatalogoFilme

def seed_catalogo():
    """Popula o catálogo de filmes com os dados do movies.json"""
    
    app = create_app()
    
    with app.app_context():
        # Verifica se já existem filmes no catálogo
        total = CatalogoFilme.query.count()
        if total > 0:
            print(f"Catálogo já possui {total} filmes.")
            resposta = input("Deseja recriar o catálogo? (s/N): ")
            if resposta.lower() != 's':
                print("Cancelado.")
                return
            print("Limpando catálogo existente...")
            CatalogoFilme.query.delete()
            db.session.commit()
        
        # Carrega o JSON
        try:
            with open('movies.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            print("Erro: Arquivo movies.json não encontrado!")
            #print("Certifique-se de que o arquivo está na mesma pasta que este script.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Erro ao ler JSON: {e}")
            sys.exit(1)
        
        # Adiciona cada filme ao catálogo
        filmes_adicionados = 0
        for movie_data in data['movies']:
            # Verifica se já existe pelo ID
            existe = CatalogoFilme.query.get(movie_data['id'])
            if not existe:
                filme = CatalogoFilme.from_json(movie_data)
                db.session.add(filme)
                filmes_adicionados += 1
                print(f"➕ Adicionando: {movie_data['title']} ({movie_data['year']})")
            else:
                print(f"⏭️  Pulando (já existe): {movie_data['title']}")
        
        # Commit no banco
        db.session.commit()
        print(f"\n✅ {filmes_adicionados} filmes adicionados ao catálogo com sucesso!")
        print(f"📊 Total de filmes no catálogo: {CatalogoFilme.query.count()}")

if __name__ == '__main__':
    seed_catalogo()