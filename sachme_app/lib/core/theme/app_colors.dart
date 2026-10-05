import 'package:flutter/material.dart';

/// Design tokens for Sachme ("Calm Trust Infrastructure")
abstract class AppColors {
  // Brand & Accent
  static const Color primary = Color(0xFF0F172A); // Slate 900
  static const Color primaryLight = Color(0xFF1E293B);
  static const Color brandAccent = Color(0xFF2563EB); // Vibrant Trust Blue

  // Verdict Colors - Epistemic & Calm (WCAG AAA compliant pairings)
  static const Color contradicted = Color(0xFFDC2626); // Crimson/Red
  static const Color contradictedContainerLight = Color(0xFFFEF2F2);
  static const Color contradictedContainerDark = Color(0xFF3B1517);

  static const Color misleading = Color(0xFFD97706); // Warm Amber
  static const Color misleadingContainerLight = Color(0xFFFFFBEB);
  static const Color misleadingContainerDark = Color(0xFF38230B);

  static const Color supported = Color(0xFF16A34A); // Pine Emerald
  static const Color supportedContainerLight = Color(0xFFF0FDF4);
  static const Color supportedContainerDark = Color(0xFF0F2C18);

  static const Color unverifiable = Color(0xFF6366F1); // Calm Indigo
  static const Color unverifiableContainerLight = Color(0xFFEEF2FF);
  static const Color unverifiableContainerDark = Color(0xFF1E1B4B);

  static const Color opinion = Color(0xFF0D9488); // Deep Teal
  static const Color opinionContainerLight = Color(0xFFF0FDFA);
  static const Color opinionContainerDark = Color(0xFF133430);

  // Neutral Scales - Light Mode
  static const Color bgLight = Color(0xFFF8FAFC);
  static const Color surfaceLight = Color(0xFFFFFFFF);
  static const Color surfaceVariantLight = Color(0xFFF1F5F9);
  static const Color borderLight = Color(0xFFE2E8F0);
  static const Color textPrimaryLight = Color(0xFF0F172A);
  static const Color textSecondaryLight = Color(0xFF475569);
  static const Color textTertiaryLight = Color(0xFF94A3B8);

  // Neutral Scales - Dark Mode
  static const Color bgDark = Color(0xFF090D14);
  static const Color surfaceDark = Color(0xFF111722);
  static const Color surfaceVariantDark = Color(0xFF1A2232);
  static const Color borderDark = Color(0xFF263248);
  static const Color textPrimaryDark = Color(0xFFF8FAFC);
  static const Color textSecondaryDark = Color(0xFF94A3B8);
  static const Color textTertiaryDark = Color(0xFF64748B);

  // Credibility Tiers
  static const Color tier1 = Color(0xFF0284C7); // Official/Gov/Science Sky
  static const Color tier2 = Color(0xFF8B5CF6); // Fact-Checker Purple
  static const Color tier3 = Color(0xFF64748B); // Web/UGC Slate
}
