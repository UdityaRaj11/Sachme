import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

class AppDatabase {
  static Database? _database;
  static const String _dbName = 'sachme_vault.db';
  static const int _dbVersion = 1;

  static const String tableVerifications = 'verifications';

  /// Initializes databaseFactory for desktop platforms (Windows, Linux, macOS)
  static void initialize() {
    if (!kIsWeb && (Platform.isWindows || Platform.isLinux || Platform.isMacOS)) {
      sqfliteFfiInit();
      databaseFactory = databaseFactoryFfi;
    }
  }

  static Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  static Future<Database> _initDatabase() async {
    initialize();

    String path;
    if (kIsWeb) {
      path = _dbName;
    } else {
      final documentsDirectory = await getApplicationDocumentsDirectory();
      path = join(documentsDirectory.path, _dbName);
    }

    final factory = (!kIsWeb && (Platform.isWindows || Platform.isLinux || Platform.isMacOS))
        ? databaseFactoryFfi
        : databaseFactory;

    return await factory.openDatabase(
      path,
      options: OpenDatabaseOptions(
        version: _dbVersion,
        onCreate: (db, version) async {
          await db.execute('''
            CREATE TABLE $tableVerifications (
              id TEXT PRIMARY KEY,
              url TEXT,
              platform TEXT,
              content_type TEXT,
              summary_text TEXT,
              claim_detected TEXT,
              overall_verdict TEXT,
              overall_confidence INTEGER,
              badge_label TEXT,
              verdict_title TEXT,
              why_explanation TEXT,
              raw_response_json TEXT,
              created_at TEXT,
              is_bookmarked INTEGER DEFAULT 0
            )
          ''');

          await db.execute('''
            CREATE INDEX idx_verifications_created_at ON $tableVerifications (created_at DESC)
          ''');
          await db.execute('''
            CREATE INDEX idx_verifications_verdict ON $tableVerifications (overall_verdict)
          ''');
        },
      ),
    );
  }

  /// Inserts or updates a verification item
  static Future<void> saveVerification({
    required String id,
    required String url,
    required String platform,
    required String contentType,
    required String summaryText,
    required String claimDetected,
    required String overallVerdict,
    required int overallConfidence,
    required String badgeLabel,
    required String verdictTitle,
    required String whyExplanation,
    required Map<String, dynamic> rawJson,
    DateTime? createdAt,
  }) async {
    final db = await database;
    await db.insert(
      tableVerifications,
      {
        'id': id,
        'url': url,
        'platform': platform,
        'content_type': contentType,
        'summary_text': summaryText,
        'claim_detected': claimDetected,
        'overall_verdict': overallVerdict,
        'overall_confidence': overallConfidence,
        'badge_label': badgeLabel,
        'verdict_title': verdictTitle,
        'why_explanation': whyExplanation,
        'raw_response_json': jsonEncode(rawJson),
        'created_at': (createdAt ?? DateTime.now()).toIso8601String(),
        'is_bookmarked': 0,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  /// Retrieves all verification records, ordered by newest first
  static Future<List<Map<String, dynamic>>> getHistory({
    String? verdictFilter,
    String? searchQuery,
  }) async {
    final db = await database;
    String whereClause = '';
    List<dynamic> whereArgs = [];

    if (verdictFilter != null && verdictFilter.isNotEmpty && verdictFilter != 'ALL') {
      whereClause += 'overall_verdict = ?';
      whereArgs.add(verdictFilter);
    }

    if (searchQuery != null && searchQuery.trim().isNotEmpty) {
      if (whereClause.isNotEmpty) whereClause += ' AND ';
      whereClause += '(claim_detected LIKE ? OR why_explanation LIKE ? OR url LIKE ?)';
      final queryParam = '%${searchQuery.trim()}%';
      whereArgs.addAll([queryParam, queryParam, queryParam]);
    }

    return await db.query(
      tableVerifications,
      where: whereClause.isEmpty ? null : whereClause,
      whereArgs: whereArgs.isEmpty ? null : whereArgs,
      orderBy: 'created_at DESC',
      limit: 100,
    );
  }

  /// Deletes a specific verification
  static Future<int> deleteVerification(String id) async {
    final db = await database;
    return await db.delete(
      tableVerifications,
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  /// Clears entire history
  static Future<int> clearAllHistory() async {
    final db = await database;
    return await db.delete(tableVerifications);
  }
}
