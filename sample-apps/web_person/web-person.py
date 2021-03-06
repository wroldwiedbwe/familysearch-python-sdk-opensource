# -*- coding: utf-8 -*-

from __future__ import print_function
import webbrowser
import os
import sys
import pprint

try:
    # Python 3
    import configparser
    from http import server
    from urllib.parse import parse_qs
except ImportError:
    # Python 2
    import ConfigParser as configparser
    import BaseHTTPServer as server
    from urlparse import parse_qs

from familysearch import FamilySearch

config_path = os.path.dirname(os.path.abspath(sys.argv[0])) + "/config.ini"

config = configparser.ConfigParser()
config.read(config_path)
dev_key = config.get("fskey", "devkey")
base = config.get("fskey", "base")
port = config.get("server", "port")
redirect = config.get("server", "redirect_uri")

url = "http://localhost" + (":" + port) if port is not "80" else ""
ruri = ""
for x in redirect[::-1]:
    ruri = x + ruri
    if x is "/":
        break

fs = FamilySearch("FSPySDK/SampleApps", dev_key, base=base)

try:
    fslogin = fs.root_collection["response"]['collections'][0]['links']\
            ['http://oauth.net/core/2.0/endpoint/authorize']['href']
except KeyError as e:
    print("KeyError:", str(e))
    raise


def qshow():
    def hr(): print("="*80)
    hr()
    print("fs.root_collection: ...")
    pp = pprint.PrettyPrinter(width=120, indent=2)
    pp.pprint(fs.root_collection)
    hr()
    print("""fs.root_collection["response"]: ...""")
    pp.pprint(fs.root_collection["response"])
    hr()
    print("""fs.root_collection["response"]["collections"]: ...""")
    pp.pprint(fs.root_collection["response"]["collections"])
    hr()
    print("""fs.root_collection["response"]["collections"][0]: ...""")
    pp.pprint(fs.root_collection["response"]["collections"][0])
    hr()
    print("""fs.root_collection["response"]["collections"][0]["links"]: ...""")
    pp.pprint(fs.root_collection["response"]["collections"][0]["links"])
    hr()
    print("""fs.root_collection["response"]["collections"][0]["links"]['http://oauth.net/core/2.0/endpoint/authorize']: ...""")
    pp.pprint(fs.root_collection["response"]["collections"][0]["links"]['http://oauth.net/core/2.0/endpoint/authorize'])
    hr()
    print("""fs.root_collection["response"]["collections"][0]["links"]['http://oauth.net/core/2.0/endpoint/authorize']['href']: ...""")
    pp.pprint(fs.root_collection["response"]["collections"][0]["links"]['http://oauth.net/core/2.0/endpoint/authorize']['href'])
    hr()
# qshow()

print("fslogin:", fslogin)
fslogin = fs._add_query_params(fslogin, {
                                         'response_type': 'code',
                                         'client_id': fs.dev_key,
                                         'redirect_uri': redirect
                                        })
print("fslogin:", fslogin)


class getter(server.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(code=200)
        self.send_header("Content-type", "text/html;charset=utf-8")
        self.end_headers()
        path = self.path
        print("path:", path)

        top = "<!DOCTYPE html><html><head><title>FSPySDK Sample App</title>"
        top += '<meta charset="UTF-8">'
        middle = "</head><body>"
        bottom = "</body></html>"
        if path.startswith(ruri):
            bottom = self.get_code(path) + bottom
        else:
            if fs.logged_in:
                middle += self.logged_in()
                if path.startswith("/?pid="):
                    pid = parse_qs(path)["/?pid"][0]
                    person = fs.get(fs.person(pid))  # = fs.get_person(pid)
                    middle += self.has_pid(person)
            else:
                middle = self.not_logged_in() + middle
                middle = self.not_logged_in()

        body = top + middle + bottom

        self.wfile.write(body.encode("utf-8"))

    def not_logged_in(self):
        string = '<script>function openWin(){window.open("' + fslogin
        string += '","fsWindow","width=560,height=632");}</script>'
        string += "</head><body>"
        string += "<button onclick=openWin()>Sign in to FamilySearch</button>"
        return string

    def logged_in(self):
        def show_fs():
            print("="*80)
            pp = pprint.PrettyPrinter(width=120, indent=2)
            for k in sorted(list(fs.__dict__.keys())):
                if k[0] == '_': continue
                v = fs.__dict__[k]
                vt = type(v)
                if isinstance(v, (bool, type(''), type(b''), type(u''), tuple, list, set, frozenset)):
                    print(k, vt, v)
                elif isinstance(v, (dict,)):
                    print(k, vt, "...")
                    pp.pprint(v)
                else:
                    print(k, vt)
                print("")
            print("="*80)

        def p():
            show_fs()
            print("fs.user:", type(fs.user), fs.user)
            print("fs.current_user():", fs.current_user())
            print("fs.current_user_person():", fs.current_user_person())
            print("fs.agent('x'):", fs.agent('x'))
            print("fs.current_user_history():", fs.current_user_history())
        p()
        string = 'Search given FamilySearch PID (default is your own)<form>'
        string += '<input type="text" name="pid" value=' + '"KW41-44D"' # fs.user['personId']
        string += '><br /><input type="submit" value="Submit"></form>'
        return string

    def has_pid(self, person):
        name = person['response']['persons'][0]['names'][0]['nameForms'][0]\
            ['fullText']
        string = 'This is ' + name + '. <br />'
        if person['response']['persons'][0]['display']['gender'] == "Male":
            string += 'He'
        else:
            string += 'She'
        string += " is "
        if person['persons'][0]['living']:
            string += 'living'
        else:
            string += 'deceased'
        string += ".<br />"
        if person['response']['persons'][0]['display']['gender'] == "Male":
            string += 'His'
        else:
            string += "Her"
        string += ' lifespan is "'
        string += person['persons'][0]['display']['lifespan']
        string += '".<br />'
        return string

    def get_code(self, path):
        qs = parse_qs(path)
        qs = list(qs.values())[0][0]
        fs.oauth_code_login(qs)
        return '<script>window.opener.location.reload();window.close()</script>'

webbrowser.open(url)
server.HTTPServer(('', int(port)), getter).serve_forever()
