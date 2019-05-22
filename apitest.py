import requests
import re
import time
from bs4 import BeautifulSoup
import json
import os
from collections import deque

text = """[1] „Ob eine Äußerung noch Satire oder bereits ein <i>Hasskommentar</i> sei, dürfe nicht privaten Betreibern überlassen werden. Dies müsse der Rechtsstaat entscheiden.“
[1] „Im Rahmen eines Aktionstages gegen <i>Hasskommentare</i> im Internet, koordiniert durch das Bundeskriminalamt, hat die Itzehoer Bezirkskriminalinspektion am Dienstagmorgen eine Wohnung in Wedel durchsucht.“
[1] „Dadurch, dass nicht jeder herabsetzende Kommentar automatisch ein <i>Hasskommentar</i> ist, der gelöscht wird, sondern Vertreter der PC-Ideologie als Gatekeeper dienen und entscheiden, welche Art von Kommentaren legitim sind und welche nicht […], führt der »Kampf gegen den Hass« einseitig dazu, dass unliebsame Meinungen gelöscht und praktisch zensiert werden.“
[1] „Da ich vor Kurzem die tolle Idee eines öffentlichen Posts hatte, haben sich auf meiner Pinnwand hunderte <i>Hasskommentare</i> gesammelt. Mir wird ganz übel, als ich die schrecklichen Nachrichten lese.“"""

def getWordType(contents):
    # print(contents)
    x= re.search(r"=== (\{\{Wortart\|(.*?)\|Deutsch\}\}.*)",contents)
    # print("Here",x.groups())
    return f"{x.group(2)} adjektivisch" if "adjektivische Deklination" in x.group(1) else x.group(2)

articles = {"m": "der", "f": "die", "n": "das"}
def joinPlural(els):
    print(els)
    return ", ".join([el if isinstance(el,str) else ", ".join(el if len(el)==1 else ["("+ ", ".join(el) +")"]) for el in els])
    # results = []
    # for el in els:
    #     print(f"el: {el}")
    #     print("joined", ("("+ ", ".join(el) +")"))
    #     results.append(el if isinstance(el,str) else ", ".join(el if len(el)==1 else ["("+ ", ".join(el) +")"]))
    # return results
def getPlural(contents, wordtype):
    if wordtype=="Substantiv adjektivisch":
        table = re.search(r"\{\{Deutsch adjektivisch Übersicht\s*(.*?)\s*\}\}", contents, flags=re.DOTALL).group(1)
        stamms = re.findall(r"\|Stamm.*?=(\w*)",table)
        stamm = ""
        for n, x in enumerate(stamms):
            stamm += (("" if n==0 else "/") + f"{x}") if x not in stamms[:n] else ""
        return f"der {stamm}", stamm.replace("/","n/")+"n"
    elif wordtype=="Substantiv":
        # table = re.search(r"\{\{Deutsch Substantiv Übersicht.*?\}\}",contents, flags=re.MULTILINE)
        table = re.search(r"\{\{Deutsch Substantiv Übersicht\s*(.*?)\s*\}\}", contents, flags=re.DOTALL).group(1)
        genders = re.findall(r"\|Genus.*?=(\w*)",table)
        
        singulars = re.findall(r"\|Nominativ Singular.*?=(\w*)",table)
        singular = ""
        for n, x in enumerate(singulars):
            singular += (("" if n==0 else "/") + f"{x}") if x not in singulars[:n] else ""
        plurals = re.findall(r"\|Nominativ Plural.*?=(\w*)",table)
        plural = ""
        for n, x in enumerate(plurals):
            plural += (("" if n==0 else "/") + f"{x}") if x not in plurals[:n] else ""
        article = "/".join(articles[x] for x in genders)

        return article, singular, plural
    elif wordtype=="Adjektiv":
        table = re.search(r"\{\{Deutsch Adjektiv Übersicht\s*(.*?)\s*\}\}", contents, flags=re.DOTALL).group(1)
        komp = re.findall(r"\|Komparativ.*?=(\w*)",table)
        sup = re.findall(r"\|Superlativ.*?=(\w*)",table)
        return joinPlural([komp,sup])
    elif wordtype=="Verb":
        table = re.search(r"\{\{Deutsch Verb Übersicht\s*(.*?)\s*\}\}", contents, flags=re.DOTALL).group(1)
        präsens = re.findall(r"\|Präsens_er, sie, es.*?=(\w*)",table)
        präteritum = re.findall(r"\|Präteritum_ich.*?=(\w*)",table)
        partizip = re.findall(r"\|Partizip II.*?=(\w*)",table)
        hilfverb = "/".join(re.findall(r"\|Hilfsverb.*?=(\w*)",table)).replace("sein","ist").replace("haben","hat")
        return joinPlural([präsens, präteritum, hilfverb+" " + joinPlural([partizip])])
    else:
        return None

def splitMultDefs(contents, lang = "de"):
    if contents is None: return None
    langsectiontitles = {"de": "({{Sprache|Deutsch}})", "en": "German"}
    split = re.split(r"(^==[^=]*?==$)", contents, flags=re.MULTILINE)
    assert len(split)%2==1, "Wrong number of sections in the page."
    for n in range((len(split)-1)//2):
        if langsectiontitles[lang] in split[1+2*n]:
            sectiontitle = split[1+2*n]
            section = split[1+2*n]+split[1+2*n+1]
    # print(f"\n{repr(section)}")
    multipledeftitles = {"de": r"(=== \{\{Wortart\|.*?\|Deutsch\}\}.*)", "en": r"([.\s]*)"}
    data = []
    split = re.split(multipledeftitles[lang], section)
    # print()
    # for x in split:
    #     print(f"\nHere{repr(x)}")
    for n in range((len(split)-1)//2):
        # if re.search(multipledeftitles[lang], split[1+2*n]):
        data.append(sectiontitle+"\n"+split[1+2*n]+split[1+2*n+1])
    # for x in data:
    #     print(f"\nThere{repr(x)}")
    return data

def replacer(m, replacements,namedgroups):
    d = m.groupdict()
    key = None
    for k,v in d.items():
        if v is not None:
            key = k
    return m.expand(namedgroups[key]) if key is not None else replacements[re.escape(m.group(0))]
def kreplacer(m):
    print(m)
    result = "<i>"+", ".join(m.group(1).split("|"))+":</i>"
    result = re.sub(r", t\d+=(.*?),", r"\g<1>", result).replace("_","").replace("ft=","")
    return result
def curlyjoiner(m):
    return "<i>"+"".join(m.group(1).split("|"))+"</i>"
def getMeanings(contents):
    rawdata = re.search(r"\{\{Bedeutungen\}\}\s*(.*?)(?:\n\n|\n\{\{)", contents, flags=re.DOTALL).group(1)
    replacements = {r"\[\[": "", r"\]\]": "", "''(?P<quote>.*?)''": "",
                    r":+\[(?P<start>\d)\]": "", r"kPl\.": "kein Plural"}
    namedgroups = {"quote": r"<i>\g<quote></i>", "start": r"[\g<start>]"}
    rawdata = re.sub(r"\{\{K\|(.*?)\}\}", lambda x: kreplacer(x), rawdata)
    rawdata = re.sub(r"\{\{(.*?)\}\}", lambda x: curlyjoiner(x), rawdata)
    if replacements:
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
    print(rawdata)

def getExamples(contents):
    rawdata = re.search(r"\{\{Beispiele\}\}\s*(.*?)(?:\n\n|\n\{\{)", contents, flags=re.DOTALL).group(1)
    replacements = {r"\[\[": "", r"\]\]": "", "''(?P<quote>.*?)''": "",
                    r":+\[(?P<start>\d)\]": "", r"kPl\.": "kein Plural", r"(?P<ref><ref>.*?</ref>)": ""}
    namedgroups = {"quote": r"<i>\g<quote></i>", "start": r"[\g<start>]", "ref": ""}
    if replacements:
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
    print(rawdata)

def addFromFile():
    file = open(os.path.expanduser("~/Desktop/ankiaddwords.txt"))
    contents = file.read()
    file.close()
    data = []
    for line in contents.splitlines():
        word = re.search(r"^\w+", line)
        number = re.search(r"\d+", line)
        hint = re.search(r"\(.*\)", line)
        data.append([word.group(0),int(number.group(0)) if number else None,hint.group(0) if hint else None])
    print(data)

def getIPA2(words, lang="de"):
    contentsf = {"de": getIPA2contents, "en": getIPA2contentsen}
    if isinstance(words,str): words = [words]
    contents = getWiktionaryContents(words, lang=lang)
    return {word: "[.]" if contents[word] is None else contentsf[lang](contents[word]) for word in words}

def getIPA2contents(contents):
    word = re.search(r"==\s*(\w+)\s*.*?==",contents)
    print(f"\ncontents2 {repr(contents)}")
    word=word.group(1)
    rawdata = re.search(r"\{\{IPA\}\}\s*(.*)\s*", contents).group(1)
    replacements = {"''(?P<quote>.*?)''": "", r"\{\{Lautschrift\|(?P<laut>.*?)\}\}": "", r"(?P<ref><ref>.*?</ref>)": "",
        r"\[\[": "", r"\]\]": "",}
    namedgroups = {"quote": r"<i>\g<quote></i>", "ref": "", "laut": r"[\g<laut>]"}
    if replacements:
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
    if word in ["der","ist","sich","ich","du","er","ihr"]:
        rawdata = rawdata.split("]")[0]+"]"
    if re.search(r"\]\S+", rawdata):
        rawdata = f"({rawdata})"
    return rawdata

def getIPA2contentsen(contents):
    rawdata = re.findall(r".*\{\{IPA\|(.*?)\|lang=de\}\}[ ]*(.*)", contents)
    ipas = []
    for ipa in rawdata:
        s = ipa[0].split("|")
        a = re.sub(r"\{\{a\|(.*?)\}\}",r"\g<1>",ipa[1]) if ipa[1] else ""
        if len(s) > 1 or ipa[1]:
            ipas.append("("+", ".join(s)+(f" {a}" if a else "")+")")
    if len(ipas) > 1:
        return "("+", ".join(ipas)+")"
    else:
        return ", ".join(ipas)

def getTranslation(contents, lang="en"):
    rawdata = re.search(r"\*\{\{"+lang+r"}\}:\s*(.*)", contents)
    if rawdata:
        rawdata = rawdata.group(1)
        rawdata = re.sub(r"\{\{Ü\|"+lang+r"\|(.*?)\}\}", r"\g<1>", rawdata)
        return rawdata
    else:
        return None

def getWiktionaryContents(words, whichWords = 1, lang="de"):
    words = [words] if isinstance(words,str) else words
    whichWords = [whichWords]*len(words) if isinstance(whichWords,int) else whichWords
    texts = {}
    for n in range(1+(len(words)-1)//50):
        words2 = words[50*n:50*(n+1)]
        data = requests.get(f"https://"+lang+f".wiktionary.org/w/api.php?action=query&format=json&prop=revisions&rvprop=content&rvslots=*&titles="+"|".join(words2))
        data = json.loads(data.text)["query"]["pages"]
        contents = {data[el]["title"]: None if int(el)<0 else data[el]["revisions"][0]["slots"]["main"]["*"] for el in data}
        print(f"\ncontents {contents}")
        for word in contents:
            multDefs = splitMultDefs(contents[word], lang=lang)
            print(f"\nmultdefs {multDefs}")
            texts[word] = multDefs[whichWords[50*n+words2.index(word)]-1] if multDefs else None
    return texts

# def addAllIpas(notes):
#     actm = 0
#     actn = 0
#     wordstoget = set()
#     for m, note in enumerate(notes):
#         pass

def addAllIpas(notes):
    actm = 0
    actn = 0
    wordstoget = set()
    jobs = deque()
    fields = "German", "Plural and inflected forms"
    matchstring = r"(; *|, *|/ *|\n *|<.+?>|\)|\(| +|\. *)"
    for m, note in enumerate(notes):
        print(f"m of note: {m}")
        jobs.append([note,1,[]])
        for field in fields:
            entry = note[field]
            print(f"for field <{field}> entry len {len(entry.split())} <{entry}>")
            breakdowns = jobs[-1][2]
            breakdowns.append([])
            print(f"breakdown <{re.split(matchstring,entry)}>")
            for x in re.split(matchstring,entry,flags=re.MULTILINE):
                if x=="" or re.search(matchstring,x,flags=re.MULTILINE):
                    breakdowns[-1].append([0,x])
                    # print(f"breakdown with numbers <{jobs[-1][1][-1]}>")
                else:
                    breakdowns[-1].append([1,x])
                    # print(f"breakdown with numbers <{jobs[-1][1][-1]}>")
                    wordstoget.add(x)
                    if len(wordstoget) == 50:
                        print(f"\nFilled 50 words")
                        ipas = getIPA2(list(wordstoget))
                        processIPAs(jobs, ipas, fields)
                        wordstoget = set()
        jobs[-1][1]=0
    if jobs:
        ipas = getIPA2(list(wordstoget))
        print(f"\nprocessing the end\nlen wordstoget: {len(wordstoget)}\nipas: {ipas}\nwordstoget: {wordstoget}")
        processIPAs(jobs, ipas, fields)
        wordstoget = set()
        
def processIPAs(jobs, ipas, fields, checkEnglish=True):
    for k, job in enumerate(jobs):
        # print(f"job: {job}")
        for m, breakdown in enumerate(job[2]):
            for n, el in enumerate(breakdown):
                # print(f"el start {el}")
                if el[0]==1:
                    el[0]=0
                    ipa=ipas[el[1]]
                    if ipa == "[.]" and checkEnglish:
                        el[1] = getIPA2(el[1], lang="en")[el[1]]
                    else:
                        el[1] = ipa
                # print(f"el end {el}")
            print(f"breakdown {breakdown}\nconnected {list(zip(*breakdown))}\nstring {''.join(list(zip(*breakdown))[1])}")
            job[0][fields[m]]="".join(list(zip(*breakdown))[1])
        if job[1]==0: jobs[k]=None
    while jobs and jobs[0] is None:
        jobs.popleft()

notes = [
    {"German": "das Haus", "Plural and inflected forms": "die Häuser"},
    {"German": "der Hund", "Plural and inflected forms": """
    auf die Ethik bezogen, die Ethik betreffend, Trennungsspalt, der durch das Zerreißen eines materiellen Gegenstandes entsteht
    die zeichnerische Planung oder Erfassung eines dreidimensionalen Gegenstandes oder eines Gebäudes auf einer horizontalen oder vertikalen Bildebene
    Sein Fernbleiben von der Feier kränkte die Gastgeberin sehr. Der Graf kränkt sich über das flegelhafte Benehmen seiner Töchter.
    beleidigt schweigen, um seinen Unmut zu zeigen und dabei meist den Mund verziehen
    """}
]

# w = """[1] <i>keine Steigerung</i>: auf die Ethik bezogen, die Ethik betreffend
# [2] gemäß der Ethik sich verhaltend"""

def newlinetodiv(text):
    return re.sub(r"(\n|^)(.*)\n",r"\g<1><div>\g<2></div>\n",text)

# print(newlinetodiv(w))

# addAllIpas(notes)

# a = [[],[]]

# for n, x in enumerate(a):
#     x.append(1)

# print(a)

# x = re.match("(?=\w+)[^\d]+","asd")
# print(x)

lang="de"
words = "beste"
whichWords = [1]
texts = getWiktionaryContents(words, whichWords=whichWords, lang=lang)
# print(texts)
# print(getWordType(texts[words]))
# print(getPlural(texts[words], getWordType(texts[words])))
print(getIPA2(words,lang=lang))

# print(word)
# for word, content in getWiktionaryContents(word).items():
#     print(f"word {word}, type {getWordType(content)}")
# print(getWiktionaryContents(word))

# data = requests.get(f"https://de.wiktionary.org/w/api.php?action=query&format=json&prop=revisions&rvprop=content&rvslots=*&titles="+word)
# # data = requests.get(f"https://en.wiktionary.org/w/api.php?action=query&format=json&prop=revisions&rvprop=content&rvslots=*&titles="+word)
# data = json.loads(data.text)["query"]["pages"]
# # print(data)
# content = {data[el]["title"]: None if el==-1 else data[el]["revisions"][0]["slots"]["main"]["*"] for el in data}
# text = splitMultDefs(content[word])[0]
# text = splitMultDefsen(content[word])[0]
# print(text)

# print(getTranslation(text, lang="et"))
# print(getIPA(text))
# print(getIPAen(text))
# print(content[word])
# print(content)

# getExamples(text)

# newlinetodiv(text)

# splitMultDefs(text)
# print(getWordType(text))
# wordType = getWordType(text)
# plural = getPlural(text, wordType)

# print(f"wordType: {wordType}\nplural: {plural}")

# x = """== hand ({{Sprache|Englisch}}) ==
# === {{Wortart|Substantiv|Englisch}} ===
# """
# y = re.split(r"^== .*? ==$",x,flags=re.MULTILINE)
# print(y)

# f = requests.get(f"https://de.wiktionary.org/w/api.php?action=query&format=json&prop=revisions&rvprop=content&rvslots=*&titles=schützen|frech")
# data = json.loads(f.text)["query"]["pages"]
# # for el in data:
# #     print(data[el]["title"])
# #     if el != -1:
# #         print(data[el]["revisions"][0]["slots"]["main"]["*"])
# data = {data[el]["title"]: None if el==-1 else data[el]["revisions"][0]["slots"]["main"]["*"] for el in data}
# print(data)
#     # if
# # print(json.dumps(data, sort_keys=True, indent=4))
