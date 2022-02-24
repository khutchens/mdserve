#! /usr/bin/env python3

import argparse
import http.server
import jinja2
import json
import mistune
import os
import simple_websocket_server
import socketserver
import threading

class HTTPReqHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        base, ext = os.path.splitext(self.path)
        if ext != '.md':
            return super().do_GET()

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        expath = os.path.dirname(os.path.realpath(__file__))
        with open(expath + '/page.html.jinja') as file:
            template = jinja2.Environment(loader=jinja2.BaseLoader).from_string(file.read())
        with open(expath + f'/style-{args.style}.html') as file:
            style_text = file.read()
        self.wfile.write(template.render(style=style_text, file_name=self.path, ws_port=websocket_port).encode('utf-8'))

class TCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class WebSocket(simple_websocket_server.WebSocket):
    def handle(self):
        request = json.loads(self.data)

        if request['type'] == 'mtime':
            self.send_message(json.dumps({'type': 'mtime', 'time': os.stat(root_path + request['path']).st_mtime}))
        if request['type'] == 'markdown':
            with open(root_path + request['path']) as file:
                html = mistune.html(file.read())
            self.send_message(json.dumps({'type': 'markdown', 'html': html}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=9000)
    parser.add_argument('-s', '--style', choices=['none', 'github'], default='github')
    args = parser.parse_args()

    root_path = os.getcwd()
    print('path:', root_path)

    def serve(port, serve_call):
        while True:
            try:
                server = serve_call(port)
                return server, port
            except OSError:
                print('failed binding port:', port)
            port += 1

    websocket_server, websocket_port = serve(args.port, lambda port: simple_websocket_server.WebSocketServer('', port, WebSocket))
    print('websocket port:', websocket_port)

    http_server, http_port = serve(websocket_port + 1, lambda port: TCPServer(('', port), HTTPReqHandler))
    print('http port:     ', http_port)

    with http_server:
        http_server_thread = threading.Thread(target=http_server.serve_forever)
        http_server_thread.daemon = True
        http_server_thread.start()

        websocket_server.serve_forever()

        http_server.shutdown()


