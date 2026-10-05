import '../../domain/entities/verification_result.dart';

sealed class VerifyState {
  const VerifyState();
}

class VerifyInitial extends VerifyState {
  const VerifyInitial();
}

class VerifyProcessing extends VerifyState {
  final String status;
  final String currentStep;
  final double progress; // 0.0 to 1.0
  final String inputContent;

  const VerifyProcessing({
    required this.status,
    required this.currentStep,
    required this.progress,
    required this.inputContent,
  });

  VerifyProcessing copyWith({
    String? status,
    String? currentStep,
    double? progress,
    String? inputContent,
  }) {
    return VerifyProcessing(
      status: status ?? this.status,
      currentStep: currentStep ?? this.currentStep,
      progress: progress ?? this.progress,
      inputContent: inputContent ?? this.inputContent,
    );
  }
}

class VerifySuccess extends VerifyState {
  final VerificationResult result;

  const VerifySuccess({required this.result});
}

class VerifyError extends VerifyState {
  final String message;
  final String? errorType;
  final bool canRetry;
  final String inputContent;

  const VerifyError({
    required this.message,
    this.errorType,
    this.canRetry = true,
    required this.inputContent,
  });
}
