import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_typography.dart';
import '../../../../core/utils/verdict_helper.dart';
import '../../domain/entities/claim.dart';
import 'evidence_card.dart';

class ClaimCard extends StatefulWidget {
  final ClaimEntity claim;
  final int index;

  const ClaimCard({
    super.key,
    required this.claim,
    required this.index,
  });

  @override
  State<ClaimCard> createState() => _ClaimCardState();
}

class _ClaimCardState extends State<ClaimCard> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final category = VerdictHelper.fromString(widget.claim.verdict);
    final verdictColor = VerdictHelper.getColor(category);

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
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
          // Header: Claim number, badge, confidence
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: verdictColor.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        VerdictHelper.getBadgeLabel(category),
                        style: AppTypography.labelSmall(verdictColor),
                      ),
                    ),
                    Text(
                      '${widget.claim.confidence}% Certainty',
                      style: AppTypography.labelSmall(
                        Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(
                  widget.claim.claim,
                  style: AppTypography.titleMedium(
                    Theme.of(context).colorScheme.onSurface,
                  ).copyWith(fontSize: 16),
                ),
              ],
            ),
          ),

          // Collapsible evidence toggle
          if (widget.claim.evidence.isNotEmpty) ...[
            const Divider(height: 1),
            InkWell(
              onTap: () {
                setState(() {
                  _isExpanded = !_isExpanded;
                });
              },
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '${widget.claim.evidence.length} Evidence Sources',
                      style: AppTypography.labelSmall(AppColors.brandAccent),
                    ),
                    Icon(
                      _isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                      size: 18,
                      color: AppColors.brandAccent,
                    ),
                  ],
                ),
              ),
            ),
            if (_isExpanded)
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 4, 12, 12),
                child: Column(
                  children: widget.claim.evidence
                      .map((ev) => EvidenceCard(evidence: ev))
                      .toList(),
                ),
              ),
          ],
        ],
      ),
    );
  }
}
