import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../constants/api_constants.dart';
import 'api_exceptions.dart';

class ApiClient {
  late final Dio _dio;

  ApiClient({String? baseUrl}) {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl ?? ApiConstants.baseUrl,
        connectTimeout: ApiConstants.connectTimeout,
        receiveTimeout: ApiConstants.receiveTimeout,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    if (kDebugMode) {
      _dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            debugPrint('[API REQUEST] ${options.method} ${options.uri}');
            return handler.next(options);
          },
          onResponse: (response, handler) {
            final processTime = response.headers.value('x-process-time-ms');
            debugPrint(
              '[API RESPONSE] ${response.statusCode} ${response.requestOptions.path} (${processTime ?? "?"}ms)',
            );
            return handler.next(response);
          },
          onError: (DioException error, handler) {
            debugPrint('[API ERROR] ${error.response?.statusCode} ${error.message}');
            return handler.next(error);
          },
        ),
      );
    }
  }

  void updateBaseUrl(String newUrl) {
    _dio.options.baseUrl = newUrl;
  }

  String get currentBaseUrl => _dio.options.baseUrl;

  ApiException _handleDioError(DioException error) {
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.sendTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.connectionError) {
      return NetworkException(
        message: 'Could not connect to Sachme verification service. Please check your network.',
        details: error.error,
      );
    }

    final response = error.response;
    if (response != null) {
      final statusCode = response.statusCode;
      final data = response.data;
      String message = 'An error occurred during verification.';
      String? errorType;
      dynamic details;

      if (data is Map<String, dynamic>) {
        message = data['message'] as String? ??
            data['detail'] as String? ??
            message;
        errorType = data['error_type'] as String?;
        details = data['details'];
      }

      switch (statusCode) {
        case 400:
          return InvalidUrlException(
            message: message,
            statusCode: 400,
            errorType: errorType,
            details: details,
          );
        case 422:
          return UnsupportedContentException(
            message: message,
            statusCode: 422,
            errorType: errorType,
            details: details,
          );
        case 429:
          return RateLimitException(
            message: message,
            statusCode: 429,
            errorType: errorType,
            details: details,
          );
        case 502:
          return ExtractionFailedException(
            message: message,
            statusCode: 502,
            errorType: errorType,
            details: details,
          );
        case 500:
        default:
          return ServerException(
            message: message,
            statusCode: statusCode ?? 500,
            errorType: errorType,
            details: details,
          );
      }
    }

    return ApiException(message: error.message ?? 'Unknown network error');
  }

  Future<Map<String, dynamic>> postSync(
    String path, {
    required Map<String, dynamic> data,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        path,
        data: data,
        cancelToken: cancelToken,
      );
      return response.data ?? {};
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  Future<Map<String, dynamic>> get(
    String path, {
    Map<String, dynamic>? queryParameters,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        path,
        queryParameters: queryParameters,
        cancelToken: cancelToken,
      );
      return response.data ?? {};
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }
}
