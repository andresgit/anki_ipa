import requests
import re
import time

text = """müssen, muss, musste, hat gemusst

Präsens  
ich muss, du musst, er muss, wir müssen, ihr müsst, sie müssen

Präteritum 
ich musste, du musstest, er musste, wir mussten, ihr musstet, sie mussten

Imperativ 
-

Konjunktiv I 
ich müsse, du müssest, er müsse, wir müssen, ihr müsset, sie müssen

Konjunktiv II 
ich müsste, du müsstest, er müsste, wir müssten, ihr müsstet, sie müssten"""


def getIPAEng(word):
    if not word.strip():
        return ""
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

def allIPA(word, checkEnglishIfNone = True):
    res = []
    for x in word.split():
        y = getIPA(x)
        if y == "[.]" and checkEnglishIfNone:
            y = getIPAEng(x)
        res.append(y)
    return " ".join(res)

def pluralIPA(w, checkEnglishIfNone = True):
    ipas = []
    w=w.replace("&nbsp;", " ").replace("&#32;"," ").replace("&#160;"," ")
    for x in map(str.strip, re.split(";|,",w)):
        ipas.append(allIPA(x, checkEnglishIfNone))
    return ", ".join(ipas)

##print(getIPA("ich"))

removebrackets = True
printNewline = True
##printNewline = False

for x2 in text.splitlines():
    if printNewline:
        x3 = re.sub("\s*\[.*?\]\s*","",x2)
        if removebrackets:
            x3 = re.sub("\(.*?\)","",x3)
        if x2.strip()=="Konjunktiv I":
            x3="Konjunktiv eins"
        elif x2.strip()=="Konjunktiv II":
            x3="Konjunktiv zwei"
        ipas = pluralIPA(x3)
        print(x2)
        if x2.strip() and x2.strip()!="-":
            print(ipas)
    else:
        for x in x2.split(","):
            if x:
                x = x.split(" [")[0]
                x3 = x
                if removebrackets:
                    x3 = re.sub("\(.*?\)","",x3)
                x3=x3.replace(" I "," eins ").replace(" II "," zwei ")
                ipas = [getIPA(y) if y else "" for y in re.split("\)|\(| ",x3)]
                ipas = filter(None,ipas)
                print(x," ".join(ipas), end="")
                if len(x2.split(",")) > 1 and x != x2.split(",")[-1]:
                    print(", ",end="")
        print()
