import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import 'package:sachme/features/verify/presentation/controllers/verify_controller.dart';
import '../controllers/history_controller.dart';
import '../widgets/history_card.dart';

class HistoryScreen extends ConsumerWidget {
  const HistoryScreen({super.key});

  static const List<Map<String, String>> _filterOptions = [
    {'label': 'All', 'filter': 'ALL'},
    {'label': '❌ Disproven', 'filter': 'CONTRADICTED'},
    {'label': '⚠️ Misleading', 'filter': 'MISLEADING'},
    {'label': '✅ Verified', 'filter': 'SUPPORTED'},
    {'label': '❓ Unverified', 'filter': 'UNVERIFIABLE'},
  ];

  void _showClearConfirmDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Clear All History?'),
        content: const Text(
          'This will remove all stored verification records from this device. This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              ref.read(historyControllerProvider.notifier).clearAll();
              Navigator.pop(ctx);
            },
            style: TextButton.styleFrom(foregroundColor: AppColors.contradicted),
            child: const Text('Clear All'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(historyControllerProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('History Vault'),
        actions: [
          if (state.items.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep_outlined),
              tooltip: 'Clear History',
              onPressed: () => _showClearConfirmDialog(context, ref),
            ),
        ],
      ),
      body: Column(
        children: [
          // Search Bar
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
            child: TextField(
              onChanged: (val) {
                ref.read(historyControllerProvider.notifier).setSearchQuery(val);
              },
              decoration: InputDecoration(
                hintText: 'Search claims or sources...',
                hintStyle: AppTypography.bodyMedium(
                  Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.4),
                ),
                prefixIcon: const Icon(Icons.search, size: 20),
                filled: true,
                fillColor: isDark
                    ? AppColors.surfaceVariantDark
                    : AppColors.surfaceVariantLight,
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),

          // Filter Chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: _filterOptions.map((opt) {
                final isSelected = state.activeFilter == opt['filter'];
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(opt['label']!),
                    selected: isSelected,
                    onSelected: (_) {
                      ref
                          .read(historyControllerProvider.notifier)
                          .setFilter(opt['filter']!);
                    },
                    selectedColor: AppColors.brandAccent.withValues(alpha: 0.15),
                    checkmarkColor: AppColors.brandAccent,
                    labelStyle: AppTypography.labelSmall(
                      isSelected
                          ? AppColors.brandAccent
                          : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 12),

          // Items List
          Expanded(
            child: state.items.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.inbox_outlined,
                          size: 48,
                          color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.3),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          state.searchQuery.isNotEmpty
                              ? 'No results matching "${state.searchQuery}"'
                              : 'No verifications found',
                          style: AppTypography.titleMedium(
                            Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
                          ),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                    itemCount: state.items.length,
                    itemBuilder: (context, index) {
                      final item = state.items[index];
                      return HistoryCard(
                        item: item,
                        onTap: () {
                          final result = item.toVerificationResult();
                          ref
                              .read(verifyControllerProvider.notifier)
                              .showHistoricalResult(result);
                          context.go('/');
                        },
                        onDelete: () {
                          ref
                              .read(historyControllerProvider.notifier)
                              .deleteItem(item.id);
                        },
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
