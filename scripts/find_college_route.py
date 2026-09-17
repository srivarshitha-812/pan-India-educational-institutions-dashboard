import re

with open('scratch/337.52e2d3e8e3776afe.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Look for route definition with collegeDetails
pos = text.find('collegeDetails')
while pos != -1:
    print('--- collegeDetails snippet ---')
    print(text[max(0, pos-150):min(len(text), pos+300)])
    pos = text.find('collegeDetails', pos+1)
