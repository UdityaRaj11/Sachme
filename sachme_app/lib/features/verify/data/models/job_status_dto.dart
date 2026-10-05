import 'verify_response_dto.dart';

class JobStatusDto {
  final String jobId;
  final String status;
  final int progressPercentage;
  final String currentStep;
  final VerifyResponseDto? result;
  final String? error;
  final String createdAt;
  final String? completedAt;

  const JobStatusDto({
    required this.jobId,
    required this.status,
    required this.progressPercentage,
    required this.currentStep,
    this.result,
    this.error,
    required this.createdAt,
    this.completedAt,
  });

  bool get isCompleted => status == 'completed';
  bool get isFailed => status == 'failed';

  factory JobStatusDto.fromJson(Map<String, dynamic> json) {
    return JobStatusDto(
      jobId: json['job_id'] as String? ?? '',
      status: json['status'] as String? ?? 'queued',
      progressPercentage: (json['progress_percentage'] as num?)?.toInt() ?? 0,
      currentStep: json['current_step'] as String? ?? 'Processing...',
      result: json['result'] != null && json['result'] is Map<String, dynamic>
          ? VerifyResponseDto.fromJson(json['result'] as Map<String, dynamic>)
          : null,
      error: json['error'] as String?,
      createdAt: json['created_at'] as String? ?? '',
      completedAt: json['completed_at'] as String?,
    );
  }
}
