import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import 'package:sachme/features/history/presentation/controllers/history_controller.dart';
import 'package:sachme/features/history/presentation/widgets/history_card.dart';
import '../controllers/verify_controller.dart';
import '../controllers/verify_state.dart';
import '../widgets/clipboard_banner.dart';
import 'result_screen.dart';
import 'verifying_screen.dart';

class VerifyScreen extends ConsumerStatefulWidget {
  const VerifyScreen({super.key});

  @override
  ConsumerState<VerifyScreen> createState() => _VerifyScreenState();
}

class _VerifyScreenState extends ConsumerState<VerifyScreen> {
  final TextEditingController _inputController = TextEditingController();
  final FocusNode _focusNode = FocusNode();

  @override
  void dispose() {
    _inputController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _triggerVerification(String text) {
    if (text.trim().isEmpty) return;
    _focusNode.unfocus();
    ref.read(verifyControllerProvider.notifier).verify(text);
  }

  Future<void> _pasteFromClipboard() async {
    final data = await Clipboard.getData(Clipboard.kTextPlain);
    if (data?.text != null && data!.text!.isNotEmpty) {
      _inputController.text = data.text!;
    }
  }

  @override
  Widget build(BuildContext context) {
    final verifyState = ref.watch(verifyControllerProvider);
    final historyState = ref.watch(historyControllerProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // Direct routing based on active verification state
    if (verifyState is VerifyProcessing) {
      return VerifyingScreen(state: verifyState);
    } else if (verifyState is VerifySuccess) {
      return ResultScreen(result: verifyState.result);
    }

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Text(
              'Sachme',
              style: AppTypography.displayLarge(
                Theme.of(context).colorScheme.onSurface,
              ).copyWith(fontSize: 22),
            ),
            const SizedBox(width: 6),
            Text(
              '(सच में?)',
              style: AppTypography.titleMedium(AppColors.brandAccent).copyWith(fontSize: 16),
            ),
          ],
        ),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: AppColors.supported.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.supported.withValues(alpha: 0.3)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 7,
                  height: 7,
                  decoration: const BoxDecoration(
                    color: AppColors.supported,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 6),
                Text(
                  'Firewall Active',
                  style: AppTypography.labelSmall(AppColors.supported),
                ),
              ],
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Clipboard Intelligence Card
            ClipboardBanner(
              onVerifyTapped: (url) {
                _inputController.text = url;
                _triggerVerification(url);
              },
            ),

            // Error Card if previous verification failed
            if (verifyState is VerifyError) ...[
              Container(
                margin: const EdgeInsets.only(bottom: 20),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: isDark
                      ? AppColors.contradictedContainerDark
                      : AppColors.contradictedContainerLight,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: AppColors.contradicted.withValues(alpha: 0.3),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.error_outline, color: AppColors.contradicted, size: 20),
                        const SizedBox(width: 8),
                        Text(
                          'Verification Notice',
                          style: AppTypography.titleMedium(AppColors.contradicted),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      verifyState.message,
                      style: AppTypography.bodyMedium(
                        Theme.of(context).colorScheme.onSurface,
                      ),
                    ),
                    if (verifyState.canRetry) ...[
                      const SizedBox(height: 12),
                      Align(
                        alignment: Alignment.centerRight,
                        child: TextButton.icon(
                          onPressed: () {
                            _triggerVerification(verifyState.inputContent);
                          },
                          icon: const Icon(Icons.refresh, size: 16),
                          label: const Text('Try Again'),
                          style: TextButton.styleFrom(
                            foregroundColor: AppColors.contradicted,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],

            // Hero Prompt
            Text(
              'What would you like to verify?',
              style: AppTypography.headlineMedium(
                Theme.of(context).colorScheme.onSurface,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Share a post from Instagram, YouTube, X, or paste any suspicious claim or link.',
              style: AppTypography.bodyMedium(
                Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.65),
              ),
            ),
            const SizedBox(height: 20),

            // Input Box
            Container(
              decoration: BoxDecoration(
                color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: isDark ? AppColors.borderDark : AppColors.borderLight,
                  width: 1.5,
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: isDark ? 0.2 : 0.03),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  TextField(
                    controller: _inputController,
                    focusNode: _focusNode,
                    maxLines: 4,
                    minLines: 2,
                    decoration: InputDecoration(
                      hintText: 'Paste URL or forward message...',
                      hintStyle: AppTypography.bodyMedium(
                        Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.4),
                      ),
                      border: InputBorder.none,
                      isDense: true,
                    ),
                    style: AppTypography.bodyLarge(
                      Theme.of(context).colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          IconButton(
                            icon: const Icon(Icons.paste_rounded, size: 20),
                            tooltip: 'Paste from clipboard',
                            onPressed: _pasteFromClipboard,
                          ),
                          if (_inputController.text.isNotEmpty)
                            IconButton(
                              icon: const Icon(Icons.clear_rounded, size: 20),
                              tooltip: 'Clear',
                              onPressed: () {
                                setState(() {
                                  _inputController.clear();
                                });
                              },
                            ),
                        ],
                      ),
                      ElevatedButton.icon(
                        onPressed: () => _triggerVerification(_inputController.text),
                        icon: const Icon(Icons.shield_outlined, size: 18),
                        label: const Text('Verify with Sachme'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.brandAccent,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                          elevation: 0,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),

            // Sample Claims Section
            Text(
              'SAMPLE CLAIMS TO TEST',
              style: AppTypography.labelSmall(
                Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
              ),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _buildSampleChip(
                  label: '🎓 Govt ₹25,000 Student Scheme',
                  claim: 'Government is giving ₹25,000 to every student. Register now at http://free-scholarship.xyz',
                ),
                _buildSampleChip(
                  label: '🩺 WHO Lemon Water Cure',
                  claim: 'WHO announces hot lemon water kills 100% of cancer cells immediately.',
                ),
                _buildSampleChip(
                  label: '🛰️ ISRO Chandrayaan Mission',
                  claim: 'ISRO successfully lands Chandrayaan on lunar south pole.',
                ),
              ],
            ),
            const SizedBox(height: 32),

            // Recent Verifications
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'RECENT VERIFICATIONS',
                  style: AppTypography.labelSmall(
                    Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
                  ),
                ),
                if (historyState.items.isNotEmpty)
                  GestureDetector(
                    onTap: () => context.go('/history'),
                    child: Text(
                      'View All (${historyState.items.length})',
                      style: AppTypography.labelSmall(AppColors.brandAccent),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 12),

            if (historyState.items.isEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
                decoration: BoxDecoration(
                  color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: isDark ? AppColors.borderDark : AppColors.borderLight,
                  ),
                ),
                child: Column(
                  children: [
                    Icon(
                      Icons.history_toggle_off_rounded,
                      size: 32,
                      color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.3),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'No past verifications yet',
                      style: AppTypography.titleMedium(
                        Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Verifications you check will appear here for fast offline reference.',
                      textAlign: TextAlign.center,
                      style: AppTypography.bodyMedium(
                        Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.45),
                      ),
                    ),
                  ],
                ),
              )
            else
              ...historyState.items.take(3).map((item) {
                return HistoryCard(
                  item: item,
                  onTap: () {
                    final result = item.toVerificationResult();
                    ref.read(verifyControllerProvider.notifier).showHistoricalResult(result);
                  },
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _buildSampleChip({required String label, required String claim}) {
    return ActionChip(
      label: Text(label),
      onPressed: () {
        _inputController.text = claim;
        _triggerVerification(claim);
      },
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    );
  }
}
