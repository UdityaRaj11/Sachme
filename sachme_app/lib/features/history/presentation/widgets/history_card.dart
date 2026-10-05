import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/utils/url_sanitizer.dart';
import '../../../../core/utils/verdict_helper.dart';
import '../../domain/history_item.dart';

class HistoryCard extends StatelessWidget {
  final HistoryItem item;
  final VoidCallback onTap;
  final VoidCallback? onDelete;

  const HistoryCard({
    super.key,
    required this.item,
    required this.onTap,
    this.onDelete,
  });

  String _formatDate(DateTime dt) {
    final now = DateTime.now();
    final difference = now.difference(dt);
    if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else if (difference.inDays < 7) {
      return '${difference.inDays}d ago';
    } else {
      return DateFormat('MMM d').format(dt);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final category = VerdictHelper.fromString(item.overallVerdict);
    final verdictColor = VerdictHelper.getColor(category);
    final containerColor = VerdictHelper.getContainerColor(category, isDark);
    final iconData = VerdictHelper.getIcon(category);
    final platformName = UrlSanitizer.identifyPlatform(item.url);

    final cardContent = Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isDark ? AppColors.borderDark : AppColors.borderLight,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Verdict Icon Indicator
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: containerColor,
                  shape: BoxShape.circle,
                  border: Border.all(color: verdictColor.withValues(alpha: 0.3)),
                ),
                child: Icon(iconData, size: 20, color: verdictColor),
              ),
              const SizedBox(width: 14),

              // Title, platform, time
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.claimDetected.isNotEmpty
                          ? item.claimDetected
                          : item.summaryText,
                      style: AppTypography.titleMedium(
                        Theme.of(context).colorScheme.onSurface,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: isDark
                                ? AppColors.surfaceVariantDark
                                : AppColors.surfaceVariantLight,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            platformName,
                            style: AppTypography.labelSmall(
                              Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
                            ).copyWith(fontSize: 10),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          _formatDate(item.createdAt),
                          style: AppTypography.bodyMedium(
                            Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.45),
                          ).copyWith(fontSize: 11),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),

              // Confidence Score Chip
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: verdictColor.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      '${item.overallConfidence}%',
                      style: AppTypography.labelSmall(verdictColor).copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Icon(
                    Icons.chevron_right,
                    size: 18,
                    color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.3),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );

    if (onDelete != null) {
      return Dismissible(
        key: Key(item.id),
        direction: DismissDirection.endToStart,
        background: Container(
          alignment: Alignment.centerRight,
          padding: const EdgeInsets.only(right: 20),
          decoration: BoxDecoration(
            color: AppColors.contradicted,
            borderRadius: BorderRadius.circular(16),
          ),
          child: const Icon(Icons.delete_outline, color: Colors.white),
        ),
        onDismissed: (_) => onDelete!(),
        child: cardContent,
      );
    }

    return cardContent;
  }
}
