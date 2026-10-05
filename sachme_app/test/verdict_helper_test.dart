import 'package:flutter_test/flutter_test.dart';
import 'package:sachme/core/theme/app_colors.dart';
import 'package:sachme/core/utils/verdict_helper.dart';

void main() {
  group('VerdictHelper Tests', () {
    test('Parses verdict string categories correctly', () {
      expect(VerdictHelper.fromString('CONTRADICTED'), equals(VerdictCategory.contradicted));
      expect(VerdictHelper.fromString('FALSE'), equals(VerdictCategory.contradicted));
      expect(VerdictHelper.fromString('MISLEADING'), equals(VerdictCategory.misleading));
      expect(VerdictHelper.fromString('SUPPORTED'), equals(VerdictCategory.supported));
      expect(VerdictHelper.fromString('TRUE'), equals(VerdictCategory.supported));
      expect(VerdictHelper.fromString('UNVERIFIABLE'), equals(VerdictCategory.unverifiable));
      expect(VerdictHelper.fromString('OPINION'), equals(VerdictCategory.opinion));
      expect(VerdictHelper.fromString(null), equals(VerdictCategory.unknown));
    });

    test('Maps appropriate verdict colors', () {
      expect(
        VerdictHelper.getColor(VerdictCategory.contradicted),
        equals(AppColors.contradicted),
      );
      expect(
        VerdictHelper.getColor(VerdictCategory.misleading),
        equals(AppColors.misleading),
      );
      expect(
        VerdictHelper.getColor(VerdictCategory.supported),
        equals(AppColors.supported),
      );
      expect(
        VerdictHelper.getColor(VerdictCategory.unverifiable),
        equals(AppColors.unverifiable),
      );
    });

    test('Provides clear tier labels', () {
      expect(VerdictHelper.getTierLabel('tier_1_primary'), contains('Tier 1'));
      expect(VerdictHelper.getTierLabel('tier_2_secondary'), contains('Tier 2'));
      expect(VerdictHelper.getTierLabel('tier_3_other'), contains('Tier 3'));
    });
  });
}
