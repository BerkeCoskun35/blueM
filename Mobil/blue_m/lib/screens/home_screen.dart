// home_screen.dart
import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:blue_m/screens/ytmusic_player.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // 1) Sunucunuzun adresini buraya yazın.
  //    Android emulator için genelde 10.0.2.2:5000, fiziksel cihaz için yerel IP’niz.
  static const String baseUrl = 'http://10.0.2.2:5000';

  late Timer _statusTimer;
  List<Song> _songs = [];
  String? _currentVideoId;
  String? _currentSongTitle;
  String? _currentSongArtist;
  int _isPlaying = 0;
  double _volume = 0.5; // 0.0 - 1.0 arası

  @override
  void initState() {
    super.initState();
    fetchSongs();
    // Her saniye oynatma durumunu güncelle
    _statusTimer = Timer.periodic(
      const Duration(seconds: 10),
      (_) => fetchStatus(),
    );
  }

  @override
  void dispose() {
    _statusTimer.cancel();
    super.dispose();
  }

  // Şarkı listesini API'den çek
  Future<void> fetchSongs() async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/api/songs'));
      if (res.statusCode == 200) {
        final List<dynamic> data = json.decode(res.body);
        setState(() {
          _songs = data.map((e) => Song.fromJson(e)).toList();
        });
      } else {
        debugPrint('fetchSongs hata: ${res.statusCode}');
      }
    } catch (e) {
      debugPrint('fetchSongs exception: $e');
    }
  }

  // Seçilen şarkıyı çalmaya başlat
  Future<void> playSong(String? videoId) async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/api/songs/play/$videoId'));
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        setState(() {
          _currentVideoId = videoId;
          _currentSongTitle = data['title'];
          _currentSongArtist = data['artist'];
          _isPlaying = 1;
        });
      } else {
        debugPrint('playSong hata: ${res.statusCode}');
      }
    } catch (e) {
      debugPrint('playSong exception: $e');
    }
  }

  // Pause / Resume toggle
  Future<void> _togglePlayPause() async {
    if (_currentVideoId == null) return;
    try {
      if (_isPlaying == 1) {
        final res = await http.get(Uri.parse('$baseUrl/api/songs/pause'));
        if (res.statusCode == 200) setState(() => _isPlaying = 0);
      } else {
        final res = await http.get(Uri.parse('$baseUrl/api/songs/resume'));
        if (res.statusCode == 200) setState(() => _isPlaying = 1);
      }
    } catch (e) {
      debugPrint('togglePlayPause exception: $e');
    }
  }

  // Çalmayı tamamen durdur
  Future<void> stopSong() async {
    if (_currentVideoId == null) return;
    try {
      final res = await http.get(Uri.parse('$baseUrl/api/songs/stop'));
      if (res.statusCode == 200) {
        setState(() {
          _isPlaying = 0;
          _currentVideoId = null;
          _currentSongTitle = null;
          _currentSongArtist = null;
        });
      }
    } catch (e) {
      debugPrint('stopSong exception: $e');
    }
  }

  // Ses kaydırıcısı değiştiğinde
  Future<void> setVolume(double value) async {
    setState(() => _volume = value);
    final int vol = (value * 100).round();
    try {
      await http.get(Uri.parse('$baseUrl/api/songs/volume/$vol'));
    } catch (e) {
      debugPrint('setVolume exception: $e');
    }
  }

  // Sunucudan anlık durum bilgisi
  Future<void> fetchStatus() async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/api/songs/status'));
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        setState(() {
          _isPlaying = data['is_playing'] as int;
          _volume = (data['volume'] as int) / 100.0;
        });
      }
    } catch (e) {
      debugPrint('fetchStatus exception: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF171717),
      appBar: AppBar(
        backgroundColor: const Color(0xFF222222),
        title: Image.asset('assets/images/logo.png', height: 36),
        centerTitle: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.person_outline, color: Colors.white),
            onPressed: () => Navigator.pushNamed(context, '/login'),
          ),
        ],
      ),
      drawer: Drawer(
        backgroundColor: const Color(0xFF222222),
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            const DrawerHeader(
              decoration: BoxDecoration(color: Color(0xFF333333)),
              child: Text('Menü',
                  style: TextStyle(color: Colors.white, fontSize: 20)),
            ),
            ListTile(
              leading: const Icon(Icons.home, color: Colors.white),
              title: const Text('Ana Sayfa',
                  style: TextStyle(color: Colors.white)),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              leading: const Icon(Icons.library_books, color: Colors.white),
              title:
                  const Text('Kitaplık', style: TextStyle(color: Colors.white)),
              onTap: () {}, // Dilerseniz ekleyin
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          // Şarkı listesi
          Expanded(
            child: _songs.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: GridView.builder(
                      physics: const BouncingScrollPhysics(),
                      gridDelegate:
                          const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        crossAxisSpacing: 10,
                        mainAxisSpacing: 10,
                        childAspectRatio: 1,
                      ),
                      itemCount: _songs.length,
                      itemBuilder: (context, index) {
                        final song = _songs[index];
                        return GestureDetector(
                          onTap: () {
                            if (_currentVideoId == song.videoId) {
                              stopSong();
                            } else {
                              playSong(song.videoId);
                            }
                          },
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(10),
                            child: Stack(
                              children: [
                                Positioned.fill(
                                  child: song.thumbnailUrl != null &&
                                          song.thumbnailUrl!.isNotEmpty
                                      ? Image.network(song.thumbnailUrl!,
                                          fit: BoxFit.cover)
                                      : Container(color: Colors.grey),
                                ),
                                Positioned(
                                  bottom: 0,
                                  left: 0,
                                  right: 0,
                                  child: Container(
                                    color: Colors.black54,
                                    padding: const EdgeInsets.all(8),
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text("${song.title} (${song.duration})",
                                            style: const TextStyle(
                                                color: Colors.white,
                                                fontWeight: FontWeight.bold)),
                                        Text("${song.artist})",
                                            style: const TextStyle(
                                                color: Colors.white70,
                                                fontSize: 12)),
                                      ],
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  ),
          ),

          // Şu an çalıyor bilgisi
          if (_currentSongTitle != null)
            Container(
              width: double.infinity,
              color: const Color(0xFF222222),
              padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 16),
              child: Text(
                'Şu an çalıyor: $_currentSongTitle - $_currentSongArtist',
                style: const TextStyle(color: Colors.white),
              ),
            ),

          // Kontroller (play/pause, stop, volume)
          Container(
            color: const Color(0xFF222222),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                IconButton(
                  icon: Icon(
                    _isPlaying == 1
                        ? Icons.pause_circle_filled
                        : Icons.play_circle_fill,
                    color: Colors.white,
                    size: 36,
                  ),
                  onPressed: _togglePlayPause,
                ),
                IconButton(
                  icon: const Icon(Icons.stop, color: Colors.white, size: 28),
                  onPressed: stopSong,
                ),
                Expanded(
                  child: Slider(
                    value: _volume,
                    onChanged: setVolume,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// JSON’dan Song objesine dönüştürmek için model
class Song {
  final String? videoId;
  final String? title;
  final String? artist;
  final String? thumbnailUrl;
  final String? duration;

  Song({
    this.videoId,
    this.title,
    this.artist,
    this.thumbnailUrl,
    this.duration,
  });

  factory Song.fromJson(Map<String, dynamic> json) => Song(
        videoId: json['video_id'] as String,
        title: json['title'] as String,
        artist: json['artist'] as String,
        thumbnailUrl: json['thumbnail_url'] as String?,
        duration: json['duration'] as String?,
      );
}
