import re

with open('scratch/aishe_main.js', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('getEncryptedValue(J){')
if pos != -1:
    print('--- getEncryptedValue & helper methods ---')
    print(text[pos-200:pos+1200])
