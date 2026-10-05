import 'dart:io' show Platform;
import 'package:flutter/foundation.dart';

class ApiConstants {
  static const String _defaultAndroidUrl = 'http://10.0.2.2:8000';
  static const String _defaultLocalhost = 'http://127.0.0.1:8000';

  static String get baseUrl {
    const fromEnv = String.fromEnvironment('API_URL');
    if (fromEnv.isNotEmpty) return fromEnv;

    if (kIsWeb) return _defaultLocalhost;
    try {
      if (Platform.isAndroid) return _defaultAndroidUrl;
    } catch (_) {}
    return _defaultLocalhost;
  }

  static const String syncVerifyEndpoint = '/api/v1/verify/sync';
  static const String asyncVerifyEndpoint = '/api/v1/verify';
  static const String jobStatusEndpoint = '/api/v1/jobs';
  static const String healthEndpoint = '/api/v1/health';

  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 60);
  static const Duration pollInterval = Duration(milliseconds: 600);
}
