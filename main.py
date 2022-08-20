import re
import json
import network
import socket
import page
from machine import Pin
  
def do_connect(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

def create_access_point(ssid="ESP-AP", password=None):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid)
    if password:
        ap.config(password=password)
    ap.config(max_clients=10)
    ap.active(True)
    while ap.active() == False:
      pass

    print('Connection successful')
    print(ap.ifconfig())
    return ap


class Request:
  def __init__(self, data_raw: bytes):
    data = data_raw.decode('UTF-8')
    first_line = data.split('\r\n', 1)[0]
    self.__split_fistline(first_line)
    self.data = data.split('\r\n\r\n', 1)[1]
  def __split_fistline(self, first_line):
    if len(first_line) == 0:
      return
    print('firstline: %s' % first_line)
    (self.method, query_string, self.version) = first_line.split(' ')
    qs_slited = query_string.split('?')
    if len(qs_slited) > 1:
      (self.route, _params) = qs_slited
    else:
      self.route = qs_slited[0]
      _params = ""
    self.__split_querystring(_params)
  def __split_querystring(self, query_parameters_raw):
    self.query_params = dict()
    for elmt in query_parameters_raw.split('&'):
      e_split = elmt.split('=', 1)
      if len(e_split) > 1:
        (k, v) = e_split
        self.query_params[k] = v

class State:
  def __init__(self, gpio: int, name: str):
    self.gpio = gpio
    self.name = name
    self.pin = Pin(gpio, Pin.OUT)

  
states = [
  State(gpio=4, name='Neon'),
  State(gpio=5, name='NeonArgon'),
]

pins = [
  Pin(4, Pin.OUT),
  Pin(5, Pin.OUT),
]

do_connect("<ssid>", "<password>")
#ap = create_access_point("CalibLite")
#print("Wifi Access Point Name: " + ap.config('essid'))

def routes(request):
  """
  analyse the route and return the response.
  """
  response = None
  print(' Analyse of request: %s' % request.route)
  res = re.match(r"/light/(\d+)/(\w+)", request.route)
  if res:
    print('  match on POST /light/(\d+)/(\w+)')
    id = int(res.group(1))
    state = {'on': 1, 'off': 0}[res.group(2)]
    if id < len(pins):
      pins[id].value(state)
    return {"headers": ["HTTP/1.1 200 OK"], "body": None}
  res = re.match(r'/light/(\d+)', request.route)
  if res:
    print('  match on GET /light/(\d+)')
    id = int(res.group(1))
    if id < len(pins):
      state = pins[id].value()
      _doc = {'light': id, 'state': state}
      print(f"  response: {_doc}")
      return {"headers": ["HTTP/1.1 200 OK", "Content-Type: application/json"], "body": json.dumps(_doc)}
  if request.route == '/lights':
    print('  match on GET /light/(\d+)')
    _doc = [{'light': id, 'state': pin.value()} for id, pin in enumerate(pins)]
    print(f"  response: {_doc}")
    return {"headers": ["HTTP/1.1 200 OK", "Content-Type: application/json"], "body": json.dumps(_doc)}
  return False


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

while True:
  conn, addr = s.accept()
  print('Got a connection from %s' % str(addr))
  request_string = conn.recv(1024)
  request = Request(request_string)
  print('Request: %s %s' % (request.method, request.route))
  for (k,v) in request.query_params.items():
    print('%s => %s' % (k, v))
  if request.route == '/':
    conn.send(page.index())
  elif request.route == '/hello':
    conn.send(page.hello())
  else:
    response = routes(request)
    print("response {}".format(response))
    if response:
      for header in response["headers"]:
        conn.send("%s\r\n" % header)
      if response["body"]:
        size = len(response["body"])
        conn.send("Content-Length: %d\r\n" % size)
        conn.send("\r\n")
        conn.sendall(response["body"])
    else:
      conn.send("HTTP/1.1 404 NOT FOUND\r\n")
      conn.send(page.page_404())
  conn.close()
