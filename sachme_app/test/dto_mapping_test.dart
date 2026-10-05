import 'package:flutter_test/flutter_test.dart';
import 'package:sachme/features/verify/data/models/verify_response_dto.dart';
import 'package:sachme/features/verify/domain/entities/evidence.dart';

void main() {
  group('DTO Mapping & Section 10/11 Schema Tests', () {
    test('Parses complete Section 10 & 11 response accurately', () {
      final sampleJson = {
        "status": "success",
        "content": {
          "url": "text://direct-input",
          "platform": "text_direct",
          "content_type": "text",
          "language": "en",
          "summary": {
            "visual": null,
            "text": "Government is giving ₹25,000 to every student.",
            "key_points": [
              "Government is giving ₹25,000 to every student. Register now at http://free-scholarship.xyz"
            ]
          }
        },
        "claims": [
          {
            "claim_id": "c_1",
            "claim": "Government is giving ₹25,000 to every student",
            "verdict": "CONTRADICTED",
            "confidence": 94,
            "evidence": [
              {
                "finding": "PIB Fact Check: A viral message claiming financial assistance is completely fraudulent.",
                "type": "contradicting",
                "source": "Press Information Bureau (PIB)",
                "url": "https://pib.gov.in/FactCheck/FakeStudentScheme2026.html",
                "credibility_score": 96
              }
            ],
            "explanation": "EVIDENCE: Cross-checked against PIB. VERDICT: CONTRADICTED."
          }
        ],
        "overall_verdict": "CONTRADICTED",
        "overall_confidence": 94,
        "user_interface": {
          "badge_label": "❌ False / Disproven",
          "claim_detected": "Government is giving ₹25,000 to every student",
          "evidence_points": [
            "❌ Press Information Bureau (PIB): A viral message claiming financial assistance is completely fraudulent."
          ],
          "verdict_title": "Disproven / Misinformation",
          "confidence_display": "94%",
          "why_explanation": "Directly contradicted by credible reporting from Press Information Bureau (PIB).",
          "evidence_sources": [
            {
              "source": "Press Information Bureau (PIB)",
              "url": "https://pib.gov.in/FactCheck/FakeStudentScheme2026.html",
              "credibility": "96/100"
            }
          ]
        }
      };

      final dto = VerifyResponseDto.fromJson(sampleJson);

      expect(dto.status, equals('success'));
      expect(dto.overallVerdict, equals('CONTRADICTED'));
      expect(dto.overallConfidence, equals(94));
      expect(dto.claims.length, equals(1));

      final claim = dto.claims.first;
      expect(claim.claimId, equals('c_1'));
      expect(claim.confidence, equals(94));
      expect(claim.verdict, equals('CONTRADICTED'));
      expect(claim.evidence.length, equals(1));

      final ev = claim.evidence.first;
      expect(ev.source, equals('Press Information Bureau (PIB)'));
      expect(ev.credibilityScore, equals(96));
      expect(EvidenceEntity.parseStance(ev.type), equals(EvidenceStance.contradicting));

      expect(dto.userInterface, isNotNull);
      final ui = dto.userInterface!;
      expect(ui.badgeLabel, equals('❌ False / Disproven'));
      expect(ui.whyExplanation, contains('Press Information Bureau'));
      expect(ui.evidenceSources.first['credibility'], equals('96/100'));
    });
  });
}
