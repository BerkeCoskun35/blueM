// home_screen.dart
import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late AudioPlayer _audioPlayer;
  double _volume = 0.5;
  bool _isPlaying = false;

//  @override
//void initState() {
//  super.initState();
//  // PlayerMode.lowLatency moduyla başlatıyoruz:
//  _audioPlayer = AudioPlayer();
//  _audioPlayer.setPlayerMode(PlayerMode.lowLatency);
//  // Bir kez asset’i yükleyip hazır hale getir:
//  _audioPlayer.setSource(AssetSource('audio.mp3'));
//  // Playback sırasında kaynakları stop() sonrası bırakmasını istiyorsak:
//  _audioPlayer.setReleaseMode(ReleaseMode.stop);  // default RELEASE zaten release eder :contentReference[oaicite:1]{index=1}
//  // İlk ses seviyesini uygula:
//  _audioPlayer.setVolume(_volume);
//}

@override
  void initState() {
    super.initState();
    _audioPlayer = AudioPlayer()
      // Uzun dosyalar için mediaPlayer modu tercih edin:
      ..setPlayerMode(PlayerMode.mediaPlayer)
      // Çalmayı durdurunca kaynak serbest kalsın:
      ..setReleaseMode(ReleaseMode.stop);
  }


//  @override
//void dispose() {
//  // Eğer pause’dan sonra bile RAM’de tutulan bir buffer kaldıysa:
//  _audioPlayer.release();
//  _audioPlayer.dispose();
//  super.dispose();
//}


@override
  void dispose() {
    _audioPlayer.release();
    _audioPlayer.dispose();
    super.dispose();
  }


//  Future<void> _togglePlayPause() async {
//    if (_isPlaying) {
//      // Duraklat
//      await _audioPlayer.pause();
//    } else {
//      // Çal (ilk seferde yüklemek için play, sonraki seferler resume da olur)
//      await _audioPlayer.resume();
//    }
//    setState(() => _isPlaying = !_isPlaying);
//  }//

//  Future<void> _setVolume(double value) async {
//    setState(() {
//      _volume = value;
//    });
//    // Gerçek ses seviyesini de uygula
//    await _audioPlayer.setVolume(_volume);
//  }


Future<void> _togglePlayPause() async {
    if (_isPlaying) {
      // Stop(), tamponu serbest bırakır:
      await _audioPlayer.stop();
    } else {
      // play() ile asset’i akıtma şeklinde çal:
      await _audioPlayer.play(
        AssetSource('audio.mp3'),
        volume: _volume,
      );
    }
    setState(() => _isPlaying = !_isPlaying);
  }

  Future<void> _setVolume(double value) async {
    setState(() => _volume = value);
    await _audioPlayer.setVolume(_volume);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF171717),
      appBar: AppBar(
        backgroundColor: const Color(0xFF222222),
        title: Image.asset(
          'assets/images/logo.png',
          height: 36,
        ),
        centerTitle: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.person_outline, color: Colors.white),
            onPressed: () {
              Navigator.pushNamed(context, '/login');
            },
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
              child: Text('Menü', style: TextStyle(color: Colors.white, fontSize: 20)),
            ),
            ListTile(
              leading: const Icon(Icons.home, color: Colors.white),
              title: const Text('Ana Sayfa', style: TextStyle(color: Colors.white)),
              onTap: () {
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.library_books, color: Colors.white),
              title: const Text('Kitaplık', style: TextStyle(color: Colors.white)),
              onTap: () {},
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(12.0),
              child: GridView.builder(
                physics: const BouncingScrollPhysics(),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 10,
                  childAspectRatio: 1,
                ),
                itemCount: 50,
                itemBuilder: (context, index) {
                  return ClipRRect(
                    borderRadius: BorderRadius.circular(10),
                    child: Stack(
                      children: [
                        Positioned.fill(
                          child: Image.asset(
                            'assets/images/album${(index % 10) + 1}.png',
                            fit: BoxFit.cover,
                            errorBuilder: (context, error, stackTrace) {
                              final fallbackColor = Colors.primaries[index % Colors.primaries.length].shade800;
                              return Container(color: fallbackColor);
                            },
                          ),
                        ),
                        Align(
                          alignment: Alignment.bottomLeft,
                          child: Container(
                            padding: const EdgeInsets.all(6),
                            decoration: BoxDecoration(
                              color: Colors.black26,
                              borderRadius: const BorderRadius.only(
                                bottomLeft: Radius.circular(10),
                                bottomRight: Radius.circular(10),
                              ),
                            ),
                            width: double.infinity,
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Şarkı ${index + 1}',
                                  style: const TextStyle(color: Colors.white, fontSize: 16),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  'Sanatçı ${index + 1}',
                                  style: const TextStyle(color: Colors.white70, fontSize: 12),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
          ),
          Container(
            color: const Color(0xFF222222),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                IconButton(
                  icon: Icon(
                    _isPlaying ? Icons.pause_circle_filled : Icons.play_circle_fill,
                    color: Colors.white,
                    size: 36,
                  ),
                  onPressed: _togglePlayPause,
                ),
                Expanded(
                  child: Slider(
                    activeColor: Colors.white,
                    inactiveColor: Colors.white30,
                    value: _volume,
                    min: 0,
                    max: 1,
                    onChanged: _setVolume,
                  ),
                ),
                Text(
                  '${(_volume * 100).toInt()}%',
                  style: const TextStyle(color: Colors.white),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
