from flask import Flask, Response, request, abort, stream_with_context
import os
import re

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>HTML5 Audio Streaming Service with Range Support</title>
    </head>
    <body>
        <h1>HTML5 Audio Streaming Service with Range Support</h1>
        <audio controls>
            <source src="/stream" type="audio/mp3">
            Tarayıcınız audio elementini desteklemiyor.
        </audio>
    </body>
    </html>
    '''

@app.route('/stream')
def stream_audio():
    file_path = 'audio.mp3'
    file_size = os.stat(file_path).st_size
    range_header = request.headers.get('Range', None)
    
    if not range_header:
        # Range header gelmiyorsa, tüm dosyayı stream ediyoruz.
        def generate():
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    yield chunk
        return Response(generate(), mimetype="audio/mp3")
    
    # Range header'ın "bytes=start-end" formatında olduğunu varsayıyoruz.
    range_match = re.search(r'(\d+)-(\d*)', range_header)
    if range_match:
        start_str, end_str = range_match.groups()
        start = int(start_str)
        end = int(end_str) if end_str else file_size - 1
    else:
        return abort(400)
    
    length = end - start + 1

    def generate():
        with open(file_path, 'rb') as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk_size = 4096 if remaining >= 4096 else remaining
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    rv = Response(stream_with_context(generate()), status=206, mimetype="audio/mp3")
    rv.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    rv.headers.add('Content-Length', str(length))
    return rv

if __name__ == '__main__':
    app.run(debug=True)
