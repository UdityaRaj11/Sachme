import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';

class VerificationStepper extends StatelessWidget {
  final double progress; // 0.0 to 1.0
  final String currentStepDescription;
  final String status;

  const VerificationStepper({
    super.key,
    required this.progress,
    required this.currentStepDescription,
    required this.status,
  });

  static const List<Map<String, dynamic>> _steps = [
    {
      'title': 'Safety & Format Verification',
      'threshold': 0.15,
      'statusKey': 'classifying',
    },
    {
      'title': 'Content & Claim Extraction',
      'threshold': 0.35,
      'statusKey': 'extracting',
    },
    {
      'title': 'Official & Fact-Checker Search',
      'threshold': 0.65,
      'statusKey': 'retrieving_evidence',
    },
    {
      'title': 'Epistemic Cross-Examination',
      'threshold': 0.85,
      'statusKey': 'verifying',
    },
  ];

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Top Progress bar
        ClipRRect(
          borderRadius: BorderRadius.circular(10),
          child: LinearProgressIndicator(
            value: progress.clamp(0.05, 1.0),
            minHeight: 6,
            backgroundColor: isDark
                ? Colors.white.withValues(alpha: 0.08)
                : Colors.black.withValues(alpha: 0.06),
            valueColor: const AlwaysStoppedAnimation<Color>(AppColors.brandAccent),
          ),
        ),
        const SizedBox(height: 24),

        // Stepper items
        ...List.generate(_steps.length, (index) {
          final step = _steps[index];
          final threshold = step['threshold'] as double;
          final isCompleted = progress >= threshold + 0.18;
          final isActive = progress >= threshold && !isCompleted;

          return Padding(
            padding: const EdgeInsets.only(bottom: 20),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Icon indicator
                Container(
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isCompleted
                        ? AppColors.supported
                        : (isActive
                            ? AppColors.brandAccent.withValues(alpha: 0.2)
                            : (isDark ? AppColors.surfaceVariantDark : AppColors.surfaceVariantLight)),
                    border: Border.all(
                      color: isCompleted
                          ? AppColors.supported
                          : (isActive ? AppColors.brandAccent : AppColors.borderLight),
                      width: 1.5,
                    ),
                  ),
                  child: Center(
                    child: isCompleted
                        ? const Icon(Icons.check, size: 16, color: Colors.white)
                        : (isActive
                            ? const SizedBox(
                                width: 12,
                                height: 12,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor: AlwaysStoppedAnimation<Color>(AppColors.brandAccent),
                                ),
                              )
                            : Text(
                                '${index + 1}',
                                style: AppTypography.labelSmall(
                                  Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.4),
                                ),
                              )),
                  ),
                ),
                const SizedBox(width: 14),

                // Label and description
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        step['title'] as String,
                        style: AppTypography.titleMedium(
                          isActive
                              ? Theme.of(context).colorScheme.onSurface
                              : (isCompleted
                                  ? Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.75)
                                  : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.4)),
                        ).copyWith(
                          fontWeight: isActive ? FontWeight.w700 : FontWeight.w500,
                        ),
                      ),
                      if (isActive && currentStepDescription.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          currentStepDescription,
                          style: AppTypography.bodyMedium(AppColors.brandAccent).copyWith(
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }
}
