class UrlSanitizer {
  static final RegExp _urlRegex = RegExp(
    r'(https?:\/\/[^\s<>"{}|\\^`\[\]]+)',
    caseSensitive: false,
  );

  /// Strips marketing/tracking query params from URL
  static String sanitizeUrl(String rawUrl) {
    try {
      final uri = Uri.parse(rawUrl.trim());
      if (!uri.hasScheme || !uri.hasAuthority) return rawUrl.trim();

      final trackingParams = {
        'utm_source',
        'utm_medium',
        'utm_campaign',
        'utm_term',
        'utm_content',
        'fbclid',
        'igshid',
        'gclid',
        's',
        't',
        'si',
      };

      final cleanQueryParameters = Map<String, dynamic>.from(uri.queryParameters)
        ..removeWhere((key, _) => trackingParams.contains(key.toLowerCase()));

      if (cleanQueryParameters.isEmpty) {
        final cleared = uri.replace(query: '').toString();
        return cleared.endsWith('?') ? cleared.substring(0, cleared.length - 1) : cleared;
      }

      return uri.replace(queryParameters: cleanQueryParameters).toString();
    } catch (_) {
      return rawUrl.trim();
    }
  }

  /// Extracts the first valid HTTP/HTTPS URL from any composite string
  static String? extractFirstUrl(String text) {
    final match = _urlRegex.firstMatch(text);
    if (match != null) {
      final raw = match.group(0);
      if (raw != null) {
        return sanitizeUrl(raw);
      }
    }
    return null;
  }

  /// Classifies platform from URL for immediate UI representation
  static String identifyPlatform(String? url) {
    if (url == null || url.isEmpty || url.startsWith('text://')) {
      return 'Plain Text';
    }
    final lower = url.toLowerCase();
    if (lower.contains('youtube.com/shorts')) return 'YouTube Shorts';
    if (lower.contains('youtube.com') || lower.contains('youtu.be')) return 'YouTube Video';
    if (lower.contains('twitter.com') || lower.contains('x.com')) return 'X / Twitter';
    if (lower.contains('instagram.com/reel')) return 'Instagram Reel';
    if (lower.contains('instagram.com/p/')) return 'Instagram Post';
    if (lower.contains('instagram.com')) return 'Instagram';
    if (lower.contains('facebook.com') || lower.contains('fb.watch')) return 'Facebook';
    if (lower.contains('t.me') || lower.contains('telegram')) return 'Telegram';
    if (lower.contains('reddit.com')) return 'Reddit';
    return 'Web Article';
  }
}
