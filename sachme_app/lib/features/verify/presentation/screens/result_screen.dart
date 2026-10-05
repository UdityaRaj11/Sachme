import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:share_plus/share_plus.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/utils/url_sanitizer.dart';
import '../../domain/entities/verification_result.dart';
import '../controllers/verify_controller.dart';
import '../widgets/claim_card.dart';
import '../widgets/evidence_card.dart';
import '../widgets/verdict_hero_card.dart';

class ResultScreen extends ConsumerWidget {
  final VerificationResult result;

  const ResultScreen({super.key, required this.result});

  void _shareResult(BuildContext context) {
    final buffer = StringBuffer();
    buffer.writeln('🔍 Sachme Verification Report');
    buffer.writeln('-----------------------------');
    buffer.writeln('Verdict: ${result.verdictTitle}');
    buffer.writeln('Certainty: ${result.overallConfidence}%');
    buffer.writeln();
    buffer.writeln('Claim Analyzed:');
    buffer.writeln('"${result.claimDetected}"');
    buffer.writeln();
    buffer.writeln('Why:');
    buffer.writeln(result.whyExplanation);
    buffer.writeln();
    if (result.evidenceSources.isNotEmpty) {
      buffer.writeln('Primary Evidence:');
      for (final src in result.evidenceSources.take(3)) {
        buffer.writeln('• ${src['source']}: ${src['url']}');
      }
    }
    buffer.writeln();
    buffer.writeln('Verified via Sachme (सच में?) — AI Information Firewall');

    SharePlus.instance.share(
      ShareParams(
        text: buffer.toString(),
        subject: 'Verification Result: ${result.claimDetected}',
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final platformName = UrlSanitizer.identifyPlatform(result.url);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: isDark ? AppColors.surfaceVariantDark : AppColors.surfaceVariantLight,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                platformName,
                style: AppTypography.labelSmall(
                  Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.share_outlined),
            tooltip: 'Share Verification Report',
            onPressed: () => _shareResult(context),
          ),
          IconButton(
            icon: const Icon(Icons.home_outlined),
            tooltip: 'Return Home',
            onPressed: () {
              ref.read(verifyControllerProvider.notifier).reset();
              context.go('/');
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(18, 12, 18, 40),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. Hero Verdict Card
            VerdictHeroCard(result: result),
            const SizedBox(height: 24),

            // 2. Claim Detected Box
            Text(
              'CLAIM ANALYZED',
              style: AppTypography.labelSmall(
                Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
              ),
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: isDark ? AppColors.borderDark : AppColors.borderLight,
                ),
              ),
              child: Text(
                '"${result.claimDetected}"',
                style: AppTypography.titleMedium(
                  Theme.of(context).colorScheme.onSurface,
                ).copyWith(
                  fontStyle: FontStyle.italic,
                  fontWeight: FontWeight.w600,
                  fontSize: 16,
                ),
              ),
            ),
            const SizedBox(height: 24),

            // 3. What We Found Section
            if (result.evidencePoints.isNotEmpty) ...[
              Text(
                'WHAT WE FOUND',
                style: AppTypography.labelSmall(
                  Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
              const SizedBox(height: 8),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: isDark ? AppColors.borderDark : AppColors.borderLight,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: result.evidencePoints.map((point) {
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Text(
                        point,
                        style: AppTypography.bodyMedium(
                          Theme.of(context).colorScheme.onSurface,
                        ).copyWith(height: 1.45),
                      ),
                    );
                  }).toList(),
                ),
              ),
              const SizedBox(height: 24),
            ],

            // 4. Claims and Evidence breakdown
            if (result.claims.isNotEmpty) ...[
              Text(
                'CLAIM BREAKDOWN & EVIDENCE',
                style: AppTypography.labelSmall(
                  Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
              const SizedBox(height: 8),
              ...result.claims.asMap().entries.map((entry) {
                return ClaimCard(
                  claim: entry.value,
                  index: entry.key + 1,
                );
              }),
            ] else if (result.allEvidence.isNotEmpty) ...[
              Text(
                'EVIDENCE SOURCES',
                style: AppTypography.labelSmall(
                  Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
              const SizedBox(height: 8),
              ...result.allEvidence.map((ev) => EvidenceCard(evidence: ev)),
            ],

            const SizedBox(height: 24),

            // Action Buttons
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () {
                      ref.read(verifyControllerProvider.notifier).reset();
                      context.go('/');
                    },
                    icon: const Icon(Icons.arrow_back, size: 18),
                    label: const Text('Verify Another'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => _shareResult(context),
                    icon: const Icon(Icons.share, size: 18),
                    label: const Text('Share Result'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.brandAccent,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                      elevation: 0,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
