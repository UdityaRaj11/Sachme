class VerifyRequestDto {
  final String? url;
  final String? directText;
  final String languagePreference;

  const VerifyRequestDto({
    this.url,
    this.directText,
    this.languagePreference = 'en',
  });

  Map<String, dynamic> toJson() {
    return {
      'url': url,
      'direct_text': directText,
      'language_preference': languagePreference,
    };
  }
}

class ContentSummaryDto {
  final String? visual;
  final String text;
  final List<String> keyPoints;

  const ContentSummaryDto({
    this.visual,
    required this.text,
    required this.keyPoints,
  });

  factory ContentSummaryDto.fromJson(Map<String, dynamic> json) {
    return ContentSummaryDto(
      visual: json['visual'] as String?,
      text: json['text'] as String? ?? '',
      keyPoints: (json['key_points'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
    );
  }
}

class ContentSectionDto {
  final String url;
  final String platform;
  final String contentType;
  final String language;
  final ContentSummaryDto summary;

  const ContentSectionDto({
    required this.url,
    required this.platform,
    required this.contentType,
    required this.language,
    required this.summary,
  });

  factory ContentSectionDto.fromJson(Map<String, dynamic> json) {
    return ContentSectionDto(
      url: json['url'] as String? ?? '',
      platform: json['platform'] as String? ?? 'unknown',
      contentType: json['content_type'] as String? ?? 'unknown',
      language: json['language'] as String? ?? 'en',
      summary: json['summary'] != null
          ? ContentSummaryDto.fromJson(json['summary'] as Map<String, dynamic>)
          : const ContentSummaryDto(text: '', keyPoints: []),
    );
  }
}

class ClaimEvidenceItemDto {
  final String finding;
  final String type;
  final String source;
  final String url;
  final int credibilityScore;

  const ClaimEvidenceItemDto({
    required this.finding,
    required this.type,
    required this.source,
    required this.url,
    required this.credibilityScore,
  });

  factory ClaimEvidenceItemDto.fromJson(Map<String, dynamic> json) {
    return ClaimEvidenceItemDto(
      finding: json['finding'] as String? ?? '',
      type: json['type'] as String? ?? 'contextual',
      source: json['source'] as String? ?? 'Unknown Source',
      url: json['url'] as String? ?? '',
      credibilityScore: (json['credibility_score'] as num?)?.toInt() ?? 50,
    );
  }
}

class VerifiedClaimDto {
  final String claimId;
  final String claim;
  final String verdict;
  final int confidence;
  final List<ClaimEvidenceItemDto> evidence;
  final String explanation;

  const VerifiedClaimDto({
    required this.claimId,
    required this.claim,
    required this.verdict,
    required this.confidence,
    required this.evidence,
    required this.explanation,
  });

  factory VerifiedClaimDto.fromJson(Map<String, dynamic> json) {
    return VerifiedClaimDto(
      claimId: json['claim_id'] as String? ?? '',
      claim: json['claim'] as String? ?? '',
      verdict: json['verdict'] as String? ?? 'UNVERIFIABLE',
      confidence: (json['confidence'] as num?)?.toInt() ?? 50,
      evidence: (json['evidence'] as List<dynamic>?)
              ?.map((e) => ClaimEvidenceItemDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      explanation: json['explanation'] as String? ?? '',
    );
  }
}

class UserFacingUIDto {
  final String badgeLabel;
  final String claimDetected;
  final List<String> evidencePoints;
  final String verdictTitle;
  final String confidenceDisplay;
  final String whyExplanation;
  final List<Map<String, String>> evidenceSources;

  const UserFacingUIDto({
    required this.badgeLabel,
    required this.claimDetected,
    required this.evidencePoints,
    required this.verdictTitle,
    required this.confidenceDisplay,
    required this.whyExplanation,
    required this.evidenceSources,
  });

  factory UserFacingUIDto.fromJson(Map<String, dynamic> json) {
    final rawSources = json['evidence_sources'] as List<dynamic>? ?? [];
    final sources = rawSources.map((item) {
      if (item is Map) {
        return {
          'source': item['source']?.toString() ?? '',
          'url': item['url']?.toString() ?? '',
          'credibility': item['credibility']?.toString() ?? '',
        };
      }
      return <String, String>{};
    }).toList();

    return UserFacingUIDto(
      badgeLabel: json['badge_label'] as String? ?? '',
      claimDetected: json['claim_detected'] as String? ?? '',
      evidencePoints: (json['evidence_points'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      verdictTitle: json['verdict_title'] as String? ?? '',
      confidenceDisplay: json['confidence_display'] as String? ?? '',
      whyExplanation: json['why_explanation'] as String? ?? '',
      evidenceSources: sources,
    );
  }
}

class VerifyResponseDto {
  final String status;
  final ContentSectionDto content;
  final List<VerifiedClaimDto> claims;
  final String overallVerdict;
  final int overallConfidence;
  final UserFacingUIDto? userInterface;
  final Map<String, dynamic> rawJson;

  const VerifyResponseDto({
    required this.status,
    required this.content,
    required this.claims,
    required this.overallVerdict,
    required this.overallConfidence,
    this.userInterface,
    required this.rawJson,
  });

  factory VerifyResponseDto.fromJson(Map<String, dynamic> json) {
    return VerifyResponseDto(
      status: json['status'] as String? ?? 'success',
      content: json['content'] != null
          ? ContentSectionDto.fromJson(json['content'] as Map<String, dynamic>)
          : const ContentSectionDto(
              url: '',
              platform: 'unknown',
              contentType: 'text',
              language: 'en',
              summary: ContentSummaryDto(text: '', keyPoints: []),
            ),
      claims: (json['claims'] as List<dynamic>?)
              ?.map((e) => VerifiedClaimDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      overallVerdict: json['overall_verdict'] as String? ?? 'UNVERIFIABLE',
      overallConfidence: (json['overall_confidence'] as num?)?.toInt() ?? 50,
      userInterface: json['user_interface'] != null
          ? UserFacingUIDto.fromJson(json['user_interface'] as Map<String, dynamic>)
          : null,
      rawJson: json,
    );
  }
}
