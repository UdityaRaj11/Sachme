import 'package:dio/dio.dart';
import '../entities/verification_result.dart';
import '../../data/models/job_status_dto.dart';
import '../../data/models/verify_response_dto.dart';

abstract class VerifyRepository {
  /// Executes synchronous verification
  Future<VerificationResult> verifySynchronous({
    String? url,
    String? directText,
    String language = 'en',
    CancelToken? cancelToken,
  });

  /// Initiates asynchronous background verification job
  Future<String> submitAsyncJob({
    String? url,
    String? directText,
    String language = 'en',
    CancelToken? cancelToken,
  });

  /// Polls job status
  Future<JobStatusDto> pollJobStatus(
    String jobId, {
    CancelToken? cancelToken,
  });

  /// Checks API service health
  Future<bool> checkHealth();

  /// Maps DTO to Domain Entity
  VerificationResult mapDtoToEntity(VerifyResponseDto dto, {String? customId});
}
