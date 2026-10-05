import 'evidence.dart';

class ClaimEntity {
  final String claimId;
  final String claim;
  final String verdict;
  final int confidence;
  final List<EvidenceEntity> evidence;
  final String explanation;

  const ClaimEntity({
    required this.claimId,
    required this.claim,
    required this.verdict,
    required this.confidence,
    required this.evidence,
    required this.explanation,
  });
}
