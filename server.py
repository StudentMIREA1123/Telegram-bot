import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from bot import run_bot

HTTP_PORT = 8080


class StatusPage(BaseHTTPRequestHandler):
    def do_GET(self):
        html = """<!doctype html><html><head><meta charset="utf-8">
        <title>Bot Server</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px">
            <h1> Сервер поднят</h1>
            <p>Бот работает в Telegram (long-polling).</p>
            <p style="color:#888">Порт: 8080</p>
        </body></html>"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, *args):
        pass  # не спамим в консоль


def start_status_page():
    server = HTTPServer(('127.0.0.1', HTTP_PORT), StatusPage)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f'[http] Страница статуса: http://localhost:{HTTP_PORT}')


if __name__ == '__main__':
    start_status_page()   # 1. поднимаем страницу в фоне
    run_bot()             # 2. запускаем бота (блокирует поток)