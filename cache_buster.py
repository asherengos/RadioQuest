import os
import re
import time

# Get current timestamp
version = int(time.time())
css_dir = os.path.join('static', 'css')

for filename in os.listdir(css_dir):
    if filename.endswith('.css'):
        filepath = os.path.join(css_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # Only add ?v= if not already present
        def cache_bust(match):
            url = match.group(1)
            if '?' in url:
                return f"url({url})"
            return f"url({url}?v={version})"
        new_content = re.sub(r"url\(([^)]+)\)", cache_bust, content)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filename} with cache-busting params") 