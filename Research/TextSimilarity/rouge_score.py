from rouge import Rouge

with open('texts/Goldilocks1.txt') as f:
   t1=f.read()

with open('texts/Goldilocks2.txt') as f:
   t2=f.read()

with open('texts/US-Elections1.txt') as f:
   t3=f.read()

with open('texts/US-Elections2.txt') as f:
   t4=f.read()

rouge = Rouge()
print(rouge.get_scores(t1, t1)[0]['rouge-1']['r']) #1.0
print(rouge.get_scores(t1, t2)[0]['rouge-1']['r']) #0.5857142857142857
print(rouge.get_scores(t3, t4)[0]['rouge-1']['r']) #0.23333333333333334
print(rouge.get_scores(t1, t3)[0]['rouge-1']['r']) #0.16363636363636364