import sublime
import sublime_plugin
import base64
import os
import re
import urllib.parse
import urllib.request

IMAGE_FORMATS = 'jpg|jpeg|bmp|gif|png'

class HoverPreview(sublime_plugin.EventListener):
    def on_hover(self, view, point, hover_zone):
        if (hover_zone == sublime.HOVER_TEXT):
            next_double_quote = view.find('"', point).a
            next_single_quote = view.find("'", point).a
            next_parentheses = view.find(r"\)", point).a

            symbols_dict = { next_double_quote: '"', 
                             next_single_quote: "'",
                             next_parentheses: ')' }

            symbols = []
            if next_double_quote != -1:
                symbols.append(next_double_quote)
            if next_single_quote != -1:
                symbols.append(next_single_quote)
            if next_parentheses != -1:
                symbols.append(next_parentheses)

            # Check if symbols exist from the mouse pointer forward
            if len(symbols) == 0:
                return

            closest_symbol = min(symbols)
            symbol = symbols_dict[closest_symbol]

            # All quotes in view
            if symbol == ")":
                all_quotes = view.find_all(r"\(|\)")
                all_match = [item for item in all_quotes if (item.a == closest_symbol)]
            else:
                all_quotes = view.find_all(symbol)
                all_match = [item for item in all_quotes if item.a == closest_symbol]

            # If there are no matches return
            if len(all_match) == 0:
                return

            # Get final and initial region of quoted string
            final_region = all_match[0]
            index = all_quotes.index(final_region) - 1
            initial_region = all_quotes[index]

            if point < initial_region.b or point > final_region.a:
                return
            
            # String path for file
            path = view.substr(sublime.Region(initial_region.b, final_region.a))

            ### Handle URL's ###
            # Check URL (from http://codereview.stackexchange.com/questions/19663/http-url-validating)
            url = re.compile(
                r'^(?:http|ftp)s?://' # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
                r'localhost|' # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|' # ...or ipv4
                r'\[?[A-F0-9]*:[A-F0-9:]+\]?)' # ...or ipv6
                r'(?::\d+)?' # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            # Regex for images
            imageURL = re.compile('.+(?:' + IMAGE_FORMATS + ')')
            # Display and return if it's a URL with an image extension
            if (url.match(path) and imageURL.match(path)):
                url_path = urllib.parse.quote(path).replace("%3A", ":", 1)
                f = urllib.request.urlopen(url_path)
                encoded = str(base64.b64encode(f.read()), "utf-8")
                view.show_popup('<img src="data:image/png;base64,' + 
                                    encoded + 
                                '">', 
                                 flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY, 
                                 location=point)
                return
            ### End handle URL's ###

            path = path.strip().split('/')[-1]

            # Regex for images
            pattern = re.compile('([-@\w]+\.(?:' + IMAGE_FORMATS + '))')

            if (path and path != "" and pattern.match(path)):

                # Get base project folder
                base_folders = sublime.active_window().folders()

                # Find the first file that matches path
                for base_folder in base_folders:
                    file_name = ""
                    for root, dirs, files in os.walk(base_folder):
                        for file in files:
                            if file.endswith(path):
                                file_name = os.path.join(root, file)
                                break

                # Check that file exists
                if (file_name and os.path.isfile(file_name)):
                    encoded = str(base64.b64encode(
                                    open(file_name, "rb").read()
                                ), "utf-8")
                    view.show_popup('<img src="data:image/png;base64,' + 
                                        encoded + 
                                    '">', 
                                     flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY, 
                                     location=point)
                    return
                return
            return
        return
        
