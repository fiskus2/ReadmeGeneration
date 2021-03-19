from semantic_text_similarity.models import WebBertSimilarity
from semantic_text_similarity.models import ClinicalBertSimilarity

web_model = WebBertSimilarity(device='cpu', batch_size=10)

clinical_model = ClinicalBertSimilarity(device='cpu', batch_size=10)

with open('texts/Goldilocks1.txt') as f:
   t1=f.read()

with open('texts/Goldilocks2.txt') as f:
   t2=f.read()

with open('texts/US-Elections1.txt') as f:
   t2=f.read()

with open('texts/US-Elections2.txt') as f:
   t2=f.read()

print(web_model.predict([(t1, t1)])) #[4.61928]
print(web_model.predict([(t1, t2)])) #[3.4328978]
print(web_model.predict([(t3, t4)])) #[1.7933936]
print(web_model.predict([(t1, t3)])) #[0.17237176]
print('-------')
print(clinical_model.predict([(t1, t1)])) #[4.939695]
print(clinical_model.predict([(t1, t2)])) #[3.516664]
print(clinical_model.predict([(t3, t4)])) #[1.2412066]
print(clinical_model.predict([(t1, t3)])) #[0.4816986]
