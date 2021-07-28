#Prints histogram data of target sequence lengths
with open(r'data/docstring-dataset/processed/test/postprocessed/data.csv', 'r', encoding="ISO-8859-1") as file:
    lines = file.readlines()

histogram = [0] * 1000
for line in lines:
    target = line.split(' ')[0]
    parts = target.split('|')
    histogram[min(len(parts), 999)] += 1

for i in range(len(histogram)):
    print(str(i) + ' ' + str(histogram[i]))