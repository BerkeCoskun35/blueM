// home_screen.dart
import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:youtube_explode_dart/youtube_explode_dart.dart';
import 'package:just_audio/just_audio.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final yt = YoutubeExplode();
  final player = AudioPlayer();
  List<Song> _songs = [];
  String? _currentVideoId;
  String? _currentSongTitle;
  String? _currentSongArtist;
  bool _isPlaying = false;
  Duration _currentPosition = Duration.zero;
  Duration _totalDuration = Duration.zero;

  @override
  void initState() {
    super.initState();
    _initializePlayer();
    fetchSongs();
  }

  void _initializePlayer() {
    player.playerStateStream.listen((state) {
      setState(() {
        _isPlaying = state.playing;
      });
    });

    // Pozisyon değişikliklerini dinle
    player.positionStream.listen((position) {
      setState(() {
        _currentPosition = position;
      });
    });

    // Toplam süre değişikliklerini dinle
    player.durationStream.listen((duration) {
      if (duration != null) {
        setState(() {
          _totalDuration = duration;
        });
      }
    });
  }

  @override
  void dispose() {
    player.dispose();
    yt.close();
    super.dispose();
  }

  Future<void> fetchSongs() async {
    try {
      final playlist = await yt.playlists.get('https://www.youtube.com/playlist?list=PL1y8hJl4KWcQwFEaBFTgxwhNQwE5SinuO');
      final videos = await yt.playlists.getVideos(playlist.id).toList();
      
      setState(() {
        _songs = videos.map((video) => Song(
          videoId: video.id.value,
          title: video.title,
          artist: video.author,
          thumbnailUrl: video.thumbnails.highResUrl,
          duration: video.duration?.toString() ?? '0:00',
        )).toList();
      });
    } catch (e) {
      debugPrint('fetchSongs exception: $e');
    }
  }

  Future<void> playSong(String? videoId, {Duration? startPosition}) async {
    if (videoId == null) return;

    try {
      await player.stop(); // Önce oynatıcıyı sıfırla
      final manifest = await yt.videos.streamsClient.getManifest(videoId);
      final audioStream = manifest.audioOnly.withHighestBitrate();

      await player.setAudioSource(
        AudioSource.uri(Uri.parse(audioStream.url.toString())),
      );
      
      // Eğer başlangıç pozisyonu belirtilmişse, o noktadan başlat
      if (startPosition != null) {
        await player.seek(startPosition);
      } else {
        await player.seek(Duration.zero);
      }

      setState(() {
        _currentVideoId = videoId;
        _currentSongTitle = _songs.firstWhere((s) => s.videoId == videoId).title;
        _currentSongArtist = _songs.firstWhere((s) => s.videoId == videoId).artist;
      });

      await player.play();
    } catch (e) {
      debugPrint('playSong exception: $e');
    }
  }

  Future<void> _togglePlayPause() async {
    if (_isPlaying) {
      await player.pause();
    } else {
      await player.play();
    }
  }

  Future<void> stopSong() async {
    await player.stop();
    setState(() {
      _currentVideoId = null;
      _currentSongTitle = null;
      _currentSongArtist = null;
    });
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    final minutes = twoDigits(duration.inMinutes.remainder(60));
    final seconds = twoDigits(duration.inSeconds.remainder(60));
    return "$minutes:$seconds";
  }

  Future<void> _seekTo(Duration position) async {
    await player.seek(position);
  }

  void _showTimeInputDialog(BuildContext context, Song song) {
    final TextEditingController minuteController = TextEditingController();
    final TextEditingController secondController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF222222),
        title: const Text('Başlangıç Zamanı',
            style: TextStyle(color: Colors.white)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: minuteController,
                    keyboardType: TextInputType.number,
                    style: const TextStyle(color: Colors.white),
                    decoration: const InputDecoration(
                      labelText: 'Dakika',
                      labelStyle: TextStyle(color: Colors.white),
                      enabledBorder: UnderlineInputBorder(
                        borderSide: BorderSide(color: Colors.white30),
                      ),
                      focusedBorder: UnderlineInputBorder(
                        borderSide: BorderSide(color: Colors.white),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: TextField(
                    controller: secondController,
                    keyboardType: TextInputType.number,
                    style: const TextStyle(color: Colors.white),
                    decoration: const InputDecoration(
                      labelText: 'Saniye',
                      labelStyle: TextStyle(color: Colors.white),
                      enabledBorder: UnderlineInputBorder(
                        borderSide: BorderSide(color: Colors.white30),
                      ),
                      focusedBorder: UnderlineInputBorder(
                        borderSide: BorderSide(color: Colors.white),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('İptal', style: TextStyle(color: Colors.white70)),
          ),
          TextButton(
            onPressed: () {
              final minutes = int.tryParse(minuteController.text) ?? 0;
              final seconds = int.tryParse(secondController.text) ?? 0;
              final duration = Duration(minutes: minutes, seconds: seconds);
              
              Navigator.pop(context);
              playSong(song.videoId, startPosition: duration);
            },
            child: const Text('Oynat', style: TextStyle(color: Colors.blue)),
          ),
        ],
      ),
    );
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
                          onLongPress: () {
                            _showTimeInputDialog(context, song);
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
            child: Column(
              children: [
                // Süre göstergesi ve slider
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _formatDuration(_currentPosition),
                      style: const TextStyle(color: Colors.white70, fontSize: 12),
                    ),
                    Text(
                      _formatDuration(_totalDuration),
                      style: const TextStyle(color: Colors.white70, fontSize: 12),
                    ),
                  ],
                ),
                Slider(
                  value: _currentPosition.inSeconds.toDouble(),
                  min: 0,
                  max: _totalDuration.inSeconds.toDouble(),
                  onChanged: (value) {
                    _seekTo(Duration(seconds: value.toInt()));
                  },
                ),
                // Kontrol butonları
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    IconButton(
                      icon: Icon(
                        _isPlaying
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
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// JSON'dan Song objesine dönüştürmek için model
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
