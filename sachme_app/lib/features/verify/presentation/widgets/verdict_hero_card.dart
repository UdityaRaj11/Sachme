import 'package:flutter/material.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/utils/verdict_helper.dart';
import '../../domain/entities/verification_result.dart';
import 'confidence_gauge.dart';

class VerdictHeroCard extends StatelessWidget {
  final VerificationResult result;

  const VerdictHeroCard({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final category = VerdictHelper.fromString(result.overallVerdict);
    final verdictColor = VerdictHelper.getColor(category);
    final containerColor = VerdictHelper.getContainerColor(category, isDark);
    final iconData = VerdictHelper.getIcon(category);

    return Container(
      decoration: BoxDecoration(
        color: containerColor,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: verdictColor.withValues(alpha: 0.35),
          width: 1.5,
        ),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Top Row: Verdict Chip + Confidence Gauge
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Badge & Title
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: verdictColor.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: verdictColor.withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(iconData, size: 14, color: verdictColor),
                          const SizedBox(width: 5),
                          Text(
                            result.badgeLabel.isNotEmpty
                                ? result.badgeLabel
                                : VerdictHelper.getBadgeLabel(category),
                            style: AppTypography.labelSmall(verdictColor),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      result.verdictTitle.isNotEmpty
                          ? result.verdictTitle
                          : VerdictHelper.getDisplayTitle(category),
                      style: AppTypography.displayLarge(
                        Theme.of(context).colorScheme.onSurface,
                      ).copyWith(fontSize: 22),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 16),
              // Confidence Dial
              ConfidenceGauge(
                confidence: result.overallConfidence,
                color: verdictColor,
                size: 74,
              ),
            ],
          ),
          const SizedBox(height: 16),

          // 1-Sentence "Why" Explanation
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: isDark
                  ? Colors.black.withValues(alpha: 0.25)
                  : Colors.white.withValues(alpha: 0.7),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: isDark
                    ? Colors.white.withValues(alpha: 0.08)
                    : Colors.black.withValues(alpha: 0.05),
              ),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  Icons.psychology_outlined,
                  size: 20,
                  color: verdictColor,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'WHY THIS VERDICT?',
                        style: AppTypography.labelSmall(verdictColor),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        result.whyExplanation,
                        style: AppTypography.bodyMedium(
                          Theme.of(context).colorScheme.onSurface,
                        ).copyWith(height: 1.4),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
