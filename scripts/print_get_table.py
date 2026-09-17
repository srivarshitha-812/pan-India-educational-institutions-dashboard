with open('scratch/337.52e2d3e8e3776afe.js', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('let Qa=')
get_table_pos = text.find('getTable(){', pos)
print(text[get_table_pos:get_table_pos+3000])
