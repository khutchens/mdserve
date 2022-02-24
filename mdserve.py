#! /usr/bin/env python3

import argparse
import time
import http.server
import jinja2
import mistune
import os
import socketserver

class ReqHandler(http.server.SimpleHTTPRequestHandler):
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
        self.wfile.write(template.render(style=style_text, file_name=self.path).encode('utf-8'))

    def do_POST(self):
        data_len = int(self.headers.get_all('content-length')[0])
        data = self.rfile.read(data_len)
        path = self.directory + self.path

        if data == b'mtime':
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()

            self.wfile.write(str(os.stat(path).st_mtime).encode('utf-8'))

        elif data == b'markdown':
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()

            with open(path) as file:
                html = mistune.html(file.read())
            self.wfile.write(bytes(html, 'utf-8'))

        else:
            self.send_response(400)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=9000)
    parser.add_argument('-s', '--style', choices=['none', 'github'], default='github')
    args = parser.parse_args()

    handler = ReqHandler
    with socketserver.TCPServer(("", args.port), handler) as httpd:
        print('Serving on: localhost:{}'.format(args.port))
        httpd.serve_forever()
