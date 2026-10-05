import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../../../core/theme/app_typography.dart';

class ConfidenceGauge extends StatefulWidget {
  final int confidence; // 0 to 100
  final Color color;
  final double size;

  const ConfidenceGauge({
    super.key,
    required this.confidence,
    required this.color,
    this.size = 72,
  });

  @override
  State<ConfidenceGauge> createState() => _ConfidenceGaugeState();
}

class _ConfidenceGaugeState extends State<ConfidenceGauge>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1100),
    );
    _animation = Tween<double>(
      begin: 0.0,
      end: widget.confidence / 100.0,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutCubic,
    ));
    _controller.forward();
  }

  @override
  void didUpdateWidget(covariant ConfidenceGauge oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.confidence != widget.confidence) {
      _animation = Tween<double>(
        begin: _animation.value,
        end: widget.confidence / 100.0,
      ).animate(CurvedAnimation(
        parent: _controller,
        curve: Curves.easeOutCubic,
      ));
      _controller.forward(from: 0.0);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return SizedBox(
      width: widget.size,
      height: widget.size,
      child: AnimatedBuilder(
        animation: _animation,
        builder: (context, child) {
          final value = _animation.value;
          final currentPercent = (value * 100).toInt();

          return CustomPaint(
            painter: _GaugePainter(
              progress: value,
              color: widget.color,
              trackColor: isDark
                  ? Colors.white.withValues(alpha: 0.08)
                  : Colors.black.withValues(alpha: 0.06),
              strokeWidth: 6,
            ),
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '$currentPercent%',
                    style: AppTypography.titleMedium(
                      Theme.of(context).colorScheme.onSurface,
                    ).copyWith(
                      fontWeight: FontWeight.w700,
                      fontSize: widget.size * 0.24,
                    ),
                  ),
                  Text(
                    'Certainty',
                    style: AppTypography.labelSmall(
                      Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
                    ).copyWith(fontSize: widget.size * 0.12),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

class _GaugePainter extends CustomPainter {
  final double progress;
  final Color color;
  final Color trackColor;
  final double strokeWidth;

  _GaugePainter({
    required this.progress,
    required this.color,
    required this.trackColor,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width - strokeWidth) / 2;

    // Track
    final trackPaint = Paint()
      ..color = trackColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    canvas.drawCircle(center, radius, trackPaint);

    // Active arc
    final activePaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    const startAngle = -math.pi / 2;
    final sweepAngle = 2 * math.pi * progress;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      sweepAngle,
      false,
      activePaint,
    );
  }

  @override
  bool shouldRepaint(covariant _GaugePainter oldDelegate) {
    return oldDelegate.progress != progress ||
        oldDelegate.color != color ||
        oldDelegate.trackColor != trackColor;
  }
}
