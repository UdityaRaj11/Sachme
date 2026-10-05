class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final String? errorType;
  final dynamic details;

  const ApiException({
    required this.message,
    this.statusCode,
    this.errorType,
    this.details,
  });

  @override
  String toString() => 'ApiException: $message (status: $statusCode, type: $errorType)';
}

class InvalidUrlException extends ApiException {
  const InvalidUrlException({
    required super.message,
    super.statusCode = 400,
    super.errorType = 'invalid_url',
    super.details,
  });
}

class UnsupportedContentException extends ApiException {
  const UnsupportedContentException({
    required super.message,
    super.statusCode = 422,
    super.errorType = 'unsupported_content',
    super.details,
  });
}

class ExtractionFailedException extends ApiException {
  const ExtractionFailedException({
    required super.message,
    super.statusCode = 502,
    super.errorType = 'content_extraction_failed',
    super.details,
  });
}

class RateLimitException extends ApiException {
  const RateLimitException({
    required super.message,
    super.statusCode = 429,
    super.errorType = 'rate_limit_exceeded',
    super.details,
  });
}

class ServerException extends ApiException {
  const ServerException({
    required super.message,
    super.statusCode = 500,
    super.errorType = 'internal_server_error',
    super.details,
  });
}

class NetworkException extends ApiException {
  const NetworkException({
    required super.message,
    super.details,
  }) : super(statusCode: null, errorType: 'network_error');
}
