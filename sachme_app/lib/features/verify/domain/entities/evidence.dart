enum EvidenceStance {
  supporting,
  contradicting,
  contextual,
}

class EvidenceEntity {
  final String finding;
  final EvidenceStance stance;
  final String source;
  final String url;
  final int credibilityScore;
  final String tier;

  const EvidenceEntity({
    required this.finding,
    required this.stance,
    required this.source,
    required this.url,
    required this.credibilityScore,
    required this.tier,
  });

  static EvidenceStance parseStance(String stanceStr) {
    switch (stanceStr.toLowerCase().trim()) {
      case 'supporting':
        return EvidenceStance.supporting;
      case 'contradicting':
        return EvidenceStance.contradicting;
      case 'contextual':
      default:
        return EvidenceStance.contextual;
    }
  }
}
