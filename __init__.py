from aqt import mw
from aqt.utils import showInfo
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

def tooltip2(text, period=1000, parent=None):
    if parent is None: parent=bw
    tooltip(text, period=period, parent=parent)

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
    return d

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
    t = re.sub("<.*?>","",t.group(1))
    if word in ["der","ist","sich","ich","du","er","ihr"]:
        t = t.split("]")[0]+"]"
    return t

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
    self.menuWiktionary = stayMenu(_("&Wiktionary"))
    self.menuDuden = stayMenu(_("&Duden"))
    self.menuMisc = stayMenu(_("&Misc"))
    self.menuBar().insertMenu(
        self.mw.form.menuTools.menuAction(), self.menuView)
    self.menuBar().insertMenu(
        self.mw.form.menuTools.menuAction(), self.menuGender)
    self.menuBar().insertMenu(
        self.mw.form.menuTools.menuAction(), self.menuWiktionary)
    self.menuBar().insertMenu(
        self.mw.form.menuTools.menuAction(), self.menuDuden)
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
    
    menu = self.menuWiktionary
    self.m2 = menu.addAction("Get from Wiktionary")
    self.m2.triggered.connect(lambda: getWiktionary())
    self.m3 = menu.addAction("Overwrite from Wiktionary")
    self.m3.setCheckable(True)
    self.m3.setChecked(False)
    self.m6 = menu.addAction("Overwrite German from Wiktionary")
    self.m6.setCheckable(True)
    self.m6.setChecked(False)
    self.m4 = menu.addAction("Add from file")
    self.m4.triggered.connect(lambda: addFromFile())
    self.m7 = menu.addAction("Overwrite definitions if they exist")
    self.m7.setCheckable(True)
    self.m7.setChecked(False)
    self.m8 = menu.addAction("Overwrite examples if they exist")
    self.m8.setCheckable(True)
    self.m8.setChecked(False)
    self.m9 = menu.addAction("Overwrite plurals if they exist")
    self.m9.setCheckable(True)
    self.m9.setChecked(False)

    menu = self.menuDuden
    self.m10 = menu.addAction("Overwrite definitions if they exist")
    self.m10.setCheckable(True)
    self.m10.setChecked(False)
    self.m11 = menu.addAction("Overwrite examples if they exist")
    self.m11.setCheckable(True)
    self.m11.setChecked(False)
    self.m12 = menu.addAction("Get from Duden")
    self.m12.triggered.connect(lambda: getDuden())

    menu = self.menuMisc
    self.m1 = menu.addAction("nbsp to space")
    self.m1.triggered.connect(lambda: nbsp_to_space())
    self.m5 = menu.addAction("To German Part of Speech")
    self.m5.triggered.connect(lambda: partOfSpeech())
    self.m5 = menu.addAction("Make adjektivisch Part of Speech")
    self.m5.triggered.connect(lambda: adjektivischPartOfSpeech())
    self.m13 = menu.addAction("Remove newline from def and examples")
    self.m13.triggered.connect(lambda: remNewLine())

def getDuden():
    noteidsall = bw.selectedNotes()
    digits = len(str(len(noteidsall)))
    missedwords = []
    for n, noteid in enumerate(noteidsall):
        setToolText(f"From Duden note nr: {n+1:>{digits}}/{len(noteidsall)}")
        note = mw.col.getNote(noteid)
        word = remHTML(note["German"])
        try:
            foreword, mainword = getMainWord(word)
            meanings, examples = getDudenStr(mainword)
            tag = "nodudendef"
            if not (meanings or examples):
                missedwords.append(word)
                if tag not in note.tags:
                    note.tags.append(tag)
                    note.flush()
                continue
            if tag in note.tags:
                note.tags.remove(tag)
            # showInfo(f"mainword {mainword}\nmeanings\n{meanings}\n\nexamples\n{examples}")
            for field, value, extraCheck in (("Definition", newlinetobr(meanings),bw.m10.isChecked()),
                                            ("Sample sentence", newlinetobr(examples), bw.m11.isChecked())):
                if value and (not note[field] or extraCheck):
                    note[field] = value
                    note.flush()
        except Exception as e:
            sys.stderr.write(f"Failed for word {word}\nerror {e}")
            raise e
    closeTooltip()
    if len(missedwords): showInfo(f"Missed words: {', '.join(missedwords)}", parent=bw)
    else: showInfo(f"Worked on {len(noteidsall)} cards")
    mw.reset()

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
    grammatik = re.findall(r"Grammatik</dt>\s*<dd [^>]*>(.*?)</dd>",text)
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
        stripped = re.sub(r"^\s+|\s+$|<p>|</p>","",parts[0],flags=re.MULTILINE)
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
    sections = parsediv(data, '<div class="division "  id="bedeutung(?:en)?">')
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

def adjektivischPartOfSpeech():
    noteidsall = bw.selectedNotes()
    digits = len(str(len(noteidsall)))
    for n in range(1+(len(noteidsall)-1)//50):
        setToolText(f"{'Downloading':<25} {n*50+1:>{digits}}/{len(noteidsall)}")
        noteids = noteidsall[n*50:(n+1)*50]
        notes, words, hints = [], [], []
        for k, noteid in enumerate(noteids):
            note = mw.col.getNote(noteid)
            notes.append(note)
            w = note["German"]
            w = remHTML(w)
            hint = note["Wiktionary nr"]
            word = re.search(r"(?:der|die|das)\s+(\w+)|(\w+)",w)
            word = word.group(1) or word.group(2)
            words.append(word)
            hints.append(int(hint) if hint else 1)
        contents = getWiktionaryContents(words,hints)
        for k, (note,word) in enumerate(zip(notes,words)):
            ind = 50*n+k
            setToolText(f"{'Working on word number':<25} {ind+1:>{digits}}/{len(noteidsall)}")
            content = contents[word]
            if content is None: continue
            wordType = getWordType(content)
            if wordType == "Substantiv adjektivisch":
                note["Part of Speech"] = wordType
                note.flush()
    mw.reset()

def partOfSpeech():
    replacements={"noun": "Substantiv", "verb": "Verb", "adj": "Adjektiv", "adv": "Adverb", "prep": "Präposition", "num": "Numerale"}
    notes = bw.selectedNotes()
    for k, noteid in enumerate(notes):
        note = mw.col.getNote(noteid)
        field = "Part of Speech"
        if note[field] in replacements:
            note[field] = replacements[note[field]]
            note.flush()
    mw.reset()

def addAllIpas(notes, overwrite=False):
    wordstoget = set()
    jobs = deque()
    fields = {"German": "IPA", "Plural and inflected forms": "IPA Plural"}
    matchstring = r"(; *|, *|/ *|\n *|<.+?>|\)|\(| +|\. *)"
    for m, note in enumerate(notes):
        setToolText(f"{'IPA Started with:':<20} {m+1}/{len(notes)}")
        # print(f"m of note: {m}")
        jobs.append([note,1,[]])
        for field in fields:
            breakdowns = jobs[-1][2]
            breakdowns.append([])
            entry = note[field]
            if note[fields[field]] and (not overwrite):
                # showInfo(f"here1 entry {entry}")
                continue
            if re.match("^(<font.*>)?(?:no plural|no singular)(</font>)?$",entry):
                entry = ""
            # print(f"for field <{field}> entry len {len(entry.split())} <{entry}>")
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
                        processIPAs(jobs, ipas, fields, overwrite=overwrite)
                        wordstoget = set()
        jobs[-1][1]=0
    if jobs:
        setToolText(f"{'IPA Downloading':<20} {m+1}/{len(notes)}")
        ipas = getIPA2(list(wordstoget))
        # print(f"\nprocessing the end\nlen wordstoget: {len(wordstoget)}\nipas: {ipas}\nwordstoget: {wordstoget}")
        setToolText(f"{'IPA Processing':<20} {m+1}/{len(notes)}")
        processIPAs(jobs, ipas, fields, overwrite=overwrite)
        
def processIPAs(jobs, ipas, fields, checkEnglish=True, overwrite=False):
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
            # print(f"breakdown {breakdown}\nconnected {list(zip(*breakdown))}\nstring {''.join(list(zip(*breakdown))[1])}")
            # job[0]["IPA"]="1"
            if job[1]==0 and (not job[0][field] or overwrite) and breakdown:
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
    fileContents = file.read()
    file.close()
    addwords, forewords, mainwords = [], [], []
    missedwords = []
    notes = []
    setToolText(f"Reading in the file.")
    for line in fileContents.splitlines():
        word = re.search(r"^[^\d()]*", line).group(0)
        number = re.search(r"\d+", line)
        hint = re.search(r"\(.*\)", line)
        foreword, mainword = getMainWord(word.strip())
        addwords.append([word,
                        int(number.group(0)) if number else 1,
                        hint.group(0) if hint else None])
        forewords.append(foreword)
        mainwords.append(mainword)
    for n in range(1+(len(addwords)-1)//50):
        setToolText(f"{'Downloading':<25} {n*50+1}/{len(addwords)}")
        words, whichs, hints = zip(*addwords[n*50:(n+1)*50])
        mainwords2 = mainwords[n*50:(n+1)*50]
        forewords2 = forewords[n*50:(n+1)*50]
        contents = getWiktionaryContents(mainwords2, whichs)
        for k, (word, hint, mainword, foreword) in \
            enumerate(zip(words,hints,mainwords2,forewords2)):
            ind = n*50+k
            setToolText(f"Working on word number {ind+1}/{len(addwords)}")
            content = contents[mainword]
            
            wordType = getWordType(content)
            plurals = getPlural(content, wordType)
            meanings = getMeanings(content, word=mainword) + (f" {hint}" if hint else "")
            examples = getExamples(content)
            english = getTranslation(content, lang="en")
            estonian = getTranslation(content, lang="et")
            newgerman = plurals[0] if wordType=="Substantiv" else word
            plural = ("no plural" if not plurals[1] else f"die {plurals[1]}") if wordType=="Substantiv" else plurals
            newgermanc = coloredName(newgerman,word)
            pluralc = coloredName(plural,word)
            search = f"deck:current German:'{coloredName(newgerman,newgerman)}'"
            ids = mw.col.findCards(search)
            if not ids:
                note = mw.col.newNote()
                if content is None: addTag(note,"nowikidef")
                if meanings is None:
                    missedwords.append(word)
                    addTag(note,"nowikimeaning")
                for field, value in (("German", newgermanc),
                                ("Plural and inflected forms", pluralc), 
                                ("Definition", newlinetobr(meanings)), 
                                ("Part of Speech", wordType),
                                ("Sample sentence", newlinetobr(examples)), 
                                ("English", english), ("Estonian", estonian)):
                    if value:
                        note[field] = value
                mw.col.addNote(note)
                notes.append(note)
    setToolText(f"Starting to work on IPA")
    addAllIpas(notes)
    closeTooltip()
    if len(missedwords): showInfo(f"Missed words: {', '.join(missedwords)}", parent=bw)
    else: showInfo(f"Added from file {len(addwords)} cards", parent=bw)
    mw.reset()
    # showInfo(f"german: {german}\nnewgerman: {newgerman}\nsearch: {search}\nids: {ids}")

def addTag(note,tag, flush=False):
    if tag not in note.tags:
        note.tags.append(tag)
        if flush: note.flush()
def remTag(note,tag, flush=False):
    removed = False
    while tag in note.tags:
        removed = True
        note.tags.remove(tag)
    if flush and removed: note.flush()
def getWiktionary(notes=None, overwrite=False):
    overwrite = bw.m3.isChecked()
    noteidsall = bw.selectedNotes()
    notesall, missedwords = [], []
    digits = len(str(len(noteidsall)))
    for n in range(1+(len(noteidsall)-1)//50):
        setToolText(f"{'Downloading':<25} {n*50+1:>{digits}}/{len(noteidsall)}")
        noteids = noteidsall[n*50:(n+1)*50]
        notes, words, forewords, hints = [], [], [], []
        for k, noteid in enumerate(noteids):
            try:
                note = mw.col.getNote(noteid)
                notes.append(note)
                w = note["German"]
                # w = remHTML(w)
                # word = re.search(r"(?:der|die|das)\s+(\w+)|(\w+)",w)
                # word = word.group(1) or word.group(2)
                foreword, word = getMainWord(w)
                words.append(word)
                forewords.append(foreword)
                hint = note["Wiktionary nr"]
                hints.append(int(hint) if hint else 1)
            except Exception as e:
                sys.stderr.write(f"Failed for word {word}\nerror {e}\nw {w}")
                raise e
        # showInfo(f"notes {notes}")
        try:
            notesall.extend(notes)
            contents = getWiktionaryContents(words,hints)
        except Exception as e:
            sys.stderr.write(f"Failed for words {words}")
            raise e
        for k, (note,word,foreword) in enumerate(zip(notes,words,forewords)):
            # showInfo(f"note {note}\nword {word}")
            ind = 50*n+k
            setToolText(f"{'Working on word number':<25} {ind+1:>{digits}}/{len(noteidsall)}")
            content = contents[word]
            content = contents[word]
            tag = "nowikidef"
            if content is None:
                missedwords.append(word)
                addTag(note,tag,True)
                continue
            remTag(note,tag)
            try:
                wordType = getWordType(content)
                if wordType is None:
                    missedwords.append(word)
                    addTag(note,tag,True)
                    continue
                plurals = getPlural(content, wordType, foreword)
                meanings = getMeanings(content, word=word)
                meanings = removeWordFromDef(meanings,word)
                tag = "nowikimeaning"
                if not meanings: addTag(note,tag)
                if meanings: remTag(note,tag)
                examples = getExamples(content)
                english = getTranslation(content, lang="en")
                estonian = getTranslation(content, lang="et")
                newgerman = plurals[0] if wordType=="Substantiv" else word
                plural = ("no plural" if not plurals[1] else f"die {plurals[1]}") if wordType=="Substantiv" else plurals
                newgermanc = coloredName(newgerman,newgerman)
                pluralc = coloredName(plural,newgerman)

                for params in (("German", newgermanc),
                                ("Plural and inflected forms", pluralc, plural and bw.m9.isChecked() and re.search(r"[^\s\d\[\]]{2,}",plural)),
                                ("Definition", newlinetobr(meanings), meanings and bw.m7.isChecked() and re.search(r"[^\s\d\[\]]{2,}",meanings)),
                                ("Part of Speech", wordType),
                                ("Sample sentence", newlinetobr(examples), examples and bw.m8.isChecked() and re.search(r"[^\s\d\[\]]{2,}",examples)),
                                ("English", english),
                                ("Estonian", estonian)):
                    if len(params)==2:
                        field, value = params
                        checkTest = False
                    elif len(params)==3:
                        field, value, checkTest = params
                    if overwrite or note[field]=="" or checkTest:
                        if value is None: value=""
                        # showInfo(f"field {field}\nvalue {value}\ntype value {type(value)}\ntype notefield {type(note[field])}\nnotefield {note[field]}")
                        note[field] = value
            except Exception as e:
                sys.stderr.write(f"Failed for ind {ind} german {note['German']} word {word}\nerror {e}\ncontent {content}")
                raise e
            # showInfo("\n".join([f"{field}" for field in note]))
            # t = [f"field {field} type {type(note[field])} value {note[field]}" for field in note]
            # showInfo("\n".join(t))
            note.flush()
    setToolText(f"Starting to work on IPA")
    addAllIpas(notesall, overwrite=overwrite)
    closeTooltip()
    if len(missedwords): showInfo(f"Missed words: {', '.join(missedwords)}", parent=bw)
    else: showInfo("Inserted data from Wiktionary for {} cards.".format(len(noteidsall)), parent=bw)
    mw.reset()

def getWiktionaryContents(words, whichWords = 1, lang="de"):
    words = [words] if isinstance(words,str) else words
    whichWords = [whichWords]*len(words) if isinstance(whichWords,int) else whichWords
    texts = {}
    for n in range(1+(len(words)-1)//50):
        words2 = words[50*n:50*(n+1)]
        data = requests.get(f"https://"+lang+f".wiktionary.org/w/api.php?action=query&format=json&prop=revisions&rvprop=content&rvslots=*&titles="+"|".join(words2))
        data = json.loads(data.text)["query"]["pages"]
        contents = {data[el]["title"]: None if int(el)<0 else data[el]["revisions"][0]["slots"]["main"]["*"] for el in data}
        for word in contents:
            try:
                multDefs = splitMultDefs(contents[word], lang=lang)
                texts[word] = multDefs[whichWords[50*n+words2.index(word)]-1] if multDefs else None
            except Exception as e:
                sys.stderr.write(f"Failed for word {word}\nerror {e}\nwords {words}\nwords2 {words2}\n")
                raise e
    return texts

def getMainWord(german):
    word = remHTML(german) if german else german
    return re.search(r"^(?:(-?(?:\(?sich\)?|(?:\(?(?:der|die|das)(?:/(?:der|die|das))?\)?)))\s+)?(-?\w+)",word).groups()

def removeWordFromDef(text, word):
    if not text: return text
    return re.sub(word,"",text,flags=re.IGNORECASE)

def newlinetobr(text):
    if text is None: return None
    # return re.sub(r"(\n|^)(.+)(?=\n)",r"\g<1><div>\g<2></div>",text)
    return re.sub(r"\n",r"<br>",text)

def getWordType(contents):
    x= re.search(r"=== (\{\{Wortart\|(.*?)\|Deutsch\}\}.*)",contents)
    if not x: return None
    return f"{x.group(2)} adjektivisch" if "adjektivische Deklination" in x.group(1) else x.group(2)

articles = {"m": "der", "f": "die", "n": "das"}
def joinPlural(els):
    return ", ".join([el if isinstance(el,str) else ", ".join(el if len(el)==1 else ["("+ ", ".join(el) +")"]) for el in els])
def getPlural(contents, wordtype, foreword=""):
    if wordtype=="Substantiv adjektivisch":
        table = re.search(r"\{\{Deutsch adjektivisch Übersicht\s*(.*?)\s*\}\}", contents, flags=re.DOTALL).group(1)
        stamms = re.findall(r"\|Stamm.*?=(\w*)",table)
        stamm = ""
        for n, x in enumerate(stamms):
            stamm += (("" if n==0 else "/") + f"{x}") if x not in stamms[:n] else ""
        return f"der {stamm}", stamm.replace("/","n/")+"n"
    elif wordtype=="Substantiv":
        if re.search(r"\{\{Deutsch Toponym Übersicht\s*(.*?)\s*\}\}", contents, flags=re.DOTALL):
            return f"(das) {getWordFromContents(contents)}", None
        table = re.search(r"\{\{Deutsch (?:Substantiv|Name) Übersicht\s*(.*?)\s*\}\}", contents, flags=re.DOTALL).group(1)
        genders = re.findall(r"\|Genus.*?=(\w*)",table)
        
        singulars = re.findall(r"\|Nominativ Singular.*?=(\w*)",table)
        singular = ""
        for n, x in enumerate(singulars):
            singular += (("" if n==0 else "/") + f"{x}") if x not in singulars[:n] else ""
        plurals = re.findall(r"\|Nominativ Plural.*?=(\w*)",table)
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
        komp = re.findall(r"\|Komparativ.*?=(\w*)",table)
        sup = re.findall(r"\|Superlativ.*?=(\w*)",table)
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
        

def splitMultDefs(contents, lang = "de"):
    try:
        if contents is None: return None
        langsectiontitles = {"de": "({{Sprache|Deutsch}})", "en": "German"}
        split = re.split(r"(^==[^=]*?==$)", contents, flags=re.MULTILINE)
        assert len(split)%2==1, "Wrong number of sections in the page."
        section = None
        for n in range((len(split)-1)//2):
            if langsectiontitles[lang] in split[1+2*n]:
                sectiontitle = split[1+2*n]
                section = split[1+2*n]+split[1+2*n+1]
                break
        if section is None: return None
        multipledeftitles = {"de": r"(=== \{\{Wortart\|.*?\|Deutsch\}\}.*)", "en": ".*"}
        data = []
        split = re.split(multipledeftitles[lang], section)
        for n in range((len(split)-1)//2):
            # if re.search(multipledeftitles[lang], split[1+2*n]):
            data.append(sectiontitle+"\n"+split[1+2*n]+split[1+2*n+1])
    except Exception as e:
        sys.stderr.write(f"Contents {contents}")
        raise e
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
    rawdata = re.search(r"\{\{Bedeutungen\}\}\s*(.*?)(?:\n\n|\n\{\{)", contents, flags=re.DOTALL)
    if not rawdata:
        return None
    rawdata = rawdata.group(1)
    replacements = {r"\[\[[^\]]*\|(?P<link>.*?)\]\]": "",
                    r"\[\[": "", r"\]\]": "", "''(?P<quote>.*?)''": "", r"(?P<ref><ref>.*?</ref>)": "",
                    r":+\[(?P<start>.*?)\]": "", r"kPl\.": "kein Plural", r"kSt\.": "keine Steigerung"}
    namedgroups = {"quote": r"<i>\g<quote></i>", "start": r"[\g<start>]", "ref": "", "link": r"\g<1>"}
    rawdata = re.sub(r"\{\{K\|(.*?)\}\}", lambda x: kreplacer(x), rawdata)
    rawdata = re.sub(r"\{\{(.*?)\}\}", lambda x: curlyjoiner(x), rawdata)
    if replacements:
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
    if hideWord:
        rawdata = rawdata.replace(word,"_")
    return rawdata

def getExamples(contents):
    rawdata = re.search(r"\{\{Beispiele\}\}\s*(.*?)(?:\n\n|\n\{\{)", contents, flags=re.DOTALL)
    if not rawdata:
        return None
    rawdata = rawdata.group(1)
    replacements = {r"\[\[": "", r"\]\]": "", "''(?P<quote>.*?)''": "",
                    r"(?:(?<=\n)|^):+(?P<start>\[)(?=[^\[]|$)": "", r"kPl\.": "kein Plural", r"(?P<ref><ref>.*?</ref>)": "",
                    r"(?P<beispf>\s*\{\{Beispiele fehlen.*?\}\})": "", r"(?P<beleg>\(\[http://.*?\))": ""}
    namedgroups = {"quote": r"<i>\g<quote></i>", "start": r"\g<start>", "ref": "", "beispf": "", "beleg": ""}
    if replacements:
        rawdata = re.sub("|".join(replacements.keys()), lambda x: replacer(x,replacements, namedgroups), rawdata)
    return rawdata

def getWordFromContents(contents):
    return re.search(r"==\s*(\w+)\s*.*?==",contents).group(1)

def getIPA2(words, lang="de"):
    contentsf = {"de": getIPA2contents, "en": getIPA2contentsen}
    if isinstance(words,str): words = [words]
    contents = getWiktionaryContents(words, lang=lang)
    return {word: "[.]" if contents[word] is None else contentsf[lang](contents[word]) for word in words}

def getIPA2contents(contents):
    word = re.search(r"==\s*(\w+)\s*.*?==",contents)
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

def remNewLine():
    notes = bw.selectedNotes()
    edited_N = 0
    for k, n in enumerate(notes):
        edited_card = False
        obj = mw.col.getNote(n)
        # showInfo(f"Keys: <{obj.keys()}>\ngerman: <{obj['German']}>\ngerman repr: <{repr(obj['German'])}>")
        for field in {"Definition", "Sample sentence"}:
            newtext = re.sub(r"\n", "", obj[field])
            if newtext != obj[field]:
                obj[field] = newtext
                if not edited_card:
                    edited_N +=1
                    edited_card = True
        obj.flush()
    mw.reset()
    showInfo("Worked on {} cards, removed newline in {} cards.".format(len(notes),edited_N))

def nbsp_to_space():
    # bw = aqt.dialogs._dialogs['Browser'][1]
    notes = bw.selectedNotes()
    edited_N = 0
    for k, n in enumerate(notes):
        edited_card = False
        obj = mw.col.getNote(n)
        # showInfo(f"Keys: <{obj.keys()}>\ngerman: <{obj['German']}>\ngerman repr: <{repr(obj['German'])}>")
        for field in obj.keys():
            newtext = re.sub(r"(?=\s)[^\n]", " ", obj[field].replace("&nbsp;", " "))
            if newtext != obj[field]:
                obj[field] = newtext
                if not edited_card:
                    edited_N +=1
                    edited_card = True
        obj.flush()
    mw.reset()
    showInfo("Worked on {} cards, replaced &nbsp; in {} cards.".format(len(notes),edited_N))

def coloredName(word, german):
    if not word:
        return word
    cols = {"die": "#ff0000", "der": "#0000ff", "das": "#00aa00"}
    match = re.match(r"\W*?(\w+)", german)
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
        match = re.match(r"\W*?(\w+)", w)
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
        bw.setFocus()
        tooltip("text", period=period, parent=aqt.dialogs._dialogs['Browser'][1])
        aqt.utils._tooltipLabel.setWindowFlags(Qt.SplashScreen)
        aqt.utils._tooltipLabel.show()
        aqt.utils._tooltipLabel.setText("<table cellpadding=10>\n<tr>\n<td><pre>{}</pre></td>\n</tr>\n</table>".format(text))
        aqt.utils._tooltipLabel.adjustSize()
        qApp.processEvents()
        bw.activateWindow()
    aqt.utils._tooltipTimer.setInterval(period)
    aqt.utils._tooltipLabel.setText("<table cellpadding=10>\n<tr>\n<td><pre>{}</pre></td>\n</tr>\n</table>".format(text))
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
        setToolText(newtext)
    if len(notes) > 0:
        mw.reset()
        if endInfo: showInfo("Done {} items".format(len(notes)), parent=bw)
        closeTooltip()

### create a new menu item, "test"
##action = QAction("test", Browser)
### set it to call testFunction when it's clicked
##action.triggered.connect(testFunction)
### and add it to the tools menu
##Browser.form.menuCards.addAction(action)

addHook("browser.setupMenus", onSetupMenus)