# Drug_Recognition_NER
## Objective : To Identify Drug names(Chemicals) By 2 methods
   * To use a Pre-trained model
     * Used Spacys Pretrained model(en_ner_bc5cdr_md) from <a href = "https://allenai.github.io/scispacy/"> HERE</a> 
       whose F1 score is around ~85%
   * Training a model
      * Trained a blank model using <a href = "https://archive.ics.uci.edu/ml/datasets/Drug+Review+Dataset+%28Drugs.com%29#">UCI Dataset</a> 
   
   | Model | Training Accuracy % | Testing  Accuracy % |
| :---         |     :---:      |          ---: |
| Pretrained Spacy  Model(en_ner_bc5cdr_md)   |  84.49	     |  51.27   |
| Our Trained model     | 76.42       |  72.82     |

## Setup

Create a virtual environment  `requirements.txt` file should list all Python libraries required, and they will be installed using:

```
pip install -r requirements.txt
```
Test the Jupyter NB Code @ - https://github.com/mdrazak2001/Drug_Recognition_NER/blob/main/Models/Se_med_ner.ipynb

