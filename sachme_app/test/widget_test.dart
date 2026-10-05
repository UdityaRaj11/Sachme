import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sachme/core/database/app_database.dart';
import 'package:sachme/main.dart';

void main() {
  setUpAll(() {
    AppDatabase.initialize();
  });

  testWidgets('Sachme initial smoke test: displays dashboard and tabs', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: SachmeApp(),
      ),
    );
    await tester.pumpAndSettle();

    // Verify Brand title is displayed
    expect(find.text('Sachme'), findsOneWidget);

    // Verify primary tabs are rendered
    expect(find.text('Verify'), findsOneWidget);
    expect(find.text('History'), findsOneWidget);
    expect(find.text('Settings'), findsOneWidget);

    // Verify verification input action button is rendered
    expect(find.text('Verify with Sachme'), findsOneWidget);
  });
}
