# Based on original source code by Delx, found at: https://bitbucket.org/delx/webdl
# Original source code licence: https://bitbucket.org/delx/webdl/src/ef87849c131516a07815205f546a5f5cc6fae91e/LICENSE

from lxml import html
import requests
import lxml.etree
import lxml.html
import urllib
import io
import json
import urlparse
import subprocess
import os.path

NS = {
    "smil": "http://www.w3.org/2005/SMIL21/Language",
}

def get_player_params(doc):
    for script in doc.xpath("//script"):
        if not script.text:
            continue
        for line in script.text.split("\n"):
            s = "var playerParams = {"
            if s in line:
                p1 = line.find(s) + len(s) - 1
                p2 = line.find("};", p1) + 1
                if p1 >= 0 and p2 > 0:
                    return json.loads(line[p1:p2])
    raise Exception("Unable to find player params for video")

def ensure_scheme(url):

    parts = urlparse.urlparse(url)
    if parts.scheme:
        return url
    parts = list(parts)
    parts[0] = "http"
    return urlparse.urlunparse(parts)

def download_show(video_ID,filename):

    # don't download if file already exists
    if os.path.isfile(filename.replace(":","/") + ".ts"):
        print("\n" + filename.replace(":","/") + ".ts" + " already, moving to the next file.")
        return

    url = "http://www.sbs.com.au/ondemand/video/single/" + video_ID

    urllib.urlretrieve(url, "video.html")
    f = open("video.html", "r")
    doc = lxml.html.parse(f, lxml.html.HTMLParser(encoding="utf-8", recover=True))

    player_params = get_player_params(doc)

    release_url = player_params["releaseUrls"]["html"]
    release_url = ensure_scheme(release_url)

    urllib.urlretrieve(release_url, "release.xml")
    f = open("release.xml", "r")
    doc = lxml.etree.parse(f, lxml.etree.XMLParser(encoding="utf-8", recover=True))

    video = doc.xpath("//smil:video", namespaces=NS)[0]

    video_url = video.attrib["src"]
    video_url = "hlsvariant://" + video_url

    cmd = [
        "livestreamer",
        "-o", filename + ".ts",
        video_url,
        "best",
    ]

    p = subprocess.Popen(cmd)
    ret = p.wait()

