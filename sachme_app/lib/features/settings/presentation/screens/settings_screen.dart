import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import 'package:sachme/features/verify/presentation/controllers/verify_controller.dart';

class ThemeModeNotifier extends Notifier<ThemeMode> {
  @override
  ThemeMode build() => ThemeMode.system;
  void setTheme(ThemeMode mode) => state = mode;
}

final themeModeProvider =
    NotifierProvider<ThemeModeNotifier, ThemeMode>(ThemeModeNotifier.new);

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  late final TextEditingController _serverController;
  bool _isCheckingHealth = false;
  bool? _isHealthy;

  @override
  void initState() {
    super.initState();
    final client = ref.read(apiClientProvider);
    _serverController = TextEditingController(text: client.currentBaseUrl);
  }

  @override
  void dispose() {
    _serverController.dispose();
    super.dispose();
  }

  Future<void> _testConnection() async {
    setState(() {
      _isCheckingHealth = true;
      _isHealthy = null;
    });

    final repo = ref.read(verifyRepositoryProvider);
    final healthy = await repo.checkHealth();

    if (mounted) {
      setState(() {
        _isCheckingHealth = false;
        _isHealthy = healthy;
      });
    }
  }

  void _saveServerUrl() {
    final newUrl = _serverController.text.trim();
    if (newUrl.isNotEmpty) {
      ref.read(apiClientProvider).updateBaseUrl(newUrl);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Verification service endpoint updated to: $newUrl')),
      );
      _testConnection();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final currentTheme = ref.watch(themeModeProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings & Trust'),
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        children: [
          // Section: Appearance
          Text(
            'APPEARANCE',
            style: AppTypography.labelSmall(
              Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
          ),
          const SizedBox(height: 8),
          Container(
            decoration: BoxDecoration(
              color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isDark ? AppColors.borderDark : AppColors.borderLight,
              ),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Theme Mode',
                  style: AppTypography.titleMedium(
                    Theme.of(context).colorScheme.onSurface,
                  ),
                ),
                DropdownButton<ThemeMode>(
                  value: currentTheme,
                  underline: const SizedBox.shrink(),
                  items: const [
                    DropdownMenuItem(value: ThemeMode.system, child: Text('System')),
                    DropdownMenuItem(value: ThemeMode.light, child: Text('Light')),
                    DropdownMenuItem(value: ThemeMode.dark, child: Text('Dark')),
                  ],
                  onChanged: (mode) {
                    if (mode != null) {
                      ref.read(themeModeProvider.notifier).setTheme(mode);
                    }
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Section: Connection & Backend
          Text(
            'SERVICE ENDPOINT',
            style: AppTypography.labelSmall(
              Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
          ),
          const SizedBox(height: 8),
          Container(
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
                TextField(
                  controller: _serverController,
                  decoration: InputDecoration(
                    labelText: 'API Base URL',
                    hintText: 'e.g. http://10.0.2.2:8000',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    TextButton.icon(
                      onPressed: _isCheckingHealth ? null : _testConnection,
                      icon: _isCheckingHealth
                          ? const SizedBox(
                              width: 14,
                              height: 14,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.wifi_tethering, size: 16),
                      label: Text(_isCheckingHealth ? 'Testing...' : 'Test Connection'),
                    ),
                    ElevatedButton(
                      onPressed: _saveServerUrl,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.brandAccent,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      child: const Text('Save'),
                    ),
                  ],
                ),
                if (_isHealthy != null) ...[
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Icon(
                        _isHealthy! ? Icons.check_circle : Icons.error,
                        size: 16,
                        color: _isHealthy! ? AppColors.supported : AppColors.contradicted,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        _isHealthy!
                            ? 'Connection successful: Backend healthy'
                            : 'Connection failed: Service unreachable',
                        style: AppTypography.labelSmall(
                          _isHealthy! ? AppColors.supported : AppColors.contradicted,
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Section: Epistemic Hierarchy
          Text(
            'EPISTEMIC SOURCE TIERS',
            style: AppTypography.labelSmall(
              Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
          ),
          const SizedBox(height: 8),
          Container(
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
                _buildTierRow(
                  tier: 'Tier 1 • Primary & Official',
                  color: AppColors.tier1,
                  desc: 'Government ministries (.gov, .nic.in), regulatory bodies (WHO, RBI, CDC, FDA), scientific journals (Nature, Science).',
                ),
                const Divider(height: 20),
                _buildTierRow(
                  tier: 'Tier 2 • Reputable Fact-Checkers',
                  color: AppColors.tier2,
                  desc: 'Accredited journalism & debunks (Alt News, PIB Fact Check, Reuters, AP News, BBC, PolitiFact).',
                ),
                const Divider(height: 20),
                _buildTierRow(
                  tier: 'Tier 3 • General Web & Social',
                  color: AppColors.tier3,
                  desc: 'Public blogs, forums, user-generated comments. Max confidence capped at 65% when relying exclusively on Tier 3.',
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Section: About
          Center(
            child: Column(
              children: [
                Text(
                  'Sachme • सच में?',
                  style: AppTypography.titleMedium(
                    Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '"Don\'t tell people what to believe. Show them the evidence."',
                  style: AppTypography.bodyMedium(
                    Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
                  ).copyWith(fontStyle: FontStyle.italic),
                ),
                const SizedBox(height: 4),
                Text(
                  'v1.0.0 (Build 1)',
                  style: AppTypography.labelSmall(
                    Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.4),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildTierRow({required String tier, required Color color, required String desc}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(color: color, shape: BoxShape.circle),
            ),
            const SizedBox(width: 8),
            Text(tier, style: AppTypography.titleMedium(color).copyWith(fontSize: 14)),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          desc,
          style: AppTypography.bodyMedium(
            Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
          ).copyWith(fontSize: 12),
        ),
      ],
    );
  }
}
