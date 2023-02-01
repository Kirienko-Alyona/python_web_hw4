from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
import socket
import threading
import json
from datetime import datetime
import os


UDP_IP = '127.0.0.1'
UDP_PORT = 5000
MESSAGE = "Python Web development"
WEB_PORT = 3000

BASE_DIR = pathlib.Path()


class HttpHandler(BaseHTTPRequestHandler):
    
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        # print(data)
        socket_client(UDP_IP, UDP_PORT, data)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()
    
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())
            
    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())        


def socket_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)
    try:
        while True:
            data, address = sock.recvfrom(1024)         
            print(f'Received data: {data.decode()} from: {address}')
            sock.sendto(data, address)
            print(f'Send data: {data.decode()} to: {address}')
            data_parse = urllib.parse.unquote_plus(data.decode())
            #print(data_parse)
            data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
            upload = {}
                
            with open(BASE_DIR.joinpath('storage/data.json'), 'r', encoding='utf-8') as fd:
                text = fd.readline()
                if text:
                    upload = json.loads(text)
                
            with open(BASE_DIR.joinpath('storage/data.json'), 'w', encoding='utf-8') as fd:                
                upload.update({str(datetime.now()): data_dict})
                json.dump(upload, fd, ensure_ascii=False)

    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        sock.close()
        
def socket_client(ip, port, data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.sendto(data, server)
    print(f'Send data: {data.decode()} to server: {server}')
    response, address = sock.recvfrom(1024)
    print(f'Response data: {response.decode()} from address: {address}')    
    sock.close()        
                                
def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = (UDP_IP, WEB_PORT)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    run_web_app = threading.Thread(target=run_http_server)
    server = threading.Thread(target=socket_server, args=(UDP_IP, UDP_PORT))

    server.start()
    run_web_app.start()
    server.join()
    print('Done!')
