from   django.conf                 import settings
from   django.core.management.base import BaseCommand, CommandError
import os
import re
import sys
import threading
import urllib.request

cmd_rx = re.compile(R"^#!\s*fetchstatic\s*\(\s*(.*?)\s*\)\s*$", re.I)
url_rx = re.compile(R"\w{2,}://[\w.-]+\.\w{2,}(?::\d+)?/\S+")

# Some websites require a `User-Agent` header to be sent. Any one will fit. :)
USER_AGENT = "Python/{0.major}.{0.minor}.{0.micro}".format(sys.version_info)


class Command(BaseCommand):
    help = "Download static files listed in .gitignore"

    def handle(self, **options):
        threads = [ ]
        level = 0
        url = None
        file_path = os.path.join(settings.BASE_DIR, ".gitignore")
        with open(file_path) as f:
            for i, line in enumerate(f, 1):
                m = cmd_rx.match(line)
                if m is not None:
                    action = m.group(1).lower()
                    if action == "begin":
                        level += 1
                    elif action == "end":
                        level -= 1
                    else:
                        raise CommandError("%s:%d: Unknown action `%s`" % (file_path, i, action))
                elif level > 0:
                    if line.startswith('#'):
                        line = line.lstrip('#').strip()
                        if line:
                            m = url_rx.search(line)
                            url = m.group() if m is not None else None
                    elif url is not None:
                        line = line.strip()
                        if line:
                            line = line.lstrip('/')
                            path = os.path.join(settings.BASE_DIR, line)
                            threads.append(threading.Thread(target=self.download, args=(url, path)))
                            url = None

        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def download(self, url, path):
        self.stdout.write("Fetching %s" % url)
        os.makedirs(os.path.split(path)[0], exist_ok=True)
        request = urllib.request.Request(url)
        request.add_header("User-Agent", USER_AGENT)
        with urllib.request.urlopen(request) as u:
            with open(path, "wb") as f:
                while True:
                    data = u.read(4096)
                    if not data:
                        break
                    f.write(data)
        self.stdout.write("Done: %s" % path)
