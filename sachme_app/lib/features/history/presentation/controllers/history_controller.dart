import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/database/app_database.dart';
import '../../domain/history_item.dart';

class HistoryState {
  final List<HistoryItem> items;
  final bool isLoading;
  final String activeFilter; // 'ALL', 'CONTRADICTED', 'MISLEADING', 'SUPPORTED', 'UNVERIFIABLE'
  final String searchQuery;

  const HistoryState({
    this.items = const [],
    this.isLoading = false,
    this.activeFilter = 'ALL',
    this.searchQuery = '',
  });

  HistoryState copyWith({
    List<HistoryItem>? items,
    bool? isLoading,
    String? activeFilter,
    String? searchQuery,
  }) {
    return HistoryState(
      items: items ?? this.items,
      isLoading: isLoading ?? this.isLoading,
      activeFilter: activeFilter ?? this.activeFilter,
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }
}

final historyControllerProvider =
    NotifierProvider<HistoryController, HistoryState>(HistoryController.new);

class HistoryController extends Notifier<HistoryState> {
  @override
  HistoryState build() {
    // Initial fetch
    Future.microtask(() => loadHistory());
    return const HistoryState(isLoading: true);
  }

  Future<void> loadHistory() async {
    state = state.copyWith(isLoading: true);
    try {
      final rows = await AppDatabase.getHistory(
        verdictFilter: state.activeFilter == 'ALL' ? null : state.activeFilter,
        searchQuery: state.searchQuery.isEmpty ? null : state.searchQuery,
      );

      final items = rows.map((r) => HistoryItem.fromMap(r)).toList();
      state = state.copyWith(items: items, isLoading: false);
    } catch (_) {
      state = state.copyWith(isLoading: false);
    }
  }

  void setFilter(String filter) {
    if (state.activeFilter == filter) return;
    state = state.copyWith(activeFilter: filter);
    loadHistory();
  }

  void setSearchQuery(String query) {
    state = state.copyWith(searchQuery: query);
    loadHistory();
  }

  Future<void> deleteItem(String id) async {
    await AppDatabase.deleteVerification(id);
    loadHistory();
  }

  Future<void> clearAll() async {
    await AppDatabase.clearAllHistory();
    state = state.copyWith(items: []);
  }
}
