from lib2to3.pgen2 import driver
from urllib import response
import dateutil.parser
from distutils.log import info
from django.shortcuts import render, redirect
from itsdangerous import exc
from matplotlib.style import context
import pandas as pd
import requests
# import scispacy
import spacy
import re
import nltk
from spacy import displacy
from spacy.matcher import Matcher
from nltk.tokenize import sent_tokenize, word_tokenize
from django.urls import reverse, reverse_lazy
import urllib.parse
import json


# Drug Recognition (4000+ Med Chemicals)
nlp = spacy.load("en_ner_bc5cdr_md")

# Trained model UCI Dataset (5000+ Med Chemicals)
# https://archive.ics.uci.edu/ml/datasets/Drug+Review+Dataset+%28Drugs.com%29#
nlp2 = spacy.load("Models/trained_model_5000")


# Person recognition
nlp5 = spacy.load('en_core_web_sm')


context = {}


def home(request):
    if request.method == 'POST':
        pdf = request.FILES['pdf']
        pg = request.POST['pg']
        lists = word_tokenize(pdftoword(pdf, int(pg) - 1))
        # print(lists)
        drug_list = drugs(lists)
        doctor = get_doctor(lists)
        date = get_date(lists)
        # print(drug_list, doctor, date)
        context = {'drug_list': drug_list, 'doctor': doctor, 'date': date}
        drug_list = ' '.join(map(str, drug_list))
        req = 'drug_list=' + drug_list
        req = req + '&doctor=' + str(doctor)
        req = req + '&date=' + str(date)
        return redirect('data/?' + f'{req}')

    return render(request, 'info_extract/home.html')


def data(request):
    context = {}
    drug_list = request.GET.get('drug_list', -1)
    doctor = request.GET.get('doctor', -1)
    date = request.GET.get('date', -1)
    new_drug_list = []
    d = ''
    open = 0
    # print(drug_list)
    for i, w in enumerate(drug_list):
        if w == '[':
            continue
        elif w == ']':
            new_drug_list.append([d])
            d = ''
        else:
            if w == "'":
                continue
            d += w
    print(new_drug_list)
    ultra_list = []
    for d in new_drug_list:
        ultra_list.append(d[0])
    print(ultra_list)
    ultra_list = list(dict.fromkeys(ultra_list))
    new_drug_list = ultra_list
    # new_drug_list = list(dict.fromkeys(new_drug_list))
    drug_info, adverse_reactions, del_indices, google_des, google_sideeff = get_drug_info(
        new_drug_list)
    new_drug_list = [i for j, i in enumerate(
        new_drug_list) if j not in del_indices]
    print(google_sideeff)
    if new_drug_list != -1 and new_drug_list != 'None':
        dlist = zip(new_drug_list, drug_info, adverse_reactions,
                    google_des, google_sideeff)
        context['drug_list'] = dlist
    if doctor != -1 and doctor != 'None':
        context['doctor'] = doctor
    if date != -1 and date != 'None':
        context['date'] = date
    return render(request, 'info_extract/data.html', context)


def get_drug_info(drug_list):
    drug_info = []
    adverse_reactions = []
    del_indices = []
    google_desc = []
    google_sideeff = []
    google = 'https://www.google.com/search?q='
    api = 'https://api.fda.gov/drug/label.json?search='
    for idx, drug in enumerate(drug_list):
        # print("drug = ", str(drug))
        if(drug[0] == ' '):
            drug = drug[1:]
        endpoint = api + str(drug)
        # print(endpoint)
        r = requests.get(endpoint)
        data = r.json()
        # print(data['results'])
        description = ""
        adverse_reaction = ""
        try:
            data = data['results']
            data = data[0]
            description = data['description'][0]
            adverse_reaction = data['adverse_reactions'][0]
            drug_info.append(description[:400] + '...')
            adverse_reactions.append(adverse_reaction[:400] + '...')
            google_des = google + str(drug) + " description"
            google_eff = google + str(drug) + " side effects"
            google_desc.append(google_des)
            google_sideeff.append(google_eff)
        except:
            del_indices.append(idx)
            pass
    return drug_info, adverse_reactions, del_indices, google_desc, google_sideeff


'''Drug Name &  Dose Extraction'''


def drugs(lists):
    try:
        text = ""
        for word in lists:
            text += word + ' '
        nlp_ob = nlp(text)

        pattern = [{'ENT_TYPE': 'CHEMICAL'}, {'IS_ASCII': True}]
        matcher = Matcher(nlp.vocab)
        matcher.add("DRUG_DOSE", [pattern])

        matches = matcher(nlp_ob)
        # print(nlp_ob)
        drugs_list = []
        for match_id, start, end in matches:
            # get string representation
            string_id = nlp.vocab.strings[match_id]
            span = nlp_ob[start:end]  # the matched span
            drugs_list.append([span.text])
            # print(string_id, start, end, span.text)
        return drugs_list
    except:
        return None


''' Doctors Name Extraction '''


def get_doctor(names_doc_tokens):
    try:
        def find_dr(word):
            for i1, w in enumerate(word):
                if (word[i1:i1+3]).lower() == 'dr.':
                    return i1
            return -1
        names_doc_text = ""
        for token_idx, w in enumerate(names_doc_tokens):
            if (find_dr(w) == 0) and (len(w) <= 15):
                break
        for word in names_doc_tokens:
            names_doc_text += word + ' '
        doctor = names_doc_tokens[token_idx]
        # print(doctor)
        nlp_names = nlp5(names_doc_tokens[token_idx] + ' ' +
                         names_doc_tokens[token_idx + 1] + '  ' + names_doc_tokens[token_idx + 2])
        # print(nlp_names)
        for name in nlp_names.ents:
            if name.label_ == 'PERSON':
                doctor = doctor + ' ' + str(name)
        return doctor
    except:
        return None


'''Extract Date'''


def get_date(dates_tokens):
    try:
        def find_date(word):
            for i1, w in enumerate(word):
                if (word[i1:i1+4]).lower() == 'date':
                    # print(word)
                    return i1
            return -1

        dates_text = ""
        for token_idx, w in enumerate(dates_tokens):
            if (find_date(w) != -1):
                break
        probable_dates = [dates_tokens[token_idx + 1],
                          dates_tokens[token_idx + 2]]
        # print(dates_tokens)
        date = ''
        for probable_date in probable_dates:
            try:
                date = dateutil.parser.parse(probable_date).date()
                break
            except:
                pass
        return date
    except:
        return None


'''Pdf To Text'''


def pdftoword(pdf, pg):
    from io import StringIO
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.pdfpage import PDFPage
    from pdfminer.pdfparser import PDFParser

    output_string = StringIO()
    with pdf as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for i, page in enumerate(PDFPage.create_pages(doc)):
            if i == pg:
                interpreter.process_page(page)
    return output_string.getvalue()
