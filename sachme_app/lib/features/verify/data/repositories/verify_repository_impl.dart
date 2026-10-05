import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../../core/database/app_database.dart';
import '../../../../core/network/api_client.dart';
import '../../domain/entities/claim.dart';
import '../../domain/entities/evidence.dart';
import '../../domain/entities/verification_result.dart';
import '../../domain/repositories/verify_repository.dart';
import '../models/job_status_dto.dart';
import '../models/verify_response_dto.dart';

class VerifyRepositoryImpl implements VerifyRepository {
  final ApiClient _apiClient;
  final Uuid _uuid = const Uuid();

  VerifyRepositoryImpl({required ApiClient apiClient}) : _apiClient = apiClient;

  @override
  VerificationResult mapDtoToEntity(VerifyResponseDto dto, {String? customId}) {
    final id = customId ?? _uuid.v4();
    final ui = dto.userInterface;

    final claims = dto.claims.map((c) {
      final evidenceList = c.evidence.map((e) {
        return EvidenceEntity(
          finding: e.finding,
          stance: EvidenceEntity.parseStance(e.type),
          source: e.source,
          url: e.url,
          credibilityScore: e.credibilityScore,
          tier: e.credibilityScore >= 90
              ? 'Tier 1'
              : (e.credibilityScore >= 70 ? 'Tier 2' : 'Tier 3'),
        );
      }).toList();

      return ClaimEntity(
        claimId: c.claimId,
        claim: c.claim,
        verdict: c.verdict,
        confidence: c.confidence,
        evidence: evidenceList,
        explanation: c.explanation,
      );
    }).toList();

    final claimDetected = ui?.claimDetected.isNotEmpty == true
        ? ui!.claimDetected
        : (dto.claims.isNotEmpty ? dto.claims.first.claim : dto.content.summary.text);

    final whyExplanation = ui?.whyExplanation.isNotEmpty == true
        ? ui!.whyExplanation
        : (dto.claims.isNotEmpty ? dto.claims.first.explanation : 'No additional context provided.');

    final verdictTitle = ui?.verdictTitle.isNotEmpty == true
        ? ui!.verdictTitle
        : dto.overallVerdict;

    final badgeLabel = ui?.badgeLabel.isNotEmpty == true
        ? ui!.badgeLabel
        : dto.overallVerdict;

    final confidenceDisplay = ui?.confidenceDisplay.isNotEmpty == true
        ? ui!.confidenceDisplay
        : '${dto.overallConfidence}%';

    final evidencePoints = ui?.evidencePoints ??
        claims.expand((c) => c.evidence.map((e) => '• ${e.source}: ${e.finding}')).toList();

    final evidenceSources = ui?.evidenceSources ??
        claims.expand((c) => c.evidence.map((e) => {
              'source': e.source,
              'url': e.url,
              'credibility': '${e.credibilityScore}/100',
            })).toList();

    return VerificationResult(
      id: id,
      url: dto.content.url,
      platform: dto.content.platform,
      contentType: dto.content.contentType,
      summaryText: dto.content.summary.text,
      keyPoints: dto.content.summary.keyPoints,
      claims: claims,
      overallVerdict: dto.overallVerdict,
      overallConfidence: dto.overallConfidence,
      badgeLabel: badgeLabel,
      claimDetected: claimDetected,
      evidencePoints: evidencePoints,
      verdictTitle: verdictTitle,
      confidenceDisplay: confidenceDisplay,
      whyExplanation: whyExplanation,
      evidenceSources: evidenceSources,
      rawJson: dto.rawJson,
      createdAt: DateTime.now(),
    );
  }

  @override
  Future<VerificationResult> verifySynchronous({
    String? url,
    String? directText,
    String language = 'en',
    CancelToken? cancelToken,
  }) async {
    final payload = VerifyRequestDto(
      url: url,
      directText: directText,
      languagePreference: language,
    ).toJson();

    final response = await _apiClient.postSync(
      ApiConstants.syncVerifyEndpoint,
      data: payload,
      cancelToken: cancelToken,
    );

    final dto = VerifyResponseDto.fromJson(response);
    final entity = mapDtoToEntity(dto);

    // Save automatically to offline database
    await AppDatabase.saveVerification(
      id: entity.id,
      url: entity.url,
      platform: entity.platform,
      contentType: entity.contentType,
      summaryText: entity.summaryText,
      claimDetected: entity.claimDetected,
      overallVerdict: entity.overallVerdict,
      overallConfidence: entity.overallConfidence,
      badgeLabel: entity.badgeLabel,
      verdictTitle: entity.verdictTitle,
      whyExplanation: entity.whyExplanation,
      rawJson: entity.rawJson,
      createdAt: entity.createdAt,
    );

    return entity;
  }

  @override
  Future<String> submitAsyncJob({
    String? url,
    String? directText,
    String language = 'en',
    CancelToken? cancelToken,
  }) async {
    final payload = VerifyRequestDto(
      url: url,
      directText: directText,
      languagePreference: language,
    ).toJson();

    final response = await _apiClient.postSync(
      ApiConstants.asyncVerifyEndpoint,
      data: payload,
      cancelToken: cancelToken,
    );

    return response['job_id'] as String;
  }

  @override
  Future<JobStatusDto> pollJobStatus(
    String jobId, {
    CancelToken? cancelToken,
  }) async {
    final response = await _apiClient.get(
      '${ApiConstants.jobStatusEndpoint}/$jobId',
      cancelToken: cancelToken,
    );

    final jobDto = JobStatusDto.fromJson(response);

    if (jobDto.isCompleted && jobDto.result != null) {
      final entity = mapDtoToEntity(jobDto.result!, customId: jobDto.jobId);
      await AppDatabase.saveVerification(
        id: entity.id,
        url: entity.url,
        platform: entity.platform,
        contentType: entity.contentType,
        summaryText: entity.summaryText,
        claimDetected: entity.claimDetected,
        overallVerdict: entity.overallVerdict,
        overallConfidence: entity.overallConfidence,
        badgeLabel: entity.badgeLabel,
        verdictTitle: entity.verdictTitle,
        whyExplanation: entity.whyExplanation,
        rawJson: entity.rawJson,
        createdAt: entity.createdAt,
      );
    }

    return jobDto;
  }

  @override
  Future<bool> checkHealth() async {
    try {
      final response = await _apiClient.get(ApiConstants.healthEndpoint);
      return response['status'] == 'healthy';
    } catch (_) {
      return false;
    }
  }
}
