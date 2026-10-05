import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

enum VerdictCategory {
  contradicted,
  misleading,
  supported,
  unverifiable,
  opinion,
  unknown,
}

class VerdictHelper {
  static VerdictCategory fromString(String? verdict) {
    if (verdict == null) return VerdictCategory.unknown;
    switch (verdict.toUpperCase().trim()) {
      case 'CONTRADICTED':
      case 'FALSE':
      case 'DISPROVEN':
        return VerdictCategory.contradicted;
      case 'MISLEADING':
      case 'PARTIALLY_TRUE':
      case 'NEEDS_CONTEXT':
        return VerdictCategory.misleading;
      case 'SUPPORTED':
      case 'TRUE':
      case 'VERIFIED':
        return VerdictCategory.supported;
      case 'UNVERIFIABLE':
      case 'UNCONFIRMED':
        return VerdictCategory.unverifiable;
      case 'OPINION':
      case 'SATIRE':
        return VerdictCategory.opinion;
      default:
        return VerdictCategory.unknown;
    }
  }

  static Color getColor(VerdictCategory category) {
    switch (category) {
      case VerdictCategory.contradicted:
        return AppColors.contradicted;
      case VerdictCategory.misleading:
        return AppColors.misleading;
      case VerdictCategory.supported:
        return AppColors.supported;
      case VerdictCategory.unverifiable:
        return AppColors.unverifiable;
      case VerdictCategory.opinion:
        return AppColors.opinion;
      case VerdictCategory.unknown:
        return AppColors.tier3;
    }
  }

  static Color getContainerColor(VerdictCategory category, bool isDark) {
    switch (category) {
      case VerdictCategory.contradicted:
        return isDark
            ? AppColors.contradictedContainerDark
            : AppColors.contradictedContainerLight;
      case VerdictCategory.misleading:
        return isDark
            ? AppColors.misleadingContainerDark
            : AppColors.misleadingContainerLight;
      case VerdictCategory.supported:
        return isDark
            ? AppColors.supportedContainerDark
            : AppColors.supportedContainerLight;
      case VerdictCategory.unverifiable:
        return isDark
            ? AppColors.unverifiableContainerDark
            : AppColors.unverifiableContainerLight;
      case VerdictCategory.opinion:
        return isDark
            ? AppColors.opinionContainerDark
            : AppColors.opinionContainerLight;
      case VerdictCategory.unknown:
        return isDark ? AppColors.surfaceVariantDark : AppColors.surfaceVariantLight;
    }
  }

  static IconData getIcon(VerdictCategory category) {
    switch (category) {
      case VerdictCategory.contradicted:
        return Icons.cancel_rounded;
      case VerdictCategory.misleading:
        return Icons.warning_amber_rounded;
      case VerdictCategory.supported:
        return Icons.check_circle_rounded;
      case VerdictCategory.unverifiable:
        return Icons.help_outline_rounded;
      case VerdictCategory.opinion:
        return Icons.chat_bubble_outline_rounded;
      case VerdictCategory.unknown:
        return Icons.info_outline_rounded;
    }
  }

  static String getDisplayTitle(VerdictCategory category) {
    switch (category) {
      case VerdictCategory.contradicted:
        return 'Disproven / False';
      case VerdictCategory.misleading:
        return 'Misleading / Missing Context';
      case VerdictCategory.supported:
        return 'Verified Authentic';
      case VerdictCategory.unverifiable:
        return 'Unverifiable / No Record';
      case VerdictCategory.opinion:
        return 'Subjective Opinion';
      case VerdictCategory.unknown:
        return 'Information Review';
    }
  }

  static String getBadgeLabel(VerdictCategory category) {
    switch (category) {
      case VerdictCategory.contradicted:
        return '❌ Disproven';
      case VerdictCategory.misleading:
        return '⚠️ Misleading';
      case VerdictCategory.supported:
        return '✅ Verified True';
      case VerdictCategory.unverifiable:
        return '❓ Unverified';
      case VerdictCategory.opinion:
        return '💬 Opinion';
      case VerdictCategory.unknown:
        return 'ℹ️ Information';
    }
  }

  static Color getTierColor(String? tier) {
    if (tier == null) return AppColors.tier3;
    final lower = tier.toLowerCase();
    if (lower.contains('tier_1') || lower.contains('official') || lower.contains('primary')) {
      return AppColors.tier1;
    }
    if (lower.contains('tier_2') || lower.contains('secondary') || lower.contains('news')) {
      return AppColors.tier2;
    }
    return AppColors.tier3;
  }

  static String getTierLabel(String? tier) {
    if (tier == null) return 'General Web';
    final lower = tier.toLowerCase();
    if (lower.contains('tier_1') || lower.contains('official') || lower.contains('primary')) {
      return 'Tier 1 • Official / Govt';
    }
    if (lower.contains('tier_2') || lower.contains('secondary') || lower.contains('news')) {
      return 'Tier 2 • Reputable News & Fact-Check';
    }
    return 'Tier 3 • General Web & Social';
  }
}
