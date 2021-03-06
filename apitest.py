import requests
import re
import time
from bs4 import BeautifulSoup
import json
import os
from collections import deque
import sys

text = """[1] „Ob eine Äußerung noch Satire oder bereits ein <i>Hasskommentar</i> sei, dürfe nicht privaten Betreibern überlassen werden. Dies müsse der Rechtsstaat entscheiden.“
[1] „Im Rahmen eines Aktionstages gegen <i>Hasskommentare</i> im Internet, koordiniert durch das Bundeskriminalamt, hat die Itzehoer Bezirkskriminalinspektion am Dienstagmorgen eine Wohnung in Wedel durchsucht.“
[1] „Dadurch, dass nicht jeder herabsetzende Kommentar automatisch ein <i>Hasskommentar</i> ist, der gelöscht wird, sondern Vertreter der PC-Ideologie als Gatekeeper dienen und entscheiden, welche Art von Kommentaren legitim sind und welche nicht […], führt der »Kampf gegen den Hass« einseitig dazu, dass unliebsame Meinungen gelöscht und praktisch zensiert werden.“
[1] „Da ich vor Kurzem die tolle Idee eines öffentlichen Posts hatte, haben sich auf meiner Pinnwand hunderte <i>Hasskommentare</i> gesammelt. Mir wird ganz übel, als ich die schrecklichen Nachrichten lese.“"""

def remHTML(text):
    return BeautifulSoup(text, "html.parser").text

def getWordType(contents):
    # print(contents)
    x= re.search(r"=== (\{\{Wortart\|(.*?)\|Deutsch\}\}.*)",contents)
    # print("Here",x.groups())
    return f"{x.group(2)} adjektivisch" if "adjektivische Deklination" in x.group(1) else x.group(2)

articles = {"m": "der", "f": "die", "n": "das"}
subadjarticles = {"m": "ein", "f": "eine", "n": "ein"}
subadjendings = {"m": "r", "f": "", "n": "s"}
def joinPlural(els):
    return ", ".join([el if isinstance(el,str) else ", ".join(el if len(el)==1 else ["("+ ", ".join(el) +")"]) for el in els])
def getPlural(contents, wordtype, foreword=""):
    if not contents: return None
    if wordtype=="Substantiv adjektivisch":
        table = re.search(r"\{\{Deutsch adjektivisch Übersicht\s*(.*?)\s*\}\}", contents, flags=re.DOTALL).group(1)
        gender = re.findall(r"\|Genus.*?=\s*(\w*)",table)[0]
        if foreword in articles.values(): gender = [x for x,y in articles.items() if y==foreword][0]
        if foreword=="eine": gender = "f"
        stamms = re.findall(r"\|Stamm.*?=\s*(\w*)",table)
        stamm = ""
        plurals = ""
        for n, x in enumerate(stamms):
            stamm += (("" if n==0 else "/") + f"{x+subadjendings[gender]}") if x not in stamms[:n] else ""
            plurals += (("" if n==0 else "/") + f"{x}") if x not in stamms[:n] else ""
        return f"{foreword} {stamm}" if (foreword in subadjarticles.values() or foreword in articles.values()) else f"{subadjarticles[gender]} {stamm}", plurals
    elif wordtype=="Substantiv":
        if re.search(r"\{\{Deutsch Toponym Übersicht\s*(.*?)\s*\}\}", contents, flags=re.DOTALL):
            return f"(das) {getWordFromContents(contents)}", None
        table = re.search(r"\{\{Deutsch (?:Substantiv|Name) Übersicht\s*(.*?)\s*\}\}", contents, flags=re.DOTALL).group(1)
        genders = re.findall(r"\|Genus.*?=\s*(\w*)",table)
        
        singulars = re.findall(r"\|Nominativ Singular.*?=\s*((?:-\w|\w)*)",table)
        singular = ""
        for n, x in enumerate(singulars):
            singular += (("" if n==0 else "/") + f"{x}") if x not in singulars[:n] else ""
        plurals = re.findall(r"\|Nominativ Plural.*?=\s*((?:-\w|\w)*)",table)
        plural = ""

        if len(genders)==1 and genders[0] not in articles:
            return plural, f"no singular" 
        else:
            for n, x in enumerate(plurals):
                plural += (("" if n==0 else "/") + f"{x}") if x not in plurals[:n] else ""
            article = "/".join(articles[x] for x in genders)
            
            return f"{article} {singular}", plural
    elif wordtype=="Adjektiv":
        table = re.search(r"\{\{Deutsch Adjektiv Übersicht\s*(.*?)\s*\}\}", contents, flags=re.DOTALL)
        if not table:
            return None
        table = table.group(1)
        komp = re.findall(r"\|Komparativ.*?=\s*(\w*)",table)
        sup = re.findall(r"\|Superlativ.*?=\s*(\w*)",table)
        if not ("".join(komp) or "".join(sup)):
            return None
        return joinPlural([komp,sup])
    elif wordtype=="Verb":
        addsichlambda = lambda word: addsich(word, foreword)
        table = re.search(r"\{\{Deutsch Verb Übersicht\s*(.*?)\s*\}\}", contents, flags=re.DOTALL).group(1)
        präsens = re.findall(r"\|Präsens_er, sie, es.*?=\s*(.*)\s*",table)
        präteritum = re.findall(r"\|Präteritum_ich.*?=\s*(.*)\s*",table)
        partizip = re.findall(r"\|Partizip II.*?=\s*(.*)\s*",table)
        hilfverb = "/".join(re.findall(r"\|Hilfsverb.*?=\s*(.*)\s*",table)).replace("sein","ist").replace("haben","hat")
        präsens, präteritum = list(map(addsichlambda,präsens)), list(map(addsichlambda,präteritum))
        return joinPlural([präsens, präteritum, addsichlambda(hilfverb+" " + joinPlural([partizip]))])
    else:
        return None

def addsich(word, foreword):
    if foreword != "sich": return word
    return re.sub(r"^([^\s]+)",r"\g<1> sich", word, 1)

def getWordFromContents(contents):
    return re.search(r"==\s*((?:\w|\w-)+)\s*.*?==",contents).group(1)

def splitMultDefs(contents, lang = "de"):
    if contents is None: return None
    langsectiontitles = {"de": "({{Sprache|Deutsch}})", "en": "German"}
    split = re.split(r"(^==[^=]*?==$)", contents, flags=re.MULTILINE)
    assert len(split)%2==1, "Wrong number of sections in the page."
    for n in range((len(split)-1)//2):
        if langsectiontitles[lang] in split[1+2*n]:
            sectiontitle = split[1+2*n]
            section = split[1+2*n]+split[1+2*n+1]
            break
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
    result = "<i>"+", ".join(m.group(1).split("|"))+":</i>"
    result = re.sub(r", t\d+=(.*?),", r"\g<1>", result).replace("_","").replace("ft=","")
    return result
def curlyjoiner(m):
    return "<i>"+"".join(m.group(1).split("|"))+"</i>"
def getMeanings(contents, word=None, hideWord=True):
    if not contents: return None
    rawdata = re.search(r"\{\{Bedeutungen\}\}\s*(.*?)(?:\n\n|\n\{\{)", contents, flags=re.DOTALL)
    if not rawdata:
        return None
    rawdata = rawdata.group(1)
    replacements = {r"\[\[[^\]]*\|(?P<link>.*?)\]\]": "",
                    r"\[\[": "", r"\]\]": "", "''(?P<quote>.*?)''": "", r"(?P<ref><ref>.*?</ref>)": "",
                    r":+\[(?P<start>.*?)\]": "", r"kPl\.": "kein Plural", r"kSt\.": "keine Steigerung",
                    r"(?P<QS>\{\{QS Bedeutungen\|.*?\}\})": ""}
    namedgroups = {"quote": r"<i>\g<quote></i>", "start": r"[\g<start>]", "ref": "", "link": r"\g<1>", "QS": ""}
    if replacements:
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
    rawdata = re.sub(r"\{\{K\|(.*?)\}\}", lambda x: kreplacer(x), rawdata)
    rawdata = re.sub(r"\{\{(.*?)\}\}", lambda x: curlyjoiner(x), rawdata)
    # if hideWord:
    #     rawdata = rawdata.replace(word,"_")
    return rawdata

def getAnmerkung(contents):
    if not contents: return None
    rawdata = re.search(r"\{\{Anmerkung[^\n]*?\}\}\s*(.*?)(?:\n\n|\n\{\{)", contents, flags=re.DOTALL)
    if not rawdata:
        return None
    rawdata = rawdata.group(1)
    replacements = {r"\[\[[^\]]*\|(?P<link>.*?)\]\]": "",
                    r"\[\[": "", r"\]\]": "", "''(?P<quote>.*?)''": "", r"(?P<ref><ref>.*?</ref>)": "",
                    r"(?P<colon>^:+)": "", r"kPl\.": "kein Plural", r"kSt\.": "keine Steigerung",
                    r"(?P<QS>\{\{QS Bedeutungen\|.*?\}\})": ""}
    namedgroups = {"quote": r"<i>\g<quote></i>", "start": r"[\g<start>]", "ref": "", "link": r"\g<1>", "QS": "", "colon": ""}
    if replacements:
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
    rawdata = re.sub(r"\{\{K\|(.*?)\}\}", lambda x: kreplacer(x), rawdata)
    rawdata = re.sub(r"\{\{(.*?)\}\}", lambda x: curlyjoiner(x), rawdata)
    return rawdata

def getExamples(contents):
    if not contents: return None
    rawdata = re.search(r"\{\{Beispiele\}\}\s*(.*?)(?:\n\n|\n\{\{)", contents, flags=re.DOTALL)
    if not rawdata:
        return None
    rawdata = rawdata.group(1)
    replacements = {r"\[\[": "", r"\]\]": "", "''(?P<quote>.*?)''": "",
                    r"(?:(?<=\n)|^):+(?P<start>\[)(?=[^\[]|$)": "", r"kPl\.": "kein Plural", r"(?P<ref><ref>.*?</ref>)": "",
                    r"(?P<beispf>\s*\{\{Beispiele fehlen.*?\}\})": "", r"(?P<beleg>\(\[http://.*?\))": "",
                    r"\{\{L\|(?P<L>.*?)\|G=.*?\}\}": ""}
    namedgroups = {"quote": r"<i>\g<quote></i>", "start": r"\g<start>", "ref": "", "beispf": "", "beleg": "", "L": "\g<L>"}
    if replacements:
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
    return rawdata

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

def getIPA2(words, whichs=None, lang="de"):
    contentsf = {"de": getIPA2contents, "en": getIPA2contentsen}
    if isinstance(words,str): words = [words]
    contents = getWiktionaryContents(words, lang=lang, getAllDefs=True)
    ipas = dict()
    for n, word in enumerate(words):
        try:
            if whichs is None:
                ipa = contentsf[lang](contents[word])
            else:
                ipa = contentsf[lang](getFromListorNone(contents[word],whichs[n]-1))
        except Exception as e:
            sys.stderr.write(f"Failed getIPA2 for word {word}, words {words}")
            raise
        ipa = ipa if ipa else "[.]"
        ipas[word] = ipa
    return ipas

def getIPA2contents(contents):
    try:
        if contents is None: return None
        if isinstance(contents,list):
            newcontents = None
            for content in contents:
                if re.search(r"\{\{IPA\}\}\s*(.*)\s*", content):
                    newcontents = content
                    break
            if newcontents is None: return None
            contents = newcontents
        word = re.search(r"==\W*?(\w+)\s*.*?==",contents)
        word=word.group(1)
        rawdata = re.search(r"\{\{IPA\}\}\s*(.*)\s*", contents).group(1)
        replacements = {r"''(?P<quote>.*?)''": "", r"\{\{Lautschrift\|(?P<laut>.*?)\}\}": "", r"(?P<ref><ref>.*?</ref>)": "",
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
    except Exception as e:
        sys.stderr.write(f"Failed getIPA2contents() for contents\n{contents}")
        raise

def getIPA2contentsen(contents):
    try:
        if contents is None: return None
        if isinstance(contents,list):
            newcontents = None
            for content in contents:
                if re.search(r"\{\{IPA\}\}\s*(.*)\s*", content):
                    newcontents = content
                    break
            if newcontents is None: return None
            contents = newcontents
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
    except Exception as e:
        sys.stderr.write(f"Failed getIPA2contents() for contents\n{contents}")
        raise

def getTranslation(contents, lang="en"):
    rawdata = re.search(r"\*\{\{"+lang+r"}\}:\s*(.*)", contents)
    if rawdata:
        rawdata = rawdata.group(1)
        rawdata = re.sub(r"\{\{Ü\|"+lang+r"\|(.*?)\}\}", r"\g<1>", rawdata)
        return rawdata
    else:
        return None

def getWiktionaryContents(words, whichWords = 1, lang="de", getAllDefs=False):
    words = [words] if isinstance(words,str) else words
    whichWords = [whichWords]*len(words) if isinstance(whichWords,int) else whichWords
    texts = {}
    for n in range(1+(len(words)-1)//50):
        words2 = words[50*n:50*(n+1)]
        data = requests.get(f"https://"+lang+f".wiktionary.org/w/api.php?action=query&format=json&prop=revisions&rvprop=content&rvslots=*&titles="+"|".join(words2))
        data = json.loads(data.text)["query"]["pages"]
        data = {data[el]["title"]: data[el]["revisions"][0]["slots"]["main"]["*"] for el in data if int(el)>=0}
        contents = {word: data.get(word) for word in words}
        for word in contents:
            try:
                multDefs = splitMultDefs(contents[word], lang=lang)
                which = whichWords[50*n+words2.index(word)]
                texts[word] = multDefs if getAllDefs else multDefs[which-1] if multDefs else None
            except Exception as e:
                sys.stderr.write(f"Failed for word {word}\nerror {e}\nwords {words}\nwords2 {words2}\n")
                raise e
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
    # print(repr(text))
    # x = re.findall(r"(\n|^)(.+)(?=\n)",text)
    # print(x)
    # x = re.sub(r"(?=(\n|^))(.+)(?=\n)",r"\g<1><div>\g<2></div>\n",text)
    return re.sub(r"(\n|^)(.+)(?=\n)",r"\g<1><div>\g<2></div>",text)

def getMainWord(german):
    word = remHTML(german) if german else german
    return re.search(r"^(?:(-?(?:\(?sich\)?|(?:\(?(?:der|die|das|ein|eine)(?:/(?:der|die|das|ein|eine))?\)?)))\s+)?((?:-\w|\w)+)",word).groups()

def getOuter(text, element, innerInstead=False, noparams=False):
    startstring = f"<{element}>" if noparams else f"<{element}[^>]*?>"
    parts = re.split(f"({startstring}|</{element}>)",text)
    startn = 0
    for part in parts:
        if re.search(f"{startstring}",part):
            break
        startn+=1
    openn = 0
    wantedparts = []
    k=0
    # print(f"startn {startn}\nparts {parts}")
    for k, part in enumerate(parts[startn:]):
        if re.search(f"{startstring}",part):
            openn+=1
        elif part==f"</{element}>":
            openn-=1
        wantedparts.append(part)
        if openn==0:
            break
    # print(f"wantedparts {wantedparts}")
    remaining = "".join(parts[startn+k+1:]) if openn==0 else None
    if innerInstead:
        return "".join(wantedparts[1:-1] if openn==0 else wantedparts[1:]) if wantedparts else None, remaining
    else:
        return "".join(wantedparts) if wantedparts else None, remaining

def getDudenExamples(examples):
    remainingex=examples
    examplelist = []
    while examples:
        examples, remainingex = getOuter(remainingex,"li",True)
        if examples is not None:
            examplelist.append(examples)
    return examplelist

def getGrammatik(text):
    grammatik = re.findall("Grammatik</dt>\s*<dd [^>]*>(.*?)</dd>",text)
    if grammatik:
        return " | ".join(grammatik)

def parsediv(text, divtext):
    parts = re.split(f"({divtext})",text)
    text = "".join(parts[1:])#+parts[2]
    if not text: return None
    section, remaining = getOuter(text, "div", True)
    section, remaining = getOuter(section, "header", True)
    if not re.search('id="Bedeutung', remaining):
        remaining = re.sub(r"<dl(?: |>)[^\n]*?Wendungen, Redensarten, Sprichwörter.*?</dl>","",remaining,flags=re.MULTILINE+re.DOTALL)
    # if not re.search("<li",remaining):
        parts = re.split(r"(<dl(?: |>)[^\n]*?Beispiele?.*?</dl>)",remaining,flags=re.MULTILINE+re.DOTALL)
        stripped = re.sub("^\s+|\s+$|<p>|</p>","",parts[0],flags=re.MULTILINE)
        exampleslist = getDudenExamples("".join(parts[1:]))
        # print(stripped)
        return [[[stripped,exampleslist]]] if stripped else None
    sections = []
    while True:
        section, remaining = getOuter(remaining,"li",True)
        if section is None: break
        if '<li class="enumeration__sub-item" id="Bedeutung' in section:
            subsection = remainingsub = section
            subsections = []
            while remainingsub:
                subsection, remainingsub = getOuter(remainingsub,"li",True)
                if subsection is not None:
                    subsections.append(subsection)
            sections.append(subsections)
        else:
            sections.append([section])
        for k, sec in enumerate(sections[-1]):
            meaning, examples = getOuter(sec,"div",True)
            grammatik = getGrammatik(examples)
            if grammatik: meaning = f"{grammatik}: {meaning}"
            examples, remainingex = getOuter(examples,"dd",True,True)
            examplelist = getDudenExamples(examples)
            sections[-1][k]=[meaning,examplelist]
    # for section in sections:
    #     print(f"\n<{repr(section)}>")
    return sections

def replacerUmlaut(match,replacements):
    return replacements[match.group(0)]
def getDudenStr(word):
    replacements = {"ü": "ue", "Ü": "Ue", "ä": "ae", "Ä": "Ae", "Ö": "Oe", "ö": "oe", "ß": "sz"}
    word = re.sub("|".join(replacements.keys()),lambda x: replacerUmlaut(x,replacements),word)
    data = requests.get(f"https://www.duden.de/rechtschreibung/{word}").text
    if "Die Seite wurde nicht gefunden" in data: return None, None
    sections = parsediv(data, '<div class="division " id="bedeutung(?:en)?">')
    if sections is None: return None, None
    meanings, examples = [], []
    for n, section in enumerate(sections):
        for k, subsection in enumerate(section):
            addletter = chr(ord('a')+k) if len(section)>1 else ""
            meaning = re.sub("\n|<a href=[^>]*>|</a>", "",subsection[0] or "")
            meanings.append(f"[{n+1}{addletter}] {meaning}")
            for example in subsection[1]:
                example = re.sub("\n|<a href=[^>]*>|</a>", "",example)
                examples.append(f"[{n+1}{addletter}] {example}")

    return "\n".join(meanings), ("\n".join(examples) or None)

# text = 'as\ndf <dl>Beispiel</dt>\n        <dd>\n          <ul class="note__list"><li>aus der Schusslinie gehen</li>\n     </dl>     </ul></dd>\n\n'
# print(repr(text))
# parts = re.split(r"(^[^\n]*?<dl(?: |>).*Beispiele?.*?</dl>)",text,flags=re.MULTILINE+re.DOTALL)
# print(parts)
lang="de"
foreword = ""
# word = "Haus"
# word = "Estland"
# word = "Betracht"
word = "abschließen"
whichWords = 2
foreword = "der"

words = ['schloss', 'ab:', 'abschließen', 'ab', 'schließt', 'hat', 'abgeschlossen']
# print(getIPA2([word],lang="de"))
print(getIPA2(words,lang="de"))
# print(getMainWord("ein Deutscher"))

# duden = getDudenStr(word)
# print(f"\n\nword:{word}")
# print(f"\n{duden}" if duden is None else f"\nmeanings\n{duden[0]}\n\nexamples\n{duden[1]}")

# texts = getWiktionaryContents(word, whichWords=whichWords, lang=lang, getAllDefs=True)
# print(texts)
# content = texts[word][0]
# examples = getExamples(content)
# print(examples)
# anm = getAnmerkung(content)
# print(anm)
# meanings = getMeanings(content)
# print(meanings)
# main = getMainWord(word)
# print(main)

# plural = getPlural(content,getWordType(content),foreword)
# print(plural)
# meanings = getMeanings(texts[word], word=word)
# print(meanings)
# newlinetodiv(meanings)
# print(repr(meanings))
# print(newlinetodiv(meanings))
# print(texts)
# print(getWordType(texts[words]))
# print(getPlural(texts[words], getWordType(texts[words])))
# print(getIPA2(words,lang=lang))