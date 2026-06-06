import webview
from sys import stdout
from os.path import basename, expanduser, isfile, exists, getsize, dirname, abspath, join as pjoin
from os import environ, getpid, _exit, makedirs, remove
from subprocess import Popen, DEVNULL, check_output
from base64 import b64encode
from mimetypes import guess_type
from urllib.parse import quote, unquote
from urllib.request import Request, urlopen
from shutil import copyfileobj, which
from glob import glob
from re import sub, compile as reCompile, escape as reEscape
from threading import Thread

REQUIRED_ENV = {
    "QT_LOGGING_RULES": "qt.qpa.wayland=false;qt.qpa.gl=false;*.debug=false",
    "QT_QPA_PLATFORM": "wayland;xcb",
    "LIBGL_ALWAYS_SOFTWARE": "1",
    "MESA_LOADER_DRIVER_OVERRIDE": "zink"
}

environ.update(REQUIRED_ENV)

langEnv = environ.get('LANG', 'en').lower()
currentLang = 'pt' if langEnv.startswith('pt') else 'en'
translations = {
    'pt': {
        'lbl_yes': "Sim",
        'lbl_no': "Não",
        'header_lbl': "Deseja permitir que esse aplicativo faça alterações em seu dispositivo?",
        'uac_title': 'Controle de Conta do Usuário',
        'vendor_lbl': 'Publicador verificado',
        'more_details': 'Mostrar mais detalhes',
        'file_path': 'Caminho do arquivo',
        'file_origin': 'Origem do arquivo',
        'password_req': 'Para continuar, insira sua senha de administrador.',
        'unknown_vendor': 'Fornecedor Desconhecido',
        'not_found': 'Não encontrado',
        'origin_unknown': 'Origem desconhecida',
        'origin_removable': 'Unidade removível (CD/DVD/USB)',
        'origin_network': 'Local de rede',
        'origin_download': 'Baixado da internet',
        'origin_local': 'Disco rígido neste computador',
        'origin_system': 'Local do sistema',
        'pw_input_placeholder': "Senha",
        'unknown_command': 'Comando desconhecido',
    },
    'en': {
        'lbl_yes': "Yes",
        'lbl_no': "No",
        'header_lbl': "Do you want to allow this app to make changes to your device?",
        'uac_title': "User Account Control",
        'vendor_lbl': 'Publisher',
        'more_details': 'Show more details',
        'file_path': 'File path',
        'file_origin': 'File origin',
        'password_req': 'To continue, type your administrator password.',
        'unknown_vendor': 'Unknown Publisher',
        'not_found': 'Not found',
        'origin_unknown': 'Unknown origin',
        'origin_removable': 'Removable drive (CD/DVD/USB)',
        'origin_network': 'Network location',
        'origin_download': 'Downloaded from internet',
        'origin_local': 'Local hard drive of this computer',
        'origin_system': 'System location',
        'pw_input_placeholder': "Password",
        'unknown_command': 'Unknown command',
    }
}

baseDir   = dirname(abspath(__file__))
htmlPath  = pjoin(baseDir, 'index.html')
assetsDir = pjoin(baseDir, 'assets')
audioPath = pjoin(assetsDir, 'uac.mp3')
urlPrimary  = 'https://www.myinstants.com/media/sounds/windows-10-user-account-control_eraWPlA.mp3'
urlFallback = 'https://deadsounds.com/get/11856/mp3'


class UacBackend:
    def __init__(self):
        self.capturedPassword = None

    def submitPassword(self, password):
        self.capturedPassword = password
        webviewWindow.destroy()


def playUacAudio():
    cache_dir = expanduser("~/.cache/openwin-uac")
    if not exists(cache_dir):
        makedirs(cache_dir)
    
    local_audio = pjoin(cache_dir, 'uac.mp3')
    
    isValid = False
    if exists(local_audio) and getsize(local_audio) > 1000:
        isValid = True

    if not isValid:
        reqHeaders = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        for url in (urlPrimary, urlFallback):
            try:
                with urlopen(Request(url, headers=reqHeaders), timeout=10) as resp, open(local_audio, 'wb') as out:
                    copyfileobj(resp, out)
                isValid = True
                break
            except Exception:
                continue

    if isValid:
        for cmd in (
            ['mpg123', '-q', local_audio],
            ['mpv', '--no-video', '--really-quiet', local_audio],
            ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', local_audio],
            ['play', '-q', local_audio],
        ):
            if which(cmd[0]):
                try:
                    Popen(cmd, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)
                    break
                except Exception:
                    continue


def findRealCommand():
    pid = getpid()
    for _ in range(5):
        try:
            with open(f'/proc/{pid}/stat') as f:
                ppid = int(f.read().split()[3])
            with open(f'/proc/{ppid}/cmdline') as f:
                cmdline = f.read().split('\x00')
            if cmdline and 'sudo' in cmdline[0]:
                cleanArgs = [a for a in cmdline if a and not a.startswith('-')]
                if len(cleanArgs) > 1:
                    return cleanArgs[1]
            pid = ppid
        except Exception:
            break

    return translations[currentLang]['unknown_command']


def getBinaryInfo(cmd):
    cmdBase   = basename(cmd)
    humanName = iconName = None

    specificRoutes = [
        pjoin('/usr/share/applications', f'{cmdBase}.desktop'),
        expanduser(f'~/.local/share/applications/{cmdBase}.desktop'),
    ]

    specificSet = frozenset(specificRoutes)
    allRoutes   = specificRoutes + glob('/usr/share/applications/*.desktop') \
                                 + glob(expanduser('~/.local/share/applications/*.desktop'))
    uniqueRoutes = list(dict.fromkeys(allRoutes))

    for filePath in uniqueRoutes:
        if not isfile(filePath):
            continue
        try:
            foundExec = False
            tempName = tempIcon = None
            with open(filePath, encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f'Name[{currentLang}]='):
                        tempName = line.split('=', 1)[1]
                    elif line.startswith('Name=') and not tempName:
                        tempName = line.split('=', 1)[1]
                    elif line.startswith('Icon=') and not tempIcon:
                        tempIcon = line.split('=', 1)[1]
                    elif line.startswith('Exec='):
                        if basename(line.split('=', 1)[1].strip().split()[0]) == cmdBase:
                            foundExec = True

                    if foundExec and tempName and tempIcon:
                        break
            if foundExec or filePath in specificSet:
                humanName = humanName or tempName
                iconName  = iconName  or tempIcon
                if humanName and iconName:
                    break
        except Exception:
            continue

    humanName = humanName or cmdBase.capitalize()
    iconName  = iconName  or 'utilities-terminal'

    for ext in ('.png', '.svg', '.xpm', '.jpg', '.jpeg'):
        if iconName.lower().endswith(ext):
            iconName = iconName[:-len(ext)]
            break
    iconNameClean = sub(r'[^a-zA-Z0-9_\-\+\.]', '', iconName)

    iconPath = None
    for ext in ('.svg', '.png', '.xpm'):
        p = f'/usr/share/pixmaps/{iconNameClean}{ext}'
        if exists(p):
            iconPath = p
            break

    if not iconPath and iconNameClean:

        iconDirs = [d for d in ('/usr/share/icons', expanduser('~/.local/share/icons')) if exists(d)]
        if iconDirs:
            try:
                out = check_output(
                    ['find', *iconDirs, '-type', 'f', '-name', f'{iconNameClean}.*'],
                    text=True, stderr=DEVNULL
                ).strip()
                lines = [l for l in out.split('\n') if l.endswith(('.png', '.svg', '.xpm'))]
                for l in lines:
                    if any(s in l for s in ('scalable', '256', '128', '96')):
                        iconPath = l
                        break
                if not iconPath and lines:
                    iconPath = lines[0]
            except Exception:
                pass

    finalIconData = None
    if iconPath and exists(iconPath):
        try:
            mimeType, _ = guess_type(iconPath)
            mimeType = mimeType or ('image/svg+xml' if iconPath.endswith('.svg') else 'image/png')
            with open(iconPath, 'rb') as f:
                finalIconData = f"data:{mimeType};base64,{b64encode(f.read()).decode()}"
        except Exception:
            pass

    if not finalIconData:
        svgRaw = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' width='48' height='48' fill='%230078D7'>"
            "<path d='M12 2L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-3zm0 17.9c-4.13-1.02-7-5.18-7-9.9V6.3l7-2.33 7 2.33v4.67c0 4.72-2.87 8.88-7 9.9z'/>"
            "</svg>"
        )
        finalIconData = 'data:image/svg+xml;charset=utf-8,' + quote(svgRaw)


    fullPath = which(cmd) or (cmd if exists(cmd) else translations[currentLang]['not_found'])
    vendor   = translations[currentLang]['unknown_vendor']
    if fullPath != translations[currentLang]['not_found']:
        try:
            vendorRaw = check_output(['dpkg', '-S', fullPath], text=True, stderr=DEVNULL).split(':')[0]
            vendor = vendorRaw.title().replace('-', ' ')
        except Exception:
            pass

    origin = translations[currentLang]['unknown_vendor']
    if fullPath and fullPath != translations[currentLang]['not_found']:
        pathLc = fullPath.lower()
        if '/media/' in pathLc or '/run/media/' in pathLc:
            origin = translations[currentLang]['origin_removable']
        elif '/mnt/' in pathLc or '.gvfs' in pathLc or ('/run/user/' in pathLc and 'gvfs' in pathLc):
            origin = translations[currentLang]['origin_network']
        elif 'downloads' in pathLc or '/tmp/' in pathLc:
            origin = translations[currentLang]['origin_download']
        elif fullPath.startswith('/'):
            origin = translations[currentLang]['origin_local']
        else:
            origin = translations[currentLang]['origin_system']

    return {'name': humanName, 'vendor': vendor, 'path': fullPath, 'origin': origin, 'icon': finalIconData}


def getWallpaperBase64():
    desktop = environ.get('XDG_CURRENT_DESKTOP', '').lower()
    try:
        if 'cinnamon' in desktop:
            cmd = ['gsettings', 'get', 'org.cinnamon.desktop.background', 'picture-uri']
        elif 'mate' in desktop:
            cmd = ['gsettings', 'get', 'org.mate.background', 'picture-filename']
        elif 'xfce' in desktop:
            cmd = ['xfconf-query', '-c', 'xfce4-desktop', '-p', '/backdrop/screen0/monitor0/workspace0/last-image']
        else:
            cmd = ['gsettings', 'get', 'org.gnome.desktop.background', 'picture-uri']
        path = unquote(
            check_output(cmd, text=True, stderr=DEVNULL).strip().replace("'", '').replace('file://', '')
        )
        if isfile(path):
            mimeType, _ = guess_type(path)
            mimeType = mimeType or 'image/jpeg'
            with open(path, 'rb') as f:
                return f"data:{mimeType};base64,{b64encode(f.read()).decode()}"
    except Exception:
        pass
    return ''


Thread(target=playUacAudio, daemon=True).start()

targetCommand = findRealCommand()

_wpResult = [None]
def _fetchWallpaper():
    _wpResult[0] = getWallpaperBase64()

wpThread = Thread(target=_fetchWallpaper, daemon=True)
wpThread.start()
binInfo = getBinaryInfo(targetCommand)
wpThread.join()
bgBase64 = _wpResult[0] or ''

with open(htmlPath, encoding='utf-8') as f:
    htmlContent = f.read()

t = translations[currentLang]
_placeholders = {
    '{{APP_NAME}}':                binInfo['name'],
    '{{VENDOR}}':                  binInfo['vendor'],
    '{{PATH}}':                    binInfo['path'],
    '{{ORIGIN}}':                  binInfo['origin'],
    '{{APP_ICON}}':                binInfo['icon'],
    '{{LBL_TITLE}}':               t['uac_title'],
    '{{LBL_HEADER}}':              t['header_lbl'],
    '{{LBL_VENDOR}}':              t['vendor_lbl'],
    '{{LBL_MORE_DETAILS}}':        t['more_details'],
    '{{LBL_PATH}}':                t['file_path'],
    '{{LBL_ORIGIN}}':              t['file_origin'],
    '{{LBL_PASSWORD_REQ}}':        t['password_req'],
    '{{LBL_PWINPUT_PLACEHOLDER}}': t['pw_input_placeholder'],
    '{{LBL_YES}}':                 t['lbl_yes'],
    '{{LBL_NO}}':                  t['lbl_no'],
}
_tplPattern = reCompile('|'.join(reEscape(k) for k in _placeholders))
htmlContent = _tplPattern.sub(lambda m: _placeholders[m.group(0)], htmlContent)

if bgBase64:
    htmlContent = htmlContent.replace(
        '</head>',
        f"<style>#bg-dim{{background-image:url('{bgBase64}')}}</style>\n</head>"
    )

api = UacBackend()
webviewWindow = webview.create_window(
    'UAC', html=htmlContent, js_api=api,
    frameless=True, fullscreen=True, on_top=True, background_color='#000000'
)
webview.start()

if api.capturedPassword is not None:
    stdout.write(api.capturedPassword + '\n')
    stdout.flush()
    _exit(0)
else:
    _exit(1)
