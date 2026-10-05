import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/utils/url_sanitizer.dart';
import '../controllers/verify_controller.dart';
import '../controllers/verify_state.dart';
import '../widgets/verification_stepper.dart';

class VerifyingScreen extends ConsumerWidget {
  final VerifyProcessing state;

  const VerifyingScreen({super.key, required this.state});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final platformName = UrlSanitizer.identifyPlatform(state.inputContent);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Verifying with Sachme'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () {
            ref.read(verifyControllerProvider.notifier).cancel();
            context.go('/');
          },
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header Card
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
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: AppColors.brandAccent.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            platformName,
                            style: AppTypography.labelSmall(AppColors.brandAccent),
                          ),
                        ),
                        const Spacer(),
                        Text(
                          '${(state.progress * 100).toInt()}%',
                          style: AppTypography.titleMedium(
                            Theme.of(context).colorScheme.onSurface,
                          ).copyWith(fontWeight: FontWeight.w700),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text(
                      state.inputContent,
                      style: AppTypography.bodyMedium(
                        Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.75),
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),

              // Live Stepper
              Text(
                'LIVE VERIFICATION PIPELINE',
                style: AppTypography.labelSmall(
                  Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
              const SizedBox(height: 14),

              Expanded(
                child: VerificationStepper(
                  progress: state.progress,
                  currentStepDescription: state.currentStep,
                  status: state.status,
                ),
              ),

              // Bottom Cancel button
              Center(
                child: TextButton.icon(
                  onPressed: () {
                    ref.read(verifyControllerProvider.notifier).cancel();
                    context.go('/');
                  },
                  icon: const Icon(Icons.stop_circle_outlined, size: 18),
                  label: const Text('Cancel Verification'),
                  style: TextButton.styleFrom(
                    foregroundColor: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
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
