import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';
import '../../../core/utils/url_sanitizer.dart';

class ShareIntentService {
  StreamSubscription? _intentSub;
  final void Function(String content) onContentReceived;

  ShareIntentService({required this.onContentReceived});

  void initialize() {
    // Listen to shared media/text while the app is in memory (warm start)
    _intentSub = ReceiveSharingIntent.instance.getMediaStream().listen(
      (List<SharedMediaFile> value) {
        if (value.isNotEmpty) {
          final first = value.first;
          final text = first.path;
          _handleIncomingRaw(text);
        }
      },
      onError: (err) {
        debugPrint('[ShareIntent] Error listening to stream: $err');
      },
    );

    // Get the shared media/text when app was closed (cold start)
    ReceiveSharingIntent.instance.getInitialMedia().then((List<SharedMediaFile> value) {
      if (value.isNotEmpty) {
        final first = value.first;
        final text = first.path;
        _handleIncomingRaw(text);
        ReceiveSharingIntent.instance.reset();
      }
    });
  }

  void _handleIncomingRaw(String raw) {
    final clean = raw.trim();
    if (clean.isEmpty) return;

    // Check if it contains a URL
    final extractedUrl = UrlSanitizer.extractFirstUrl(clean);
    final finalContent = extractedUrl ?? clean;
    onContentReceived(finalContent);
  }

  void dispose() {
    _intentSub?.cancel();
  }
}
