import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/utils/verdict_helper.dart';
import '../../domain/entities/evidence.dart';

class EvidenceCard extends StatelessWidget {
  final EvidenceEntity evidence;

  const EvidenceCard({super.key, required this.evidence});

  Color _getStanceColor(EvidenceStance stance) {
    switch (stance) {
      case EvidenceStance.contradicting:
        return AppColors.contradicted;
      case EvidenceStance.supporting:
        return AppColors.supported;
      case EvidenceStance.contextual:
        return AppColors.unverifiable;
    }
  }

  String _getStanceLabel(EvidenceStance stance) {
    switch (stance) {
      case EvidenceStance.contradicting:
        return 'Contradicts Claim';
      case EvidenceStance.supporting:
        return 'Supports Claim';
      case EvidenceStance.contextual:
        return 'Context';
    }
  }

  Future<void> _launchSourceUrl(BuildContext context) async {
    final uri = Uri.tryParse(evidence.url);
    if (uri != null && await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not open source link.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final stanceColor = _getStanceColor(evidence.stance);
    final tierColor = VerdictHelper.getTierColor(evidence.tier);
    final tierLabel = VerdictHelper.getTierLabel(evidence.tier);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isDark ? AppColors.borderDark : AppColors.borderLight,
        ),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Left color accent bar
              Container(
                width: 5,
                color: stanceColor,
              ),

              // Main content
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Header: Source name + Credibility Badge
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              evidence.source,
                              style: AppTypography.titleMedium(
                                Theme.of(context).colorScheme.onSurface,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: tierColor.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              'Score: ${evidence.credibilityScore}/100',
                              style: AppTypography.labelSmall(tierColor),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),

                      // Tier & Stance tags
                      Row(
                        children: [
                          Text(
                            tierLabel,
                            style: AppTypography.labelSmall(
                              Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.55),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: stanceColor.withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              _getStanceLabel(evidence.stance),
                              style: AppTypography.labelSmall(stanceColor),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),

                      // Finding excerpt
                      Text(
                        evidence.finding,
                        style: AppTypography.bodyMedium(
                          Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.9),
                        ).copyWith(height: 1.45),
                      ),
                      const SizedBox(height: 12),

                      // Link action button
                      if (evidence.url.isNotEmpty && evidence.url.startsWith('http'))
                        Align(
                          alignment: Alignment.centerRight,
                          child: InkWell(
                            onTap: () => _launchSourceUrl(context),
                            borderRadius: BorderRadius.circular(8),
                            child: Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Text(
                                    'View Primary Source',
                                    style: AppTypography.labelSmall(AppColors.brandAccent),
                                  ),
                                  const SizedBox(width: 4),
                                  const Icon(
                                    Icons.open_in_new_rounded,
                                    size: 13,
                                    color: AppColors.brandAccent,
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
