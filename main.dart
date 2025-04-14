import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

Future<void> makeSecureRequest() async {
  // شهادة الخادم (يجب تحديثها بالشهادة الفعلية)
  final String trustedCertificate = '''
  -----BEGIN CERTIFICATE-----
  MIIFgTCCBGmgAwIBAgIQOXJEOvkit1HX02wQ3TE1lTANBgkqhkiG9w0BAQwFADB7
  ...
  -----END CERTIFICATE-----
  ''';

  final SecurityContext context = SecurityContext()
    ..setTrustedCertificatesBytes(trustedCertificate.codeUnits);

  final HttpClient client = HttpClient(context: context);
  
  try {
    final request = await client.getUrl(Uri.parse('https://example.com/api/data'));
    final response = await request.close();
    final responseBody = await response.transform(utf8.decoder).join();
    
    // معالجة الاستجابة
    print(responseBody);
  } catch (e) {
    print('Error: $e');
  } finally {
    client.close();
  }
}
