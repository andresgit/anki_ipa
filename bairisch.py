import requests
import re

agent = {"User-Agent":'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}

alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXZ"
##alphabet = "A"

addr="https://www.bayrisches-woerterbuch.de/buchstabe-"

##text="""
##<tr class="row-2 even">
##	<td class="column-1"><a href="http://www.bayrisches-woerterbuch.de/a-pers-fuerwort-3-pers-m/">a  (Pron. 3. Pers. m.)</a></td><td class="column-2">[<u>à</u>]</td><td class="column-3">er <a href="http://www.bayrisches-woerterbuch.de/a-pers-fuerwort-3-pers-m/"><i>Weiterlesen...</i></a></td>
##</tr>
##<tr class="row-3 odd">
##	<td class="column-1"><a href="http://www.bayrisches-woerterbuch.de/a-unbestimmter-artikel/">a (unbest. Art.)</a></td><td class="column-2">[<u>à</u>]</td><td class="column-3">ein, eine, ein <a href="http://www.bayrisches-woerterbuch.de/a-unbestimmter-artikel/"><i>Weiterlesen...</i></a></td>
##</tr>
##<tr class="row-4 even">
##	<td class="column-1"><a href="http://www.bayrisches-woerterbuch.de/aa-auch-sogar/">aa (Adv.)</a></td><td class="column-2">[<u>à:</u>]</td><td class="column-3">auch <a href="http://www.bayrisches-woerterbuch.de/aa-auch-sogar/"><i>Weiterlesen...</i></a></td>
##</tr>
##<tr class="row-5 odd">
##	<td class="column-1"><a href="http://www.bayrisches-woerterbuch.de/aa/">A-A, das</a></td><td class="column-2">[à-<u>à:</u>]</td><td class="column-3">Exkremente <a href="http://www.bayrisches-woerterbuch.de/aa/"><i>Weiterlesen...</i></a></td>
##</tr>
##<tr class="row-6 even">
##	<td class="column-1"><a href="http://www.bayrisches-woerterbuch.de/aba-awa-oba/">aba<br />
##awa (Adv.)</a></td><td class="column-2">[<u>å:</u>wà]</td><td class="column-3">siehe <a href="http://www.bayrisches-woerterbuch.de/oba-owa-adv/"><i>oba/owa </i></a></td>
##</tr>
##<tr class="row-7 odd">
##	<td class="column-1"><a href="http://www.bayrisches-woerterbuch.de/abbeerln/">abbeerln</a></td><td class="column-2">[<u>å:</u>beàln / <u>å</u>bbeàln/<br />
##<u>å:</u>biàln / <u>å</u>bbiàln]</td><td class="column-3">abbeeren, Beeren zupfen, abnehmen</td>
##</tr>
##<tr class="row-8 even">
##	<td class="column-1"><a href="http://www.bayrisches-woerterbuch.de/abbetteln/">abbetteln</a></td><td class="column-2">[<u>å:</u>bädln / <u>å</u>bbädln]</td><td class="column-3">durch Betteln oder penetrantes Bitten etwas von jmdm. erlangen</td>
##</tr>"""

def extractData(wordBlock):
    link = re.search('<a href="(.*?)">',wordBlock)
    cols = re.findall("<td.*?>(.*?)</td>",wordBlock,re.S)
##    cols = re.findall("<td.*?>(.*?)</td>",wordBlock,re.S)
    return list(map(lambda y: re.sub("<.*?>","",y),cols))

##words = re.findall("<tr.*?>\s*(.*?)\s*</tr>",text,re.S)
##for x in words:
##    print(x)
##    print()
##words = list(map(extractData, words))
##print()
##for x in words:
##    print(x)
##    print()
##print(words)
##print(words)

N=0
for a in alphabet:
    dat = requests.get(addr+a.lower(), headers=agent).text
##    dat = requests.get("https://www.bayrisches-woerterbuch.de/buchstabe-a/").text
##    dat = requests.get("https://www.bayrisches-woerterbuch.de", headers=agent).text
    
##    print(dat)
    dat = dat.split('<tbody class="row-hover">')[1].split("</tbody>")[0]
##    print(dat)
    wordBlocks = re.findall("<tr.*?>\s*(.*?)\s*</tr>",dat,re.S)
    words = list(map(extractData, wordBlocks))
    N += len(words)
    print("{} {:>4} {:>7}".format(a,len(words),N))
##    print("Tot",N)
