"""
Max Assistant - System Controller
Handles opening applications, websites, and system commands on Windows.
"""
import subprocess
import webbrowser
import os
import urllib.parse


class SystemController:
    """Controls system applications, websites, and OS commands."""

    # ─── Desktop Application Mappings ───
    APP_COMMANDS = {
        # System Utilities
        'notepad': 'notepad.exe',
        'calculator': 'calc.exe',
        'calc': 'calc.exe',
        'paint': 'mspaint.exe',
        'file explorer': 'explorer.exe',
        'explorer': 'explorer.exe',
        'task manager': 'taskmgr.exe',
        'settings': 'start ms-settings:',
        'control panel': 'control.exe',
        'command prompt': 'cmd.exe',
        'cmd': 'cmd.exe',
        'terminal': 'wt.exe',
        'powershell': 'powershell.exe',
        'snipping tool': 'snippingtool.exe',
        'snip': 'snippingtool.exe',
        'device manager': 'devmgmt.msc',
        'disk management': 'diskmgmt.msc',
        'registry editor': 'regedit.exe',
        'system info': 'msinfo32.exe',
        'resource monitor': 'resmon.exe',
        'character map': 'charmap.exe',
        'magnifier': 'magnify.exe',
        'on-screen keyboard': 'osk.exe',
        'remote desktop': 'mstsc.exe',
        'wordpad': 'wordpad.exe',

        # Microsoft Office
        'word': 'start winword',
        'excel': 'start excel',
        'powerpoint': 'start powerpnt',
        'outlook': 'start outlook',
        'onenote': 'start onenote',
        'access': 'start msaccess',

        # Browsers
        'chrome': 'start chrome',
        'edge': 'start msedge',
        'firefox': 'start firefox',
        'brave': 'start brave',

        # Development
        'vs code': 'code',
        'visual studio code': 'code',
        'vscode': 'code',
        'visual studio': 'start devenv',
        'git bash': 'start git-bash',

        # Media
        'spotify': 'start spotify:',
        'vlc': 'start vlc',
        'windows media player': 'start wmplayer',
        'groove music': 'start mswindowsmusic:',
        'photos': 'start ms-photos:',
        'camera': 'start microsoft.windows.camera:',
        'movies and tv': 'start mswindowsvideo:',
        'voice recorder': 'start windowssoundrecorder:',

        # Communication
        'whatsapp': 'start whatsapp:',
        'telegram': 'start telegram:',
        'discord': 'start discord:',
        'teams': 'start msteams:',
        'skype': 'start skype:',
        'zoom': 'start zoom',

        # Others
        'store': 'start ms-windows-store:',
        'microsoft store': 'start ms-windows-store:',
        'xbox': 'start xbox:',
        'clock': 'start ms-clock:',
        'alarms': 'start ms-clock:',
        'maps': 'start bingmaps:',
        'weather': 'start bingweather:',
        'calendar': 'start outlookcal:',
        'mail': 'start outlookmail:',
        'feedback hub': 'start feedback-hub:',
        'tips': 'start ms-get-started:',
    }

    # ─── Website URL Mappings ───
    WEBSITE_URLS = {
        'youtube': 'https://www.youtube.com',
        'google': 'https://www.google.com',
        'gmail': 'https://mail.google.com',
        'whatsapp web': 'https://web.whatsapp.com',
        'facebook': 'https://www.facebook.com',
        'twitter': 'https://www.twitter.com',
        'x': 'https://www.x.com',
        'instagram': 'https://www.instagram.com',
        'github': 'https://www.github.com',
        'chatgpt': 'https://chat.openai.com',
        'linkedin': 'https://www.linkedin.com',
        'netflix': 'https://www.netflix.com',
        'amazon': 'https://www.amazon.com',
        'reddit': 'https://www.reddit.com',
        'spotify web': 'https://open.spotify.com',
        'wikipedia': 'https://www.wikipedia.org',
        'stackoverflow': 'https://stackoverflow.com',
        'stack overflow': 'https://stackoverflow.com',
        'pinterest': 'https://www.pinterest.com',
        'tiktok': 'https://www.tiktok.com',
        'twitch': 'https://www.twitch.tv',
        'canva': 'https://www.canva.com',
        'figma': 'https://www.figma.com',
        'notion': 'https://www.notion.so',
        'drive': 'https://drive.google.com',
        'google drive': 'https://drive.google.com',
        'google docs': 'https://docs.google.com',
        'google sheets': 'https://sheets.google.com',
        'google maps': 'https://maps.google.com',
        'google translate': 'https://translate.google.com',
    }

    def open_application(self, app_name: str) -> dict:
        """Open a desktop application or website with smart fallbacks."""
        app_key = app_name.lower().strip()

        # Clean common prefixes/suffixes
        for prefix in ['open ', 'launch ', 'start ']:
            if app_key.startswith(prefix):
                app_key = app_key[len(prefix):].strip()

        # Check website mappings first if it's a known web service
        if app_key in self.WEBSITE_URLS:
            return self.open_website(self.WEBSITE_URLS[app_key], app_name)

        # Direct desktop app match
        if app_key in self.APP_COMMANDS:
            cmd = self.APP_COMMANDS[app_key]
            result = self._run_command(cmd, app_name)
            # If whatsapp or spotify fails locally, open their web version
            if not result.get('success'):
                if 'whatsapp' in app_key:
                    return self.open_website('https://web.whatsapp.com', 'WhatsApp Web')
                elif 'spotify' in app_key:
                    return self.open_website('https://open.spotify.com', 'Spotify Web')
            return result

        # Fuzzy match for apps
        for key, cmd in self.APP_COMMANDS.items():
            if key in app_key or app_key in key:
                return self._run_command(cmd, key)

        # Fuzzy match for websites
        for key, url in self.WEBSITE_URLS.items():
            if key in app_key or app_key in key:
                return self.open_website(url, key)

        # Try direct execution via start
        return self._run_command(f'start {app_name}', app_name)

    def open_website(self, url: str, site_name: str = "") -> dict:
        """Open a website in the default browser."""
        try:
            # Check if it's a known site name
            site_key = (site_name or url).lower().strip()
            if site_key in self.WEBSITE_URLS:
                url = self.WEBSITE_URLS[site_key]

            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            webbrowser.open(url)
            display_name = site_name or url
            return {
                'success': True,
                'message': f'Opened {display_name}',
                'action': 'open_website',
                'target': url
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to open website: {str(e)}',
                'action': 'open_website'
            }

    def search_web(self, query: str) -> dict:
        """Search the web using Google."""
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            webbrowser.open(url)
            return {
                'success': True,
                'message': f'Searching Google for: {query}',
                'action': 'search_web',
                'query': query
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Search failed: {str(e)}',
                'action': 'search_web'
            }

    def play_on_youtube(self, query: str) -> dict:
        """Search and play something on YouTube."""
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.youtube.com/results?search_query={encoded_query}"
            webbrowser.open(url)
            return {
                'success': True,
                'message': f'Playing on YouTube: {query}',
                'action': 'play_on_youtube',
                'query': query
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'YouTube play failed: {str(e)}',
                'action': 'play_on_youtube'
            }

    def system_command(self, action: str) -> dict:
        """Execute system commands."""
        commands = {
            'shutdown': 'shutdown /s /t 5',
            'restart': 'shutdown /r /t 5',
            'lock': 'rundll32.exe user32.dll,LockWorkStation',
            'sleep': 'rundll32.exe powrprof.dll,SetSuspendState 0,1,0',
            'screenshot': 'snippingtool',
            'volume_up': 'powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"',
            'volume_down': 'powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"',
            'mute': 'powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"',
            'brightness_up': 'powershell -c "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [Math]::Min(100, (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness + 10))"',
            'brightness_down': 'powershell -c "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [Math]::Max(0, (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness - 10))"',
        }

        action_key = action.lower().strip()

        if action_key in commands:
            return self._run_command(commands[action_key], action_key)
        else:
            return {
                'success': False,
                'message': f'Unknown system command: {action}',
                'action': 'system_command'
            }

    def _run_command(self, command: str, name: str) -> dict:
        """Execute a system command."""
        try:
            if command.startswith('start '):
                subprocess.Popen(command, shell=True)
            else:
                subprocess.Popen(command, shell=True)

            return {
                'success': True,
                'message': f'Opened {name}',
                'action': 'run_command',
                'command': command
            }
        except FileNotFoundError:
            return {
                'success': False,
                'message': f'Application "{name}" not found on this system.',
                'action': 'run_command'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error opening {name}: {str(e)}',
                'action': 'run_command'
            }
