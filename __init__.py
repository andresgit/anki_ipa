# import the main window object (mw) from aqt
from aqt import mw
# import the "show info" tool from utils.py
from aqt.utils import showInfo
# import all of the Qt GUI library
from aqt.qt import *

from aqt.browser import Browser
from anki.hooks import addHook
from aqt.utils import tooltip, _tooltipLabel, _tooltipTimer, closeTooltip, askUserDialog
from aqt import *
import requests
import re
import time
import json
from bs4 import BeautifulSoup
import os
import sys
from collections import deque
##from threading import Thread

# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.



def remHTML(text):
    return BeautifulSoup(text, "html.parser").text
##    return lxml.html.fromstring(text).text_content()

def areMultiple(w):
    return w.count("[")>1

def getIPAEng(word):
    if not word.strip():
        return ""
    if not isinstance(word,str): word="|".join(word)
    f = requests.get("https://en.wiktionary.org/wiki/"+word)
    t = f.text.split('<h2><span class="mw-headline" id="')
    for x in t:
        if x.startswith("German"): break
    if '"Appendix:German pronunciation"' not in x:
        return "[.]"
    t = x.split('"Appendix:German pronunciation">key</a>)</sup>:&#32;',1)[1].split("</ul>")[0]
    d = ""
    for x in t.split('"Appendix:German pronunciation">key</a>)</sup>:&#32;'):
        d += re.sub("<.*?>","",x.split("</li>")[0])+", "
    d = d.strip(" ,")
##    d = t.split("</li>")[0]
##    d = re.sub("<.*?>","",d)
##    if '"Appendix:German pronunciation">key</a>)</sup>:&#32;' in t:
##        d = "(CHECK EXTRA IPAS):"+d
##    t = re.search("""<dd><a href="/wiki/Hilfe:IPA" title="Hilfe:IPA">IPA</a>: ?(.*?)</dd>""",t)
##    if not t:
##        return "[.]"
    return d

##print(getIPAEng("aber"))

def getIPA(word):
    if not word.strip():
        return ""
    f = requests.get("https://de.wiktionary.org/wiki/"+word)
    t = f.text.split("/wiki/Wiktionary:")
    for x in t:
        if x.startswith("Deutsch"): break
    t = x.split("Hörbeispiele",1)[0]
    t = re.search("""<dd><a href="/wiki/Hilfe:IPA" title="Hilfe:IPA">IPA</a>: ?(.*?)</dd>""",t,re.S)
    if not t:
        return "[.]"
##    print(t)
##    print()
##    print(t.group(1))
##    print()
    t = re.sub("<.*?>","",t.group(1))
##    print(t)
    if word in ["der","ist","sich","ich","du","er","ihr"]:
        t = t.split("]")[0]+"]"
##    if "], Präteritum: [" in t:
##        t = t.split("], Präteritum: [")[0]
    return t
##    m = re.findall(
##        """(?:(?:<i>)|(?:<span)(.*?):</i> )?\[<span class="ipa" style="padding: 0 1px; text-decoration: none;">(.*?)</span>\]""",
##        t)
##    if word == "der":
##        m = [m[0]]
##    m = [((m[k][0]+": ") if m[k][0] else "") + "["+m[k][1]+"]" for k in range(len(m))]

##print(getIPA(""))

def allIPA(word, checkEnglishIfNone = False):
    global variants
    res = []
    for x in word.split():
        y = getIPA(x)
        if y == "[.]" and checkEnglishIfNone:
            y = getIPAEng(x)
        if areMultiple(y):
            variants = True
            y = "("+y+")"
        res.append(y)
    return " ".join(res)

def pluralIPA(w, checkEnglishIfNone = False):
    ipas = []
    w = re.sub(r"(?!^)<div>","\n<div>",w)
##    w = remHTML(w)
##    w=w.replace("&nbsp;", " ").replace("&#32;"," ").replace("&#160;"," ")
##    w = re.sub("<.*?>","",w)
    matchstring = r"(; *|, *|/ *|\n|<.+?>|\)|\(| +)"
    for x in re.split(matchstring,w):
        if len(re.findall(matchstring,x))>0:
            ipas.append(x)
        else:
            ipas.append(allIPA(x, checkEnglishIfNone))
    return "".join(ipas)

class stayMenu(QMenu):
    def mouseReleaseEvent(self, e):
        a = self.activeAction()
        if a and a.isEnabled() and a.isCheckable():
            a.setEnabled(False)
            QMenu.mouseReleaseEvent(self, e)
            a.setEnabled(True)
            a.trigger()
        else:
            QMenu.mouseReleaseEvent(self, e)

def onSetupMenus(self):
    """Setup menu entries and hotkeys"""
    global bw
    bw = self
    self.menuView = stayMenu(_("&IPA"))
    self.menuGender = stayMenu(_("&Gender"))
    self.menuMisc = stayMenu(_("&Misc"))
    self.menuBar().insertMenu(
        self.mw.form.menuTools.menuAction(), self.menuView)
    self.menuBar().insertMenu(
        self.mw.form.menuTools.menuAction(), self.menuGender)
    self.menuBar().insertMenu(
        self.mw.form.menuTools.menuAction(), self.menuMisc)
    menu = self.menuView
    self.a1 = menu.addAction("Get")
    self.a1.triggered.connect(lambda: testFunction())
    self.a2 = menu.addAction("Overwrite")
    self.a2.setCheckable(True)
    self.a2.setChecked(False)
    self.a3 = menu.addAction("Overwrite if there are variants")
    self.a3.setCheckable(True)
    self.a3.setChecked(False)
    self.a4 = menu.addAction("Check English Wiki if no German")
    self.a4.setCheckable(True)
    self.a4.setChecked(True)
    self.a5 = menu.addAction("Clear IPA")
    self.a5.triggered.connect(lambda: clearIPA("IPA"))
    self.a6 = menu.addAction("Clear IPA Plural")
    self.a6.triggered.connect(lambda: clearIPA("IPA Plural"))

    menu = self.menuGender
    self.g1 = menu.addAction("Add gender colors")
    self.g1.triggered.connect(lambda: colorGender(remove=False))
    self.g2 = menu.addAction("Remove gender colors")
    self.g2.triggered.connect(lambda: colorGender(remove=True))
    
    menu = self.menuMisc
    self.m1 = menu.addAction("nbsp to space")
    self.m1.triggered.connect(lambda: nbsp_to_space())
    self.m2 = menu.addAction("Get from Wiktionary")
    self.m2.triggered.connect(lambda: getWiktionary())
    self.m3 = menu.addAction("Overwrite from Wiktionary")
    self.m3.setCheckable(True)
    self.m3.setChecked(False)
    self.m4 = menu.addAction("Add from file")
    self.m4.triggered.connect(lambda: addFromFile())
##    a2.triggered.connect(lambda: testFunction(overwrite = True))
##    a3.triggered.connect(lambda: testFunction(overwriteIfVar = True))
##    a4.triggered.connect(lambda: testFunction(checkEnglishIfNone = True))
##    a.triggered.connect(Thread(target=testFunction, args=(mw,aqt.dialogs._dialogs['Browser'][1])).start)

def addAllIpas(notes):
    notes[0]["IPA"]="4"
    wordstoget = set()
    jobs = deque()
    fields = {"German": "IPA", "Plural and inflected forms": "IPA Plural"}
    matchstring = r"(; *|, *|/ *|\n *|<.+?>|\)|\(| +|\. *)"
    for m, note in enumerate(notes):
        setToolText(f"{'IPA Started with:':<20} {m+1}/{len(notes)}")
        # print(f"m of note: {m}")
        jobs.append([note,1,[]])
        for field in fields:
            entry = note[field]
            # print(f"for field <{field}> entry len {len(entry.split())} <{entry}>")
            breakdowns = jobs[-1][2]
            breakdowns.append([])
            # print(f"breakdown <{re.split(matchstring,entry)}>")
            for x in re.split(matchstring,entry,flags=re.MULTILINE):
                if x=="" or re.search(matchstring,x,flags=re.MULTILINE):
                    breakdowns[-1].append([0,x])
                    # print(f"breakdown with numbers <{jobs[-1][1][-1]}>")
                else:
                    breakdowns[-1].append([1,x])
                    # print(f"breakdown with numbers <{jobs[-1][1][-1]}>")
                    wordstoget.add(x)
                    if len(wordstoget) == 50:
                        # print(f"\nFilled 50 words")
                        setToolText(f"{'IPA Downloading':<20} {m+1}/{len(notes)}")
                        ipas = getIPA2(list(wordstoget))
                        setToolText(f"{'IPA Processing':<20} {m+1}/{len(notes)}")
                        processIPAs(jobs, ipas, fields)
                        wordstoget = set()
        jobs[-1][1]=0
    if jobs:
        setToolText(f"{'IPA Downloading':<20} {m+1}/{len(notes)}")
        ipas = getIPA2(list(wordstoget))
        # print(f"\nprocessing the end\nlen wordstoget: {len(wordstoget)}\nipas: {ipas}\nwordstoget: {wordstoget}")
        setToolText(f"{'IPA Processing':<20} {m+1}/{len(notes)}")
        processIPAs(jobs, ipas, fields)
        
def processIPAs(jobs, ipas, fields, checkEnglish=True):
    for k, job in enumerate(jobs):
        # print(f"job: {job}")
        for field, breakdown in zip(fields.values(), job[2]):
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
            # job[0]["IPA"]="1"
            job[0][field]="".join(list(zip(*breakdown))[1])
            # job[0]["IPA Plural"]="2"
            # showInfo(f"job[0]: {job[0]}\ngerman: {job[0]['German']}\nfield: {field}\nvalue: {''.join(list(zip(*breakdown))[1])}")
        if job[1]==0:
            job[0].flush()
            jobs[k]=None
    while jobs and jobs[0] is None:
        jobs.popleft()



def addFromFile():
    setToolText("Starting to add files from the file")
    file = open(os.path.expanduser("~/Desktop/ankiaddwords.txt"))
    contents = file.read()
    file.close()
    addwords = []
    missedwords = []
    notes = []
    for line in contents.splitlines():
        word = re.search(r"^\w+", line)
        number = re.search(r"\d+", line)
        hint = re.search(r"\(.*\)", line)
        addwords.append([word.group(0),int(number.group(0)) if number else 1,hint.group(0) if hint else None])
    for n in range(1+(len(addwords)-1)//50):
        setToolText(f"Downloading {n*50+1}/{len(addwords)}")
        words, whichs, hints = zip(*addwords[n*50:(n+1)*50])
        contents = getWiktionaryContents(words, whichs)
        for k, word in enumerate(words):
            ind = n*50+k
            setToolText(f"Working on word number {ind+1}/{len(addwords)}")
            content = contents[word]
            if content is None:
                missedwords.append(word)
                continue
            wordType = getWordType(content)
            plurals = getPlural(content, wordType)
            meanings = getMeanings(content)
            examples = getExamples(content)
            newgerman = f"{plurals[0]} {plurals[1]}" if wordType=="Substantiv" else word
            plural = f"die {plurals[2]}" if wordType=="Substantiv" else plurals
            newgerman = coloredName(newgerman,word)
            plural = coloredName(plural,word)
            search = f"deck:current German:'{coloredName(newgerman,newgerman)}'"
            ids = mw.col.findCards(search)
            if not ids:
                note = mw.col.newNote()
                for field, value in (("German", newgerman),
                                ("Plural and inflected forms", plural), ("English", newlinetodiv(meanings)), ("Part of Speech", wordType),
                                ("Sample sentence", newlinetodiv(examples))):
                    note[field] = value
                mw.col.addNote(note)
                notes.append(note)
    setToolText(f"Starting to work on IPA")
    addAllIpas(notes)
    # testFunction(notes, endInfo=False)
    # setToolText(f"Starting to work on gender colors")
    # colorGender(notes, endInfo=False)
    # setToolText(f"Finished gender colors")
    closeTooltip()
    if len(missedwords): showInfo(f"Missed words: {', '.join(missedwords)}", parent=bw)
    else: showInfo(f"Added from file {len(addwords)} cards", parent=bw)
    mw.reset()
    # showInfo(f"german: {german}\nnewgerman: {newgerman}\nsearch: {search}\nids: {ids}")

def getWiktionary(notes=None, overwrite=False):
    # bw = aqt.dialogs._dialogs['Browser'][1]
    overwrite = bw.m3.isChecked()
    notes = bw.selectedNotes()
    for k, n in enumerate(notes):
        obj = mw.col.getNote(n)
        w = obj["German"]
        w = remHTML(w)
        word = re.search("(?:der|die|das)?\s*(\w+)",w).group(1)
        contents = getWiktionaryContents(word,1)
        wordType = getWordType(contents)
        plurals = getPlural(contents, wordType)
        meanings = getMeanings(contents)
        examples = getExamples(contents)
        newgerman = f"{plurals[0]} {plurals[1]}" if wordType=="Substantiv" else w
        plural = f"die {plurals[2]}" if wordType=="Substantiv" else plurals

        # showInfo(f"<b>word:</b> {word}\n<b>wordType:</b> {wordType}\n<b>plurals:</b> {plurals}\n<b>plural:</b> {plural}\n<b>meanings:</b> {meanings}\n<b>examples:</b> {examples}")
        for field, value in (("German" if newgerman!=w else "", changeGerman),
                            ("Plural and inflected forms", plural), ("English", newlinetodiv(meanings)), ("Part of Speech", wordType),
                            ("Sample sentence", newlinetodiv(examples))):
            if field and (overwrite or obj[field]==""):
                obj[field] = value
        obj.flush()
    showInfo("Inserted data from Wiktionary for {} cards.".format(len(notes)), parent=bw)
    mw.reset()

def getWiktionaryContents(words, whichWords = 1, lang="de"):
    words = [words] if isinstance(words,str) else words
    whichWords = [whichWords]*len(words) if isinstance(whichWords,int) else whichWords
    texts = {}
    for n in range(1+(len(words)-1)//50):
        words2 = words[50*n:50*(n+1)]
        data = requests.get(f"https://"+lang+f".wiktionary.org/w/api.php?action=query&format=json&prop=revisions&rvprop=content&rvslots=*&titles="+"|".join(words2))
        data = json.loads(data.text)["query"]["pages"]
        # for el in data:
        #     print(f"el {el}\ntitle <{data[el]['title']}>\nkeys {data[el].keys()}")
        contents = {data[el]["title"]: None if int(el)<0 else data[el]["revisions"][0]["slots"]["main"]["*"] for el in data}
        for word in contents:
            multDefs = splitMultDefs(contents[word], lang=lang)
            texts[word] = multDefs[whichWords[50*n+words2.index(word)]-1] if multDefs else None
    return texts

def newlinetodiv(text):
    return re.sub("\n(.*)","\n<div>\g<1></div>",text)

def getWordType(contents):
    x= re.search(r"=== \{\{Wortart\|(.*?)\|Deutsch\}\}",contents)
    return x.group(1)

articles = {"m": "der", "f": "die", "n": "das"}
def joinPlural(els):
    return ", ".join([el if isinstance(el,str) else ", ".join(el if len(el)==1 else ["("+ ", ".join(el) +")"]) for el in els])
def getPlural(contents, wordtype):
    if wordtype=="Substantiv":
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
    data = []
    for n in range((len(split)-1)//2):
        if langsectiontitles[lang] in split[1+2*n]:
            data.append(split[1+2*n]+split[1+2*n+1])
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
    result = re.sub(r", t\d+=(.*?),", "\g<1>", result).replace("_","").replace("ft=","")
    return result
def curlyjoiner(m):
    return "<i>"+"".join(m.group(1).split("|"))+"</i>"
def getMeanings(contents):
    rawdata = re.search(r"\{\{Bedeutungen\}\}\s*(.*?)(?:\n\n|\n\{\{)", contents, flags=re.DOTALL).group(1)
    replacements = {r"\[\[": "", r"\]\]": "", "''(?P<quote>.*?)''": "",
                    r":+\[(?P<start>\d)\]": "", r"kPl\.": "kein Plural", r"kSt\.": "keine Steigerung"}
    namedgroups = {"quote": r"<i>\g<quote></i>", "start": r"[\g<start>]"}
    rawdata = re.sub(r"\{\{K\|(.*?)\}\}", lambda x: kreplacer(x), rawdata)
    rawdata = re.sub(r"\{\{(.*?)\}\}", lambda x: curlyjoiner(x), rawdata)
    if replacements:
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
    return rawdata

def getExamples(contents):
    rawdata = re.search(r"\{\{Beispiele\}\}\s*(.*?)(?:\n\n|\n\{\{)", contents, flags=re.DOTALL).group(1)
    replacements = {r"\[\[": "", r"\]\]": "", "''(?P<quote>.*?)''": "",
                    r":+\[(?P<start>\d)\]": "", r"kPl\.": "kein Plural", r"(?P<ref><ref>.*?</ref>)": "",
                    r"(?P<beispf>\s*\{\{Beispiele fehlen.*?\}\})": ""}
    namedgroups = {"quote": r"<i>\g<quote></i>", "start": r"[\g<start>]", "ref": "", "beispf": ""}
    if replacements:
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
    return rawdata

def getIPA2(words, lang="de"):
    contentsf = {"de": getIPA2contents, "en": getIPA2contentsen}
    if isinstance(words,str): words = [words]
    contents = getWiktionaryContents(words, lang=lang)
    return {word: "[.]" if contents[word] is None else contentsf[lang](contents[word]) for word in words}

def getIPA2contents(contents):
    word = re.search(r"==\s*(\w+)\s*.*?==",contents)
    word=word.group(1)
    rawdata = re.search(r"\{\{IPA\}\}\s*(.*)\s*", contents).group(1)
    replacements = {"''(?P<quote>.*?)''": "", "\{\{Lautschrift\|(?P<laut>.*?)\}\}": "", r"(?P<ref><ref>.*?</ref>)": "",
        r"\[\[": "", r"\]\]": "",}
    namedgroups = {"quote": r"<i>\g<quote></i>", "ref": "", "laut": "[\g<laut>]"}
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
        rawdata = re.sub(r"\{\{Ü\|"+lang+r"\|(.*?)\}\}", "\g<1>", rawdata)
        return rawdata
    else:
        return None



def nbsp_to_space():
    # bw = aqt.dialogs._dialogs['Browser'][1]
    notes = bw.selectedNotes()
    edited_N = 0
    for k, n in enumerate(notes):
        obj = mw.col.getNote(n)
        for field in obj.keys():
            if "&nbsp;" in obj[field]: edited_N +=1
            obj[field] = obj[field].replace("&nbsp;", " ")
            obj.flush()
    mw.reset()
    showInfo("Worked on {} cards, replaced &nbsp; in {} cards.".format(len(notes),edited_N))

def coloredName(word, german):
    cols = {"die": "#ff0000", "der": "#0000ff", "das": "#00aa00"}
    match = re.match("\W*?(\w+)", german)
    gend = match.group(1) if match else None
    return '<font color="{}">{}</font>'.format(cols[gend],word) if gend in cols else word
def colorGender(notes=None, remove = False, endInfo = True):
    # bw = aqt.dialogs._dialogs['Browser'][1]
    getfromid = False
    if notes is None:
        notes = bw.selectedNotes()
        getfromid = True
    for k, n in enumerate(notes):
        obj = mw.col.getNote(n) if getfromid else n
        w = obj["German"]
        w = remHTML(w)
        cols = {"die": "#ff0000", "der": "#0000ff", "das": "#00aa00"}
        match = re.match("\W*?(\w+)", w)
        gend = match.group(1) if match else None

        for field in "German", "Plural and inflected forms", "IPA", "IPA Plural":
            w = obj[field]
            w = remHTML(w)
            if remove:
                obj[field] = w
                obj.flush()
            elif match and gend in cols and obj[field]:
                obj[field] = '<font color="{}">{}</font>'.format(cols[gend],w)
                obj.flush()
    mw.reset()
    if endInfo: showInfo("Worked on colors for {} cards.".format(len(notes)))
        

def clearIPA(whichOne=""):
    diag = askUserDialog("Do you want to delete "+whichOne+"?",["Yes","No"])
    ret = diag.run()
    if ret =="Yes":

        # bw = aqt.dialogs._dialogs['Browser'][1]
        notes = bw.selectedNotes()

        for k, n in enumerate(notes):
            obj = mw.col.getNote(n)
            if whichOne not in obj.keys():
                showInfo("Key {} not existant.".format(whichOne))
                return
            else:
                obj[whichOne]=""
                obj.flush()
        mw.reset()
        showInfo("Cleared {} from {} cards.".format(whichOne,len(notes)))
    return
##    if whichOne=="IPA":
##
##    elif whichOne=="IPA Plural":

def displayData(note):
##    val1 = mw.col.getNote(note)["German"]
    val1 = mw.col.getNote(note)["Plural and inflected forms"]
    val2 = re.sub("<.*?>","",val1)
##    val2 = re.sub("<|>","",val1)
    w1 = ", ".join("\"{}\"({})".format(x,ord(x)) for x in val1)
    w2 = ", ".join("\"{}\"({})".format(x,ord(x)) for x in val2)
    
    showInfo("Type: {}\nOrig: \"{}\", detailed: {}\nEdited: \"{}\", detailed: {}".format(type(val1),val1,w1,val2,w2))
    return

def setToolText(text, period=60*1000): #closeTooltip() to close it
    if not aqt.utils._tooltipTimer:
        tooltip("text", period=period, parent=bw)
        aqt.utils._tooltipLabel.setWindowFlags(Qt.SplashScreen)
        aqt.utils._tooltipLabel.show()
        aqt.utils._tooltipLabel.setText("<table cellpadding=10>\n<tr>\n<td>{}</td>\n</tr>\n</table>".format("Starting to work on IPAs."))
        aqt.utils._tooltipLabel.adjustSize()
        qApp.processEvents()
    aqt.utils._tooltipTimer.setInterval(period)
    aqt.utils._tooltipLabel.setText("<table cellpadding=10>\n<tr>\n<td>{}</td>\n</tr>\n</table>".format(text))
    aqt.utils._tooltipLabel.adjustSize()
    qApp.processEvents()

def testFunction(notes = None, endInfo=True):
    global variants
    # get the number of cards in the current collection, which is stored in
    # the main window
    cardCount = mw.col.cardCount()
    # bw = aqt.dialogs._dialogs['Browser'][1]
    getfromid = False
    if notes is None:
        notes = bw.selectedNotes()
        getfromid = True
    Nsize = len(notes)
    setToolText("Starting to work on IPAs.")

    overwrite = bw.a2.isChecked()
    overwriteIfVar = bw.a3.isChecked()
    checkEnglishIfNone = bw.a4.isChecked()
##    showInfo("{}, {}, {}".format(overwrite, overwriteIfVar, checkEnglishIfNone))
##    displayData(notes[0])
##    return
    ipas = []
    changedN1, changedN2 = 0,0
    for k, n in enumerate(notes):
        obj = mw.col.getNote(n) if getfromid else n
        ind1 = obj.keys().index("German")
        ind2 = obj.keys().index("Plural and inflected forms")
        ind3 = obj.keys().index("IPA")
        ind4 = obj.keys().index("IPA Plural")
        
        val1 = obj.values()[ind1]
        val2 = obj.values()[ind2]
        val3 = obj.values()[ind3]
        val4 = obj.values()[ind4]
        variants = False
        res1 = pluralIPA(val1, checkEnglishIfNone = checkEnglishIfNone)
        variants, variants1 = False, variants
        if remHTML(val2) in ["no plural", "no singular"]:
            res2=""
        else:
            res2 = pluralIPA(val2, checkEnglishIfNone = checkEnglishIfNone)
        variants, variants2 = False, variants
        changed = False
##        ipas.append("Germ: {}\nPron: {}\nPlural: {}\nPron: {}".format(val1,res1,val2,res2))
        if checkEnglishIfNone and val3 == "[.]" and val3!=res1 or not overwrite and val3=="" and res1!=""\
           or overwrite or\
        overwriteIfVar and (variants1 or val3.count("] or ")>=1):
            changed = True
            changedN1 += 1
            obj["IPA"] = res1
##            ipas.append("Here1 {}".format(obj["IPA"]))
        if checkEnglishIfNone and "[.]" in val4 and val4!=res2 or not overwrite and val4=="" and res2!=""\
           or overwrite or\
        overwriteIfVar and (variants2 or val4.count("] or ")>=1):
            changed = True
            changedN2 += 1
            obj["IPA Plural"] = res2
##            ipas.append("Here2 {}".format(obj["IPA Plural"]))
        if changed:
            obj.flush()
##            ipas.append("Here3")
        # try: _tooltipLabel.delete()
        # except: pass
##        a = " ".join(str(ord(x)) for x in val1)
##        print(a)
        newtext = "<b>Updated</b> {}/{} notes, changed {}, {}.".format(k+1,len(notes),changedN1,changedN2)
        # qApp.processEvents()
        # if not aqt.utils._tooltipLabel:
        #     tooltip("Starting to work on IPAs.", period=20*1000, parent=bw)
        # else:
        # if not aqt.utils._tooltipTimer:
        #     maketooltip()
        # aqt.utils._tooltipTimer.setInterval(period)
        # aqt.utils._tooltipLabel.setText("<table cellpadding=10>\n<tr>\n<td>{}</td>\n</tr>\n</table>".format(newtext))
        # aqt.utils._tooltipLabel.adjustSize()
        setToolText(newtext)
        # qApp.processEvents()
        # if 0 < k < Nsize-1 and k%100 == 0:
        #     mw.reset()
        #     starttime = time.time()
        #     while time.time() -starttime < 5:
        #         qApp.processEvents()
##        bw.repaint()
##        time.sleep(1)
##        showInfo(ipas[-1])
    if len(notes) > 0:
        mw.reset()
        if endInfo: showInfo("Done {} items".format(len(notes)), parent=bw)
        closeTooltip()
##    c = aqt.dialogs._dialogs['Browser'][1].card
##    if c is not None:
##        n = c.note()
##        germ = n.values()[0]
##        pron = allIPA(germ)
##        showInfo("Germ: {}\nPron: {}".format(germ,pron))
##        showInfo("keys: {} \n\n values: {} \n\nitems: {}".format(n.keys(),n.values(),n.items()))
##        showInfo("q: {} \n\n a: {}".format(c.a(), c.q()))

### create a new menu item, "test"
##action = QAction("test", Browser)
### set it to call testFunction when it's clicked
##action.triggered.connect(testFunction)
### and add it to the tools menu
##Browser.form.menuCards.addAction(action)

addHook("browser.setupMenus", onSetupMenus)

##print(getIPA("aber"))
