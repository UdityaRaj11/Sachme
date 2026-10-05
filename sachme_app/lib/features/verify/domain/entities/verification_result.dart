import 'claim.dart';
import 'evidence.dart';

class VerificationResult {
  final String id;
  final String url;
  final String platform;
  final String contentType;
  final String summaryText;
  final List<String> keyPoints;
  final List<ClaimEntity> claims;
  final String overallVerdict;
  final int overallConfidence;
  final String badgeLabel;
  final String claimDetected;
  final List<String> evidencePoints;
  final String verdictTitle;
  final String confidenceDisplay;
  final String whyExplanation;
  final List<Map<String, String>> evidenceSources;
  final Map<String, dynamic> rawJson;
  final DateTime createdAt;

  const VerificationResult({
    required this.id,
    required this.url,
    required this.platform,
    required this.contentType,
    required this.summaryText,
    required this.keyPoints,
    required this.claims,
    required this.overallVerdict,
    required this.overallConfidence,
    required this.badgeLabel,
    required this.claimDetected,
    required this.evidencePoints,
    required this.verdictTitle,
    required this.confidenceDisplay,
    required this.whyExplanation,
    required this.evidenceSources,
    required this.rawJson,
    required this.createdAt,
  });

  /// All evidence items flattened across claims
  List<EvidenceEntity> get allEvidence {
    final list = <EvidenceEntity>[];
    for (final claim in claims) {
      list.addAll(claim.evidence);
    }
    return list;
  }
}
