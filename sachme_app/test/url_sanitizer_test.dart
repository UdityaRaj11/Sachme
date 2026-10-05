import 'package:flutter_test/flutter_test.dart';
import 'package:sachme/core/utils/url_sanitizer.dart';

void main() {
  group('UrlSanitizer Tests', () {
    test('Extracts HTTP and HTTPS URLs from messy message forwards', () {
      const message =
          'Hey guys check this out! https://x.com/user/status/1234567890?s=20&t=abcdef this is urgent';
      final extracted = UrlSanitizer.extractFirstUrl(message);

      expect(extracted, isNotNull);
      expect(extracted, startsWith('https://x.com/user/status/1234567890'));
      // Verifies tracking tokens are cleanly stripped
      expect(extracted, isNot(contains('s=20')));
      expect(extracted, isNot(contains('t=abcdef')));
    });

    test('Strips marketing query parameters (utm, igshid, fbclid)', () {
      const dirtyUrl =
          'https://www.instagram.com/reel/C7xyz123/?utm_source=ig_web_copy_link&igshid=MzRlODBiNWFlZA==';
      final sanitized = UrlSanitizer.sanitizeUrl(dirtyUrl);

      expect(sanitized, equals('https://www.instagram.com/reel/C7xyz123/'));
    });

    test('Returns null when message contains no URL', () {
      const textOnly = 'Government is giving Rs 25,000 to every student.';
      final extracted = UrlSanitizer.extractFirstUrl(textOnly);

      expect(extracted, isNull);
    });

    test('Identifies social platforms accurately', () {
      expect(
        UrlSanitizer.identifyPlatform('https://www.youtube.com/shorts/abcd123'),
        equals('YouTube Shorts'),
      );
      expect(
        UrlSanitizer.identifyPlatform('https://youtu.be/dQw4w9WgXcQ'),
        equals('YouTube Video'),
      );
      expect(
        UrlSanitizer.identifyPlatform('https://x.com/pibfactcheck/status/1234'),
        equals('X / Twitter'),
      );
      expect(
        UrlSanitizer.identifyPlatform('https://www.instagram.com/reel/xyz/'),
        equals('Instagram Reel'),
      );
      expect(
        UrlSanitizer.identifyPlatform('https://pib.gov.in/FactCheck/FakeScheme.html'),
        equals('Web Article'),
      );
      expect(
        UrlSanitizer.identifyPlatform('text://direct-input'),
        equals('Plain Text'),
      );
    });
  });
}
