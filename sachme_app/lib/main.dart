import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app/router.dart';
import 'core/database/app_database.dart';
import 'core/theme/app_theme.dart';
import 'features/settings/presentation/screens/settings_screen.dart';
import 'features/share_intent/services/share_intent_service.dart';
import 'features/verify/presentation/controllers/verify_controller.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  AppDatabase.initialize();

  final container = ProviderContainer();

  // Initialize native Share Intent service (Android ACTION_SEND / iOS Share Extension)
  final shareService = ShareIntentService(
    onContentReceived: (content) {
      container.read(verifyControllerProvider.notifier).verify(content);
      appRouter.go('/');
    },
  );
  shareService.initialize();

  runApp(
    UncontrolledProviderScope(container: container, child: const SachmeApp()),
  );
}

class SachmeApp extends ConsumerWidget {
  const SachmeApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);

    return MaterialApp.router(
      title: 'Sachme (सच में?)',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeMode,
      routerConfig: appRouter,
    );
  }
}
