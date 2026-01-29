
import json
import os

def fix_dashboard():
    # 1. Purge Tickers from Ledger Cache
    ledger_path = 'data/ledger_cache.json'
    if os.path.exists(ledger_path):
        try:
            with open(ledger_path, 'r') as f:
                data = json.load(f)
            
            assets = data.get('assets', {})
            targets = ['RIO', 'LGEN', 'BATS', 'RIOl', 'LGENl', 'BATSl', 'RIO.L', 'LGEN.L', 'BATS.L']
            
            removed_count = 0
            for t in targets:
                if t in assets:
                    del assets[t]
                    removed_count += 1
            
            with open(ledger_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Purged {removed_count} tickers from ledger_cache.json")
        except Exception as e:
            print(f"Error processing ledger_cache.json: {e}")

    # 2. Update Template Version
    template_path = 'templates/base.html'
    if os.path.exists(template_path):
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content.replace('v29.0', 'v30.0')
            
            if 'v30.0' in new_content and new_content != content:
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print("Updated templates/base.html to v30.0")
            else:
                print("Template already v30.0 or tag not found")
        except Exception as e:
            print(f"Error processing base.html: {e}")
            
if __name__ == "__main__":
    fix_dashboard()
