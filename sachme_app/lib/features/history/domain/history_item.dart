import 'dart:convert';
import '../../verify/data/models/verify_response_dto.dart';
import '../../verify/domain/entities/claim.dart';
import '../../verify/domain/entities/evidence.dart';
import '../../verify/domain/entities/verification_result.dart';

class HistoryItem {
  final String id;
  final String url;
  final String platform;
  final String contentType;
  final String summaryText;
  final String claimDetected;
  final String overallVerdict;
  final int overallConfidence;
  final String badgeLabel;
  final String verdictTitle;
  final String whyExplanation;
  final String rawResponseJson;
  final DateTime createdAt;
  final bool isBookmarked;

  const HistoryItem({
    required this.id,
    required this.url,
    required this.platform,
    required this.contentType,
    required this.summaryText,
    required this.claimDetected,
    required this.overallVerdict,
    required this.overallConfidence,
    required this.badgeLabel,
    required this.verdictTitle,
    required this.whyExplanation,
    required this.rawResponseJson,
    required this.createdAt,
    required this.isBookmarked,
  });

  factory HistoryItem.fromMap(Map<String, dynamic> map) {
    return HistoryItem(
      id: map['id'] as String? ?? '',
      url: map['url'] as String? ?? '',
      platform: map['platform'] as String? ?? 'Web',
      contentType: map['content_type'] as String? ?? 'article',
      summaryText: map['summary_text'] as String? ?? '',
      claimDetected: map['claim_detected'] as String? ?? '',
      overallVerdict: map['overall_verdict'] as String? ?? 'UNVERIFIABLE',
      overallConfidence: (map['overall_confidence'] as num?)?.toInt() ?? 50,
      badgeLabel: map['badge_label'] as String? ?? '',
      verdictTitle: map['verdict_title'] as String? ?? '',
      whyExplanation: map['why_explanation'] as String? ?? '',
      rawResponseJson: map['raw_response_json'] as String? ?? '{}',
      createdAt: map['created_at'] != null
          ? DateTime.tryParse(map['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
      isBookmarked: (map['is_bookmarked'] as int? ?? 0) == 1,
    );
  }

  /// Converts stored JSON into full VerificationResult entity
  VerificationResult toVerificationResult() {
    try {
      final decoded = jsonDecode(rawResponseJson) as Map<String, dynamic>;
      final dto = VerifyResponseDto.fromJson(decoded);

      return VerificationResult(
        id: id,
        url: url,
        platform: platform,
        contentType: contentType,
        summaryText: summaryText,
        keyPoints: dto.content.summary.keyPoints,
        claims: dto.claims.map((c) {
          final ev = c.evidence.map((e) {
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
            evidence: ev,
            explanation: c.explanation,
          );
        }).toList(),
        overallVerdict: overallVerdict,
        overallConfidence: overallConfidence,
        badgeLabel: badgeLabel,
        claimDetected: claimDetected,
        evidencePoints: dto.userInterface?.evidencePoints ?? [],
        verdictTitle: verdictTitle,
        confidenceDisplay: '$overallConfidence%',
        whyExplanation: whyExplanation,
        evidenceSources: dto.userInterface?.evidenceSources ?? [],
        rawJson: decoded,
        createdAt: createdAt,
      );
    } catch (_) {
      // Fallback if raw JSON corrupted
      return VerificationResult(
        id: id,
        url: url,
        platform: platform,
        contentType: contentType,
        summaryText: summaryText,
        keyPoints: [],
        claims: [],
        overallVerdict: overallVerdict,
        overallConfidence: overallConfidence,
        badgeLabel: badgeLabel,
        claimDetected: claimDetected,
        evidencePoints: [],
        verdictTitle: verdictTitle,
        confidenceDisplay: '$overallConfidence%',
        whyExplanation: whyExplanation,
        evidenceSources: [],
        rawJson: {},
        createdAt: createdAt,
      );
    }
  }
}
