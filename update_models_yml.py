import yaml
import os

config_path = 'config/models.yml'
with open(config_path, 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

desc = data['models']['default']['chatbot']['description']
if "Markdown" not in desc:
    data['models']['default']['chatbot']['description'] = desc + " Используй Markdown для форматирования."

with open(config_path, 'w', encoding='utf-8') as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)

print("config/models.yml updated successfully")
