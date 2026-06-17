// ============================================================================
// EXEMPLO de service Dart para consumir o backend Flask do MovieChoice.
//
// Este arquivo é para REFERÊNCIA — copie para o seu projeto Flutter em:
//   lib/recursos/services/api_service.dart
//
// Antes de usar, adicione no pubspec.yaml (na seção dependencies):
//   http: ^1.2.0
//   shared_preferences: ^2.3.0
//
// Depois rode: flutter pub get
// ============================================================================

//import 'dart:convert';
//import 'package:http/http.dart' as http;
//import 'package:shared_preferences/shared_preferences.dart';

/*class ApiService {
  // IMPORTANTE: ajustar conforme onde o Flask está rodando:
  // - Web (chrome): 'http://localhost:5000'
  // - Android Emulator: 'http://10.0.2.2:5000'  (10.0.2.2 é o host na ótica do emulador)
  // - iOS Simulator: 'http://localhost:5000'
  // - Celular físico na mesma rede: 'http://192.168.x.x:5000' (IP da sua máquina)
  static const String baseUrl = 'http://localhost:5000/api';

  // ------------------- Salvar/recuperar identidade do membro -----------------

  static Future<void> _salvarMembro(String id, String nome) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('membro_id', id);
    await prefs.setString('membro_nome', nome);
  }

  static Future<String?> get membroId async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('membro_id');
  }

  // ------------------- Endpoints --------------------------------------------

  /// POST /api/salas — Cria uma sala.
  /// Equivalente ao botão "Criar Sala" em criar_sala.dart.
  static Future<Map<String, dynamic>> criarSala({
    required String nome,
    required String expiracao,   // '24h' | '48h' | '72h'
    required String tipoSessao,  // 'Cinema' | 'Streaming'
    required String criadorNome,
  }) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/salas'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'nome': nome,
        'expiracao': expiracao,
        'tipo_sessao': tipoSessao,
        'criador_nome': criadorNome,
      }),
    );

    if (resp.statusCode != 201) {
      throw Exception(_erroDeResposta(resp));
    }

    final dados = jsonDecode(resp.body) as Map<String, dynamic>;
    final membro = dados['membro_atual'] as Map<String, dynamic>;
    await _salvarMembro(membro['id'], membro['nome']);
    return dados;
  }

  /// POST /api/salas/<codigo>/entrar — Entra em uma sala existente.
  /// Equivalente ao botão "Entrar na Sala" em login.dart
  /// (HOJE ele só empurra uma sala mockada — você vai precisar conectar aqui).
  static Future<Map<String, dynamic>> entrarNaSala({
    required String codigo,
    required String nome,
  }) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/salas/$codigo/entrar'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'nome': nome}),
    );

    if (resp.statusCode != 201) {
      throw Exception(_erroDeResposta(resp));
    }

    final dados = jsonDecode(resp.body) as Map<String, dynamic>;
    final membro = dados['membro_atual'] as Map<String, dynamic>;
    await _salvarMembro(membro['id'], membro['nome']);
    return dados['sala'] as Map<String, dynamic>;
  }

  /// GET /api/salas/<codigo> — Carrega o estado atual da sala.
  /// Use ao abrir a tela Sala e/ou em polling para "tempo real" rudimentar.
  static Future<Map<String, dynamic>> obterSala(String codigo) async {
    final resp = await http.get(Uri.parse('$baseUrl/salas/$codigo'));
    if (resp.statusCode != 200) {
      throw Exception(_erroDeResposta(resp));
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  /// POST /api/salas/<codigo>/filmes — Sugere um filme.
  /// Equivalente ao botão "Sugerir um Filme" em sala.dart (hoje vazio).
  static Future<Map<String, dynamic>> sugerirFilme({
    required String codigo,
    required String titulo,
  }) async {
    final id = await membroId;
    if (id == null) {
      throw Exception('Você precisa estar em uma sala para sugerir filme.');
    }
    final resp = await http.post(
      Uri.parse('$baseUrl/salas/$codigo/filmes'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'titulo': titulo, 'membro_id': id}),
    );
    if (resp.statusCode != 201) {
      throw Exception(_erroDeResposta(resp));
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  /// POST /api/filmes/<filme_id>/votar — Vota em um filme.
  static Future<Map<String, dynamic>> votar(String filmeId) async {
    final id = await membroId;
    if (id == null) {
      throw Exception('Você precisa estar em uma sala para votar.');
    }
    final resp = await http.post(
      Uri.parse('$baseUrl/filmes/$filmeId/votar'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'membro_id': id}),
    );
    if (resp.statusCode != 201) {
      throw Exception(_erroDeResposta(resp));
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  // ------------------- Helpers ----------------------------------------------

  static String _erroDeResposta(http.Response resp) {
    try {
      final body = jsonDecode(resp.body) as Map<String, dynamic>;
      return body['erro']?.toString() ?? 'Erro HTTP ${resp.statusCode}';
    } catch (_) {
      return 'Erro HTTP ${resp.statusCode}: ${resp.body}';
    }
  }
}*/

// ============================================================================
// COMO PLUGAR NAS TELAS EXISTENTES — pontos exatos pra alterar:
//
// 1) lib/recursos/telas/criar_sala.dart, método _criarSala():
//    Trocar o "await Future.delayed(...)" mockado por:
//
//       try {
//         final sala = await ApiService.criarSala(
//           nome: _nomeController.text.trim(),
//           expiracao: _expiracao!,
//           tipoSessao: _tipoSessao!,
//           criadorNome: '<obter do estado/login>',
//         );
//         _showCodigoPopup(sala['codigo']);
//       } catch (e) {
//         _showSnack(e.toString());
//       } finally {
//         setState(() => _isLoading = false);
//       }
//
// 2) lib/recursos/telas/login.dart, onPressed do botão "Entrar na Sala"
//    (hoje empurra mock 'ABC123'):
//
//       try {
//         final sala = await ApiService.entrarNaSala(
//           codigo: codigoController.text.trim().toUpperCase(),
//           nome: nomeController.text.trim(),
//         );
//         Navigator.push(context, MaterialPageRoute(builder: (_) => Sala(
//           nomeSala: sala['nome'],
//           codigo: sala['codigo'],
//           expiracao: '...',          // calcular a partir de expira_em
//           tipoSessao: sala['tipo_sessao'],
//         )));
//       } catch (e) { /* ... */ }
//
//    OBS: os campos do login HOJE são TextFields sem controller. Você vai
//    precisar criar dois TextEditingController (nomeController, codigoController)
//    e ligar nos respectivos TextFields.
//
// 3) lib/recursos/telas/sala.dart:
//    - Converter para StatefulWidget.
//    - No initState() chamar ApiService.obterSala(widget.codigo) e renderizar
//      a lista de membros/filmes de verdade (em vez do placeholder).
//    - O botão "Sugerir um Filme" abrir um diálogo com TextField + ApiService.sugerirFilme(...).
// ============================================================================
