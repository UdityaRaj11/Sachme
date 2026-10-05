import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/utils/url_sanitizer.dart';

class ClipboardBanner extends StatefulWidget {
  final void Function(String url) onVerifyTapped;

  const ClipboardBanner({super.key, required this.onVerifyTapped});

  @override
  State<ClipboardBanner> createState() => _ClipboardBannerState();
}

class _ClipboardBannerState extends State<ClipboardBanner> {
  String? _detectedUrl;
  String? _platformName;
  bool _dismissed = false;

  @override
  void initState() {
    super.initState();
    _checkClipboard();
  }

  Future<void> _checkClipboard() async {
    try {
      final data = await Clipboard.getData(Clipboard.kTextPlain);
      if (data?.text != null && data!.text!.isNotEmpty) {
        final extracted = UrlSanitizer.extractFirstUrl(data.text!);
        if (extracted != null && extracted.startsWith('http')) {
          if (mounted) {
            setState(() {
              _detectedUrl = extracted;
              _platformName = UrlSanitizer.identifyPlatform(extracted);
            });
          }
        }
      }
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    if (_detectedUrl == null || _dismissed) return const SizedBox.shrink();

    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isDark ? AppColors.surfaceVariantDark : AppColors.surfaceVariantLight,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.brandAccent.withValues(alpha: 0.3),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppColors.brandAccent.withValues(alpha: 0.12),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.content_paste_search_rounded,
              size: 20,
              color: AppColors.brandAccent,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Link copied from $_platformName',
                  style: AppTypography.labelLarge(
                    Theme.of(context).colorScheme.onSurface,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  _detectedUrl!,
                  style: AppTypography.bodyMedium(
                    Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
                  ).copyWith(fontSize: 12),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          ElevatedButton(
            onPressed: () {
              widget.onVerifyTapped(_detectedUrl!);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.brandAccent,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
              elevation: 0,
            ),
            child: const Text('Verify', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
          ),
          IconButton(
            icon: const Icon(Icons.close, size: 16),
            onPressed: () {
              setState(() {
                _dismissed = true;
              });
            },
          ),
        ],
      ),
    );
  }
}
