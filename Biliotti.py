import string
from collections import Counter
import networkx as nx


#  Alberto Biliotti
#  Matricola: 7109894
#  Email: alberto.biliotti@stud.unifi.it

def ottieniDizionarioGrafoCalcolaAnno(path, indice_titolo, indice_venue, indice_autori=1):
    grafo = nx.Graph()  # creo il grafo
    file = open(path, "r", errors="ignore")  # apro il file in lettura
    dizAut = {}  # creo il dizionario che conterrà gli autori con i rispettivi titoli
    dizPub = {}  # creo il dizionario che conterrà le pubblicazioni con i rispettivi autori
    oldest = 2023
    oldest_venue = ""
    for line in file:
        campi = line.split(";")  # divido la linea letta nei campi
        autori = campi[indice_autori]  # ricavo i nomi degli autori
        # mi ricavo l'anno di pubblicazione evitando d'includere il carattere di fine riga se presente
        if campi[-1].isnumeric() and 6 > len(campi[-1]) > 3:
            annopub = int(campi[-1])
        elif campi[-1][:-1].isnumeric() and 6 > len(campi[-1]) > 3:
            annopub = int(campi[-1][:-1])
        else:
            continue  # se l'anno è scritto in un formato non valido passo alla prossima linea del file
        if autori != "" and (campi[indice_titolo], annopub) not in grafo:
            autori = set(autori.split("|"))  # ricavo la lista degli autori
            dizPub[campi[indice_titolo], int(campi[-1][:-1])] = autori  # inserisco gli autori nel dizionario della
            # pubblicazione
            if annopub < oldest:  # controllo se la venue in analisi è la più vecchia, se si aggiorno la variabile
                oldest = annopub
                oldest_venue = campi[indice_venue]
            for nome in autori:  # aggiorno il grafo e il dizionario degli autori con la pubblicazione in analisi
                grafo.add_edge(nome, (campi[indice_titolo], annopub))
                if nome not in dizAut:
                    dizAut[nome] = {(campi[indice_titolo], annopub)}  # se l'autore non era già presente nel
                    # dizionario, creo un insieme contenente la pubblicazione in analisi
                else:
                    dizAut[nome].add((campi[indice_titolo], annopub))
    file.close()  # chiudo il file dopo averlo analizzato completamente
    return dizAut, dizPub, grafo, oldest, oldest_venue


def bfsAnno(G: nx.Graph, nodo_partenza, limite_anno):
    # Metodo che esegue una visita BFS partendo dal nodo di partenza indicato in ingresso considerando le
    # pubblicazioni fino all'anno indicato
    colorati = set()  # insieme che conterrà i nodi già visitati
    ok = set()  # insieme contenente i nodi delle pubblicazioni scritte prima dell'anno indicato
    nodi_prossimo_livello = {nodo_partenza}  # insieme contenente i nodi che incontro durante la visita (che potrei
    # aver già visitato), che stanno al livello inferiore nell'albero BFS rispetto all'iterazione corrente
    while nodi_prossimo_livello:  # ciclo finché ho ancora nodi da visitare
        livello_attuale = nodi_prossimo_livello
        nodi_prossimo_livello = set()
        for v in livello_attuale:  # ciclo sui nodi del livello in analisi
            if v not in colorati:  # controllo di non aver già visitato il nodo
                vicini = G.neighbors(v)
                if isinstance(v, tuple):  # controllo se il nodo corrisponde a una pubblicazione
                    if limite_anno >= v[1]:
                        nodi_prossimo_livello.update(vicini)  # se il nodo che sto analizzando è una pubblicazione di
                        # un anno precedente a quello indicato proseguo la visita dei nodi vicini e aggiungo il nodo
                        # in analisi alla lista dei nodi "antichi"
                        ok.add(v)
                    colorati.add(v)  # tengo comunque traccia della pubblicazione analizzata anche se più recente
                else:
                    # se incontro un nodo autore aggiungo semplicemente i vicini alla lista dei nodi da controllare
                    # e tengo traccia di aver visitato tale autore
                    colorati.add(v)
                    nodi_prossimo_livello.update(vicini)
    return colorati, ok


def componenti_connesse_anno(grafon_non_conesso, anno_pubblicazione, dizionarioAut):
    # ricavo le componenti connesse del grafo con pubblicazioni più antiche dell'anno in ingresso
    # (corrispondenti agli insiemi di nodi raggiungibili con una BFS che parte dallo stesso nodo)
    colorati = set()  # nodi gia osservati da cui non farò partire una visita BFS
    lista_nodi = set(dizionarioAut.keys())  # uso come nodo sorgente solo gli autori, visto che non possono esistere
    # pubblicazioni senza autore, diminuendo il numero di BFS necessarie
    for nodo in lista_nodi:
        if nodo not in colorati:  # controllo di non aver gia incontrato l'autore
            c, ok = bfsAnno(grafon_non_conesso, nodo, anno_pubblicazione)  # faccio partire la BFS
            colorati.update(c)  # aggiorno i nodi visitati
            yield ok  # genero un iteratore invece di ritornare tutto insieme


def calcolaStringheCompConAnno(grafo: nx.Graph, anno_pubblicazione, dizionarioAutori):
    insieme_titoli = set()  # insieme che conterrà le stringhe ottenute concatenando tutti i titoli delle pubblicazioni
    # delle componenti connesse con almeno 30 pubblicazioni
    for n in componenti_connesse_anno(grafo, anno_pubblicazione, dizionarioAutori):
        if len(n) > 30:  # controllo che la componente connessa abbia almeno 30 pubblicazioni
            stringatemp = set()  # insieme provvisorio contenente tutti i titoli delle pubblicazioni appartenenti
            # alla stessa componente connessa
            for el in n:
                stringatemp.add(el[0])
            insieme_titoli.add(" ".join(stringatemp))  # creo la stringa con tutti i titoli delle pubblicazioni
            # della componente e la aggiungo all'insieme
    return insieme_titoli


def pulisciConta(insstringhe: set):
    # metodo che, data una stringa, ne rimuove le stopword più comuni e conta le parole rimanenti,
    # restituendo le 10 più frequenti
    while insstringhe:
        stringa = insstringhe.pop().lower().replace(" the ", " ").replace(" a ", " ").replace(" and ", " ").replace(
            " to ",
            " ") \
            .replace(" in ", " ").replace(" for ", " ").replace(" to ", " ").replace(" of ", " ").replace(" on ", " ") \
            .replace(" an ", " ").replace(" with ", " ").replace(" by ", " ").replace(" how ", " ")
        print(Counter(stringa.translate(str.maketrans(' ', ' ', string.punctuation))  # rimuovo anche la punteggiatura
                      .split()).most_common(10))


def trovaAutoreMaxCollaborazioni(grafo, dizionario_autori, anno_pubblicazione):
    # Per ogni autore, controllo il numero di collaborazioni in pubblicazioni fino all'anno in input
    contatore_collaborazioni_max = 0  # variable che memorizza il numero massimo temporaneo di collaborazioni per autore
    autore_collaborativo = ""  # variabile che conterrà il nome dell'autore con il numero massimo di collaborazioni
    for autore_pub in dizionario_autori:
        conttemp = 0  # numero di collaborazioni dell'autore in analisi
        pubblicazioni_autore = grafo.neighbors(autore_pub)  # ricavo le pubblicazioni dell'autore in analisi
        for pubblicazione in pubblicazioni_autore:
            if anno_pubblicazione >= pubblicazione[1]:  # per ogni pubblicazione, se l'anno è minore o uguale di
                # quello passato in input, conto il numero di autori
                # (escludendo l'autore in analisi) e aggiorno il numero di collaborazioni
                conttemp += len(set(grafo.neighbors(pubblicazione))) - 1
        if conttemp > contatore_collaborazioni_max:  # se trovo un autore con più collaborazioni aggiorno
            # il massimo numero di collaborazioni per autore e registro il nome di tale autore
            autore_collaborativo = autore_pub
            contatore_collaborazioni_max = conttemp
    return autore_collaborativo, contatore_collaborazioni_max


def unisciGrafo(grafoPartenza, dizAutori):
    # metodo per generare il grafo unione grazie ai dizionari degli autori
    for autore_pub in dizAutori:
        for pubblicazione in dizAutori[autore_pub]:
            grafoPartenza.add_edge(autore_pub, pubblicazione)


def uniscidizAut(dizA: dict, dizB: dict):
    # Metodo per unire due dizionari degli autori,
    # utile per ottenere il dizionario degli autori associato al grafo unione
    for el in dizB:
        if el not in dizA:
            dizA[el] = dizB[el]
        else:
            dizA[el] = dizA[el].union(dizB[el])
    return dizA


def creaGrafoAutori(multigrafo: nx.MultiGraph, dizPub: dict):
    # Metodo per riempire il multigrafo degli autori grazie ai dizionari delle pubblicazioni
    for autori in dizPub.values():
        multigrafo.add_nodes_from(autori)
        while autori:  # per ogni pubblicazione devo inserire un arco tra qualunque combinazione di due suoi autori
            aut = autori.pop()
            for altriaut in autori:
                multigrafo.add_edge(aut, altriaut)


def cercaCoppiaMigliore(multigrafo: nx.MultiGraph, dizAut: dict):
    # cerco la coppia con più pubblicazioni condivise nel multigrafo degli autori
    # ossia la coppia di nodi con più archi tra loro
    coppia_autori = ("", "", 0)
    max_collaborazioni = 0
    for autore_pubblicazione in dizAut.keys():  # controllo le collaborazioni di ogni autore
        vicini = multigrafo.neighbors(autore_pubblicazione)
        for vicino in vicini:
            numArchiInComune = multigrafo.number_of_edges(autore_pubblicazione, vicino)  # conto il numero di nodi
            # tra l'autore in analisi e ogni vicino
            if numArchiInComune > max_collaborazioni:
                max_collaborazioni = numArchiInComune  # aggiorno la coppia più collaborativa
                coppia_autori = (autore_pubblicazione, vicino, max_collaborazioni)
    return coppia_autori


# definisco gli anni fino a cui voglio limitare le mie indagini
anni = [1960, 1970, 1980, 1990, 2000, 2010, 2020, 2023]
if __name__ == "__main__":
    # Inizio analizzando le tesi di dottorato (phd)
    dizAutphd, dizPubphd, grafophd, oldestphd, oldestvenuephd = ottieniDizionarioGrafoCalcolaAnno(
        r"out-dblp_phdthesis.csv", -3, 1)
    # Stampo la venue più antica
    print("Venue delle tesi di phd più antica : " + oldestvenuephd + " del " + str(oldestphd))
    for anno in anni:  # per ogni anno nella lista degli anni
        # cerco prima le componenti connesse di cui stampo i termini per poi trovare l'autore con più collaborazioni
        strtot = set(calcolaStringheCompConAnno(grafophd, anno, dizAutphd))
        print("Numero componenti connesse nel grafo delle tesi di phd fino all'anno " + str(anno) + ": " + str(
            len(strtot)))
        pulisciConta(strtot)
        autore = trovaAutoreMaxCollaborazioni(grafophd, dizAutphd, anno)
        print("Autore con il più grande numero di collaborazioni nelle tesi di phd fino al " + str(anno)
              + ": " + str(autore[0]) + " con ben " + str(autore[1]) + " collaborazioni ripetute")

    dizAutinc, dizPubinc, grafoinc, oldestinc, oldestvenueinc = ottieniDizionarioGrafoCalcolaAnno(
        r"out-dblp_incollection.csv", -3, 3)
    # Analizzo le incollection
    print("")
    print("Venue delle incollection più antica : " + oldestvenueinc + " del " + str(oldestinc))
    for anno in anni:
        strtot = set(calcolaStringheCompConAnno(grafoinc, anno, dizAutinc))
        print("Numero componenti connesse nel grafo delle incollection fino all'anno " + str(anno) + ": " + str(
            len(strtot)))
        pulisciConta(strtot)
        autore = trovaAutoreMaxCollaborazioni(grafoinc, dizAutinc, anno)
        print("Autore con il più grande numero di collaborazioni negli incollection fino al " + str(anno)
              + ": " + str(autore[0]) + " con ben " + str(autore[1]) + " collaborazioni ripetute")

    dizAutproc, dizPubproc, grafoproc, oldestproc, oldestvenueproc = ottieniDizionarioGrafoCalcolaAnno(
        r"out-dblp_proceedings.csv", -4, -4, 2)
    # Passo ad analizzare i proceeding
    print("Venue delle proceeding più antica : " + oldestvenueproc + " del " + str(oldestproc))
    for anno in anni:
        strtot = set(calcolaStringheCompConAnno(grafoproc, anno, dizAutproc))
        print(
            "Numero componenti connesse nel grafo delle procedure fino all'anno " + str(anno) + ": " + str(len(strtot)))
        pulisciConta(strtot)
        autore = trovaAutoreMaxCollaborazioni(grafoproc, dizAutproc, anno)
        print("Autore con il più grande numero di collaborazioni nei proceeding scritti fino al " + str(anno)
              + ": " + str(autore[0]) + " con ben " + str(autore[1]) + " collaborazioni ripetute")

    dizAutbook, dizPubbook, grafobook, oldestbook, oldestvenuebook = ottieniDizionarioGrafoCalcolaAnno(
        r"out-dblp_book.csv", -4, -12)
    # Ora analizzo i libri
    print("")
    print("Venue dei libri più antica : " + oldestvenuebook + " del " + str(oldestbook))
    for anno in anni:
        strtot = set(calcolaStringheCompConAnno(grafobook, anno, dizAutbook))
        print("Numero componenti connesse nel grafo dei libri fino all'anno " + str(anno) + ": " + str(len(strtot)))
        pulisciConta(strtot)
        autore = trovaAutoreMaxCollaborazioni(grafobook, dizAutbook, anno)
        print("Autore con il più grande numero di collaborazioni nei libri scritti fino al " + str(anno)
              + ": " + str(autore[0]) + " con ben " + str(autore[1]) + " collaborazioni ripetute")

    dizAutmastth, dizPubmastth, grafomastth, oldestmastth, oldestvenuemastth = ottieniDizionarioGrafoCalcolaAnno(
        r"out-dblp_mastersthesis.csv", -2, 1)
    # Analizzo le tesi di master
    print("")
    print("Venue delle tesi di master più antica : " + oldestvenuemastth + " del " + str(oldestmastth))
    for anno in anni:
        strtot = set(calcolaStringheCompConAnno(grafomastth, anno, dizAutmastth))
        print("Numero componenti connesse nel grafo delle tesi di master fino all'anno " + str(anno) + ": " + str(
            len(strtot)))
        pulisciConta(strtot)
        autore = trovaAutoreMaxCollaborazioni(grafomastth, dizAutmastth, anno)
        print("Autore con il più grande numero di collaborazioni in tesi di master fino al " + str(anno)
              + ": " + str(autore[0]) + " con ben " + str(autore[1]) + " collaborazioni ripetute")

    dizAutart, dizPubart, grafoart, oldestart, oldestvenueart = ottieniDizionarioGrafoCalcolaAnno(
        r"out-dblp_article.csv", 29, 15)
    # Procedo ad analizzare gli articoli
    print("")
    print("Venue degli articoli più antica : " + oldestvenueart + " del " + str(oldestart))
    for anno in anni:
        strtot = set(calcolaStringheCompConAnno(grafoart, anno, dizAutart))
        print(
            "Numero componenti connesse nel grafo degli articoli fino all'anno: " + str(anno) + ": " + str(len(strtot)))
        pulisciConta(strtot)
        autore = trovaAutoreMaxCollaborazioni(grafoart, dizAutart, anno)
        print("Autore con il più grande numero di collaborazioni per articolo fino al " + str(anno)
              + ": " + str(autore[0]) + " con ben " + str(autore[1]) + " collaborazioni ripetute")
    print("Ci vorrà qualche minuto...")
    dizAutinproc, dizPubinproc, grafoinproc, oldestinproc, oldestvenueinproc = ottieniDizionarioGrafoCalcolaAnno(
        r"out-dblp_inproceedings.csv", -6, 4)
    # Infine analizzo le inproceedings
    print("")
    print("Venue degli inproceedings più antica : " + oldestvenueinproc + " del " + str(oldestinproc))
    for anno in anni:
        strtot = set(calcolaStringheCompConAnno(grafoinproc, anno, dizAutinproc))
        print("Numero componenti connesse nel grafo degli inproceedings fino all'anno: " + str(anno) + ": " + str(
            len(strtot)))
        pulisciConta(strtot)
        autore = trovaAutoreMaxCollaborazioni(grafoinproc, dizAutinproc, anno)
        print("Autore con il più grande numero di collaborazioni in inproceedings fino al " + str(anno)
              + ": " + str(autore[0]) + " con ben " + str(autore[1]) + " collaborazioni ripetute")
    # Ora inizio l'analisi sul grafo unione,
    # restituendo la venue più vecchia tra tutte quelle recuperate nei passaggi precedenti
    dizAnpub = {oldestbook: oldestvenuebook, oldestinproc: oldestvenueinproc, oldestinc: oldestvenueinc,
                oldestart: oldestvenueart, oldestmastth: oldestvenuemastth, oldestphd: oldestvenuephd,
                oldestproc: oldestvenueinproc}
    minAnno = min(dizAnpub.keys())
    print("")
    print("Venue più antica in generale: " + str(dizAnpub[minAnno]) + " del " + str(minAnno))
    del grafoinproc  # dereferenzio i dizionari e i grafi non più usati per liberare un po' di RAM
    # (le strutture dati dereferenziate verranno infatti "eliminate" dal garbage collector di Python)
    # Inizio la costruzione del grafo unione a partire dai dizionari degli autori
    grafounione = grafoart
    del grafoart
    print("Ora ci vorrà molto tempo...")
    unisciGrafo(grafounione, dizAutinproc)
    unisciGrafo(grafounione, dizAutinc)
    unisciGrafo(grafounione, dizAutphd)
    unisciGrafo(grafounione, dizAutproc)
    unisciGrafo(grafounione, dizAutmastth)
    unisciGrafo(grafounione, dizAutbook)
    print("Sto unendo i dizionari...")
    # Unisco anche i vari dizionari in un unico dizionario, utile per le analisi finali sul grafo unione
    dizAutFin = uniscidizAut(dizAutart, dizAutinproc)
    dizAutFin = uniscidizAut(dizAutFin, dizAutinc)
    dizAutFin = uniscidizAut(dizAutFin, dizAutphd)
    dizAutFin = uniscidizAut(dizAutFin, dizAutproc)
    dizAutFin = uniscidizAut(dizAutFin, dizAutmastth)
    dizAutFin = uniscidizAut(dizAutFin, dizAutbook)
    print("Ora inizio a calcolare le componenti connesse...")
    del dizAutart
    del dizAutinproc
    for anno in anni:
        # Ora ripeto le analisi viste in precedenza sul grafo unione
        strtot = set(calcolaStringheCompConAnno(grafounione, anno, dizAutFin))
        print("Numero componenti connesse nel grafo unione fino all'anno: " + str(anno) + ": " + str(len(strtot)))
        pulisciConta(strtot)
        autore = trovaAutoreMaxCollaborazioni(grafounione, dizAutFin, anno)
        print("Autore con il più grande numero di collaborazioni in generale fino al " + str(anno)
              + ": " + str(autore[0]) + " con ben " + str(autore[1]) + " collaborazioni ripetute")
    # Ora costruisco il multigrafo a partire dal dizionario delle pubblicazioni
    multigrafoautori = nx.MultiGraph()
    print("Sto creando il Multigrafo!")
    creaGrafoAutori(multigrafoautori, dizPubart)
    print("Ultima attesa, ci siamo quasi!")
    creaGrafoAutori(multigrafoautori, dizPubinproc)
    print("Ci sono!")
    creaGrafoAutori(multigrafoautori, dizPubbook)
    creaGrafoAutori(multigrafoautori, dizPubphd)
    creaGrafoAutori(multigrafoautori, dizPubproc)
    creaGrafoAutori(multigrafoautori, dizPubmastth)
    creaGrafoAutori(multigrafoautori, dizPubinc)
    # Infine, cerco la coppia di autori con più collaborazioni in generale
    print(cercaCoppiaMigliore(multigrafoautori, dizAutFin))
    print("Fine, è possibile terminare l'esecuzione!")
    # è probabile che l'esecuzione ci metta tanto a terminare, anche dopo aver terminato tutti i calcoli necessari,
    # per cui, una volta che è stata stampata la stringa finale,
    # è possibile forzare il termine dell'esecuzione con un comando da tastiera
