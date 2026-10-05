import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_exceptions.dart';
import '../../../../core/utils/url_sanitizer.dart';
import '../../data/repositories/verify_repository_impl.dart';
import '../../domain/repositories/verify_repository.dart';
import 'verify_state.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient();
});

final verifyRepositoryProvider = Provider<VerifyRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  return VerifyRepositoryImpl(apiClient: client);
});

final verifyControllerProvider =
    NotifierProvider<VerifyController, VerifyState>(VerifyController.new);

class VerifyController extends Notifier<VerifyState> {
  CancelToken? _cancelToken;
  Timer? _pollingTimer;

  @override
  VerifyState build() {
    ref.onDispose(() {
      _cancelToken?.cancel();
      _pollingTimer?.cancel();
    });
    return const VerifyInitial();
  }

  void cancel() {
    _cancelToken?.cancel('User cancelled verification');
    _pollingTimer?.cancel();
    state = const VerifyInitial();
  }

  void reset() {
    state = const VerifyInitial();
  }

  Future<void> verify(String input) async {
    final cleanInput = input.trim();
    if (cleanInput.isEmpty) return;

    _cancelToken?.cancel();
    _pollingTimer?.cancel();
    _cancelToken = CancelToken();

    final repo = ref.read(verifyRepositoryProvider);

    final extractedUrl = UrlSanitizer.extractFirstUrl(cleanInput);
    final String? targetUrl = extractedUrl;
    final String? directText = extractedUrl == null ? cleanInput : null;

    state = VerifyProcessing(
      status: 'classifying',
      currentStep: 'Identifying platform and content format...',
      progress: 0.15,
      inputContent: cleanInput,
    );

    try {
      // Start asynchronous job
      final jobId = await repo.submitAsyncJob(
        url: targetUrl,
        directText: directText,
        cancelToken: _cancelToken,
      );

      state = VerifyProcessing(
        status: 'extracting',
        currentStep: 'Extracting content and isolating key claims...',
        progress: 0.35,
        inputContent: cleanInput,
      );

      // Poll until completion or timeout
      final completer = Completer<void>();
      int pollCount = 0;
      const maxPolls = 120; // 120 * 600ms = 72 seconds timeout

      _pollingTimer = Timer.periodic(const Duration(milliseconds: 600), (timer) async {
        pollCount++;
        if (pollCount > maxPolls) {
          timer.cancel();
          if (!completer.isCompleted) {
            completer.completeError(
              const ApiException(message: 'Verification took longer than expected. Please try again.'),
            );
          }
          return;
        }

        try {
          final job = await repo.pollJobStatus(jobId, cancelToken: _cancelToken);

          if (job.isCompleted && job.result != null) {
            timer.cancel();
            final entity = repo.mapDtoToEntity(job.result!, customId: job.jobId);
            state = VerifySuccess(result: entity);
            if (!completer.isCompleted) completer.complete();
          } else if (job.isFailed) {
            timer.cancel();
            final errMsg = job.error ?? 'Verification failed';
            state = VerifyError(
              message: errMsg,
              inputContent: cleanInput,
            );
            if (!completer.isCompleted) completer.complete();
          } else {
            // Update progress
            final normalizedProgress = (job.progressPercentage / 100.0).clamp(0.15, 0.95);
            state = VerifyProcessing(
              status: job.status,
              currentStep: job.currentStep,
              progress: normalizedProgress,
              inputContent: cleanInput,
            );
          }
        } catch (e) {
          timer.cancel();
          if (!completer.isCompleted) completer.completeError(e);
        }
      });

      await completer.future;
    } on ApiException catch (e) {
      if (_cancelToken?.isCancelled ?? false) return;
      state = VerifyError(
        message: e.message,
        errorType: e.errorType,
        inputContent: cleanInput,
      );
    } catch (e) {
      if (_cancelToken?.isCancelled ?? false) return;
      state = VerifyError(
        message: 'Could not complete verification: ${e.toString()}',
        inputContent: cleanInput,
      );
    }
  }

  /// Directly set a past historical result (e.g. from history vault)
  void showHistoricalResult(dynamic result) {
    state = VerifySuccess(result: result);
  }
}
