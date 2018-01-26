import xbmcplugin
import xbmcgui
import xbmcaddon
import sys
import re
import urllib
import urllib2
import urlparse
import json

from datetime import datetime, date, time

# uris
plugin_url = sys.argv[0]
base_url = 'http://nos.nl'
secure_url = 'http://nos.nl/video/resolve/'
overview_url = 'http://nos.nl/uitzendingen'
image_base_url = 'http://s.nos.nl/img/broadcast-content/programs/'

# settings
quality = xbmcaddon.Addon().getSetting('quality')
limit = int(float(xbmcaddon.Addon().getSetting('limit')))
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', None)
loc = args.get('location', None)
xbmcplugin.setContent(addon_handle, 'episodes')

# regular expressions
re_folder = re.compile('<li class="broadcast-list__item[^"]{0,}">[^<]?<a href="([^"]+)" class="[^"]+"[^>]{0,}><div class="broadcast-link__wrapper[^"]{0,}"><span class="broadcast-link__play img-icon-play"></span><span class="broadcast-link__name[^"]{0,}">([^<]+)</span>')
re_item = re.compile('<li class="broadcast-player__playlist__item"><a href="([^"]+)" class="[^"]+"[^>]{0,}><span class="[^"]+"></span><span class="broadcast-link__name[^"]{0,}">([^<]+)</span><time class="[^"]+" datetime="([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]+):([0-9]+):[^"]+">')
re_source = re.compile('<source src="([^"]+)" type="video/mp4" data-label="[A-Za-z]+ - ' + quality + '"')
re_content_length = re.compile('Content-Length: ([0-9]+)')

def build_url(query):
    return plugin_url + '?' + urllib.urlencode(query)

def addLink(location, name, folder, mode, ic, tot, info):
    if ic is None:
        ic = image_base_url + name.lower().replace(' ', '-') + '.jpg'

    li = xbmcgui.ListItem(name, iconImage=ic)
    li.setProperty('IsPlayable', 'true')

    if info != None:
        li.setInfo('video', info)

    url = build_url({'mode': mode, 'location': location})
    xbmcplugin.addDirectoryItem(addon_handle, url=url, listitem=li, isFolder=folder)

def addDir(location, name, folder, mode, ic, tot, info):
    if ic is None:
        ic = image_base_url + name.lower().replace(' ', '-') + '.jpg'
    li = xbmcgui.ListItem(name, iconImage=ic)

    if mode == 'section':
        url = build_url({'mode': mode, 'location': location, 'icon': ic, 'name': name})
    elif mode == 'item':
        url = location

    if info != None:
        li.setInfo('video', info)

    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=folder, totalItems=tot)

def getHtml(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:40.0) Gecko/20100101 Firefox/40.0')

    return urllib2.urlopen(req).read().replace('\n', '')

# for sports related streams an additional ip check is required.
# deprecated: currently resolved through redirects
def secureItem(location):
        
    return location
    
# check item for content length and fallback to a backup stream if necessary
def validateItem(location):
    request = urllib2.Request(location)
    request.get_method = lambda : 'HEAD'
    
    response = urllib2.urlopen(request)
    headers = response.info().headers
    
    for header in headers:
        matches = re.findall(re_content_length, header)
        
        for match in matches:
            if int(match[0]) == 0:
                if location.find('_backup.mp4') == -1:
                    return location.replace('.mp4', '_backup.mp4')
                
                return location.replace('_backup.mp4', '.mp4')
                
    return location

def playItem(location):
    item_html = getHtml(base_url + location)
    videos = re.findall(re_source, item_html)
    
    for video in videos:
        video = secureItem(video)
        video = validateItem(video)
        
        listItem = xbmcgui.ListItem(path=video)
        listItem.setProperty('IsPlayable', 'true')

        xbmcplugin.setResolvedUrl(addon_handle, True, listItem)

if mode is None:
    html = getHtml(overview_url + '/')
    folders = re.findall(re_folder, html)

    for folder in folders:
        addDir(folder[0], folder[1], 1, 'section', None, len(folders), None)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'section':
    html = getHtml(base_url + loc[0])
    items = re.findall(re_item, html)

    for item in items[:limit]:
        dt = datetime(int(item[2]), int(item[3]), int(item[4]), int(item[5]), int(item[6]))
        addLink(item[0], dt.strftime("%A, %d %B %Y %I:%M%p"), 0, 'item', args['icon'][0], len(items[:limit]), {'aired': dt.strftime("%Y-%m-%d")})

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'item':
    playItem(loc[0])

    xbmcplugin.endOfDirectory(addon_handle)
