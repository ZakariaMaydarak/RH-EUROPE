"""
Traduction des messages renvoyés par le serveur (erreurs, contrôles, libellés).

Le texte français sert de clé : `_("Le matricule {m} est déjà attribué…", m="EU1")`
renvoie la phrase dans la langue de la requête en cours (contextvar positionné par
routes.py), ou en français si la traduction manque. Les données ENREGISTRÉES
(historique, exports) restent en français : elles alimentent les systèmes internes.
"""

import contextvars

LANGUES = {"fr": "Français", "en": "English", "de": "Deutsch", "es": "Español", "it": "Italiano"}
ORDRE = ["en", "de", "es", "it"]
_langue = contextvars.ContextVar("rheurope_langue", default="fr")


def definir(langue):
    _langue.set(langue if langue in LANGUES else "fr")


def langue():
    return _langue.get()


def _(texte, **params):
    code = _langue.get()
    if code != "fr":
        trad = CATALOGUE.get(texte)
        if trad:
            texte = trad[ORDRE.index(code)] or texte
    return texte.format(**params) if params else texte


# Clé (français) : [anglais, allemand, espagnol, italien]
CATALOGUE = {
    # --- Libellés des champs
    "Nom": ["Last name", "Nachname", "Apellido", "Cognome"],
    "Prénom": ["First name", "Vorname", "Nombre", "Nome"],
    "Matricule": ["Employee ID", "Personalnummer", "N.º de empleado", "Matricola"],
    "Sexe": ["Gender", "Geschlecht", "Sexo", "Sesso"],
    "Adresse e-mail Accor": ["Accor email address", "Accor-E-Mail-Adresse", "Correo electrónico Accor", "Indirizzo e-mail Accor"],
    "Date de naissance": ["Date of birth", "Geburtsdatum", "Fecha de nacimiento", "Data di nascita"],
    "Date de début de contrat": ["Contract start date", "Vertragsbeginn", "Fecha de inicio del contrato", "Data di inizio contratto"],
    "Date de fin de contrat": ["Contract end date", "Vertragsende", "Fecha de fin del contrato", "Data di fine contratto"],
    "Type de contrat": ["Contract type", "Vertragsart", "Tipo de contrato", "Tipo di contratto"],
    "Service": ["Department", "Abteilung", "Departamento", "Reparto"],
    "Établissement": ["Hotel", "Hotel", "Establecimiento", "Struttura"],
    "Poste": ["Position", "Position", "Puesto", "Posizione"],
    "Manager": ["Manager", "Vorgesetzte(r)", "Responsable", "Responsabile"],
    # --- Référentiels
    "Pays": ["Country", "Land", "País", "Paese"],
    "Établissements": ["Hotels", "Hotels", "Establecimientos", "Strutture"],
    "Services": ["Departments", "Abteilungen", "Departamentos", "Reparti"],
    "Postes": ["Positions", "Positionen", "Puestos", "Posizioni"],
    "Types de contrat": ["Contract types", "Vertragsarten", "Tipos de contrato", "Tipi di contratto"],
    "Motifs de sortie": ["Leaving reasons", "Austrittsgründe", "Motivos de salida", "Motivi di uscita"],
    # --- Rôles
    "Administrateur (tous les établissements)": ["Administrator (all hotels)", "Administrator (alle Hotels)", "Administrador (todos los establecimientos)", "Amministratore (tutte le strutture)"],
    "Directeur d'hôtel (ses établissements)": ["Hotel manager (own hotels)", "Hoteldirektor(in) (eigene Hotels)", "Director de hotel (sus establecimientos)", "Direttore d'albergo (proprie strutture)"],
    "Aucun accès": ["No access", "Kein Zugriff", "Sin acceso", "Nessun accesso"],
    # --- Contrôles de saisie
    "Champ obligatoire.": ["Required field.", "Pflichtfeld.", "Campo obligatorio.", "Campo obbligatorio."],
    "Date de fin obligatoire pour un contrat « {type} ».": ["End date required for a “{type}” contract.", "Enddatum für einen Vertrag „{type}“ erforderlich.", "Fecha de fin obligatoria para un contrato «{type}».", "Data di fine obbligatoria per un contratto «{type}»."],
    "{champ} : {n} caractères maximum.": ["{champ}: {n} characters maximum.", "{champ}: maximal {n} Zeichen.", "{champ}: {n} caracteres como máximo.", "{champ}: massimo {n} caratteri."],
    "{champ} : caractères non autorisés (chiffres ou symboles).": ["{champ}: characters not allowed (digits or symbols).", "{champ}: unzulässige Zeichen (Ziffern oder Symbole).", "{champ}: caracteres no permitidos (cifras o símbolos).", "{champ}: caratteri non consentiti (cifre o simboli)."],
    "{champ} : valeur inconnue du référentiel.": ["{champ}: value not found in the reference list.", "{champ}: Wert nicht in der Referenzliste.", "{champ}: valor desconocido en la lista de referencia.", "{champ}: valore sconosciuto nell'elenco di riferimento."],
    "{champ} : « {valeur} » est désactivé dans le référentiel.": ["{champ}: “{valeur}” is deactivated in the reference list.", "{champ}: „{valeur}“ ist in der Referenzliste deaktiviert.", "{champ}: «{valeur}» está desactivado en la lista de referencia.", "{champ}: «{valeur}» è disattivato nell'elenco di riferimento."],
    "Établissement hors de votre périmètre.": ["Hotel outside your scope.", "Hotel außerhalb Ihres Zuständigkeitsbereichs.", "Establecimiento fuera de su ámbito.", "Struttura al di fuori del suo perimetro."],
    "Matricule invalide : 3 à 20 caractères (lettres majuscules, chiffres, - et _).": ["Invalid employee ID: 3 to 20 characters (capital letters, digits, - and _).", "Ungültige Personalnummer: 3 bis 20 Zeichen (Großbuchstaben, Ziffern, - und _).", "N.º de empleado no válido: de 3 a 20 caracteres (mayúsculas, cifras, - y _).", "Matricola non valida: da 3 a 20 caratteri (lettere maiuscole, cifre, - e _)."],
    "Le matricule {m} est déjà attribué à un autre collaborateur (Europe).": ["Employee ID {m} is already assigned to another employee (Europe).", "Die Personalnummer {m} ist bereits einer anderen Person zugeordnet (Europa).", "El n.º de empleado {m} ya está asignado a otro empleado (Europa).", "La matricola {m} è già assegnata a un altro collaboratore (Europa)."],
    "Format d'adresse e-mail invalide.": ["Invalid email address format.", "Ungültiges E-Mail-Format.", "Formato de correo electrónico no válido.", "Formato dell'indirizzo e-mail non valido."],
    "Domaine non autorisé : adresse attendue en {domaines}.": ["Domain not allowed: address expected in {domaines}.", "Domain nicht zulässig: Adresse mit {domaines} erwartet.", "Dominio no autorizado: se espera una dirección {domaines}.", "Dominio non consentito: indirizzo atteso in {domaines}."],
    "Adresse non nominative (boîte d'hôtel ou de service) : saisir l'adresse personnelle Accor du collaborateur.": ["Non-personal address (hotel or department mailbox): enter the employee's personal Accor address.", "Keine persönliche Adresse (Hotel- oder Abteilungspostfach): bitte die persönliche Accor-Adresse eingeben.", "Dirección no nominativa (buzón de hotel o de departamento): introduzca la dirección personal Accor del empleado.", "Indirizzo non nominativo (casella dell'albergo o del reparto): inserire l'indirizzo personale Accor del collaboratore."],
    "Cette adresse e-mail est déjà utilisée par un autre collaborateur (Europe).": ["This email address is already used by another employee (Europe).", "Diese E-Mail-Adresse wird bereits von einer anderen Person verwendet (Europa).", "Esta dirección de correo ya la utiliza otro empleado (Europa).", "Questo indirizzo e-mail è già utilizzato da un altro collaboratore (Europa)."],
    "L'adresse e-mail ne semble pas contenir le nom du collaborateur : vérifiez qu'il s'agit bien de la sienne.": ["The email address does not seem to contain the employee's name: check that it is really theirs.", "Die E-Mail-Adresse scheint den Namen der Person nicht zu enthalten: bitte prüfen.", "La dirección de correo no parece contener el apellido del empleado: compruebe que sea la suya.", "L'indirizzo e-mail non sembra contenere il cognome del collaboratore: verificare che sia il suo."],
    "{champ} : date invalide.": ["{champ}: invalid date.", "{champ}: ungültiges Datum.", "{champ}: fecha no válida.", "{champ}: data non valida."],
    "La date de naissance ne peut pas être dans le futur.": ["The date of birth cannot be in the future.", "Das Geburtsdatum darf nicht in der Zukunft liegen.", "La fecha de nacimiento no puede ser futura.", "La data di nascita non può essere nel futuro."],
    "Date de naissance invalide.": ["Invalid date of birth.", "Ungültiges Geburtsdatum.", "Fecha de nacimiento no válida.", "Data di nascita non valida."],
    "Incohérence : le collaborateur aurait {age} ans au début du contrat (minimum {min} ans).": ["Inconsistency: the employee would be {age} at contract start (minimum {min}).", "Unstimmigkeit: Die Person wäre bei Vertragsbeginn {age} Jahre alt (mindestens {min}).", "Incoherencia: el empleado tendría {age} años al inicio del contrato (mínimo {min}).", "Incoerenza: il collaboratore avrebbe {age} anni all'inizio del contratto (minimo {min})."],
    "Incohérence : le collaborateur aurait {age} ans au début du contrat.": ["Inconsistency: the employee would be {age} at contract start.", "Unstimmigkeit: Die Person wäre bei Vertragsbeginn {age} Jahre alt.", "Incoherencia: el empleado tendría {age} años al inicio del contrato.", "Incoerenza: il collaboratore avrebbe {age} anni all'inizio del contratto."],
    "Date de début à plus d'un an : vérifiez la saisie.": ["Start date more than one year ahead: check your entry.", "Beginn liegt mehr als ein Jahr in der Zukunft: bitte prüfen.", "Fecha de inicio a más de un año: compruebe los datos.", "Data di inizio oltre un anno: verificare l'inserimento."],
    "La date de fin de contrat doit être postérieure ou égale à la date de début.": ["The contract end date must be on or after the start date.", "Das Vertragsende muss am oder nach dem Vertragsbeginn liegen.", "La fecha de fin debe ser igual o posterior a la de inicio.", "La data di fine deve essere uguale o successiva alla data di inizio."],
    "Manager introuvable dans la base.": ["Manager not found in the database.", "Vorgesetzte(r) nicht in der Datenbank gefunden.", "Responsable no encontrado en la base.", "Responsabile non trovato nella banca dati."],
    "Un collaborateur ne peut pas être son propre manager.": ["An employee cannot be their own manager.", "Eine Person kann nicht ihre eigene Vorgesetzte sein.", "Un empleado no puede ser su propio responsable.", "Un collaboratore non può essere il proprio responsabile."],
    "Ce manager est inactif : choisissez un collaborateur actif.": ["This manager is inactive: choose an active employee.", "Diese(r) Vorgesetzte ist inaktiv: bitte eine aktive Person wählen.", "Este responsable está inactivo: elija un empleado activo.", "Questo responsabile è inattivo: scegliere un collaboratore attivo."],
    "Boucle hiérarchique : ce manager dépend lui-même de ce collaborateur.": ["Reporting loop: this manager reports to this employee.", "Hierarchieschleife: diese(r) Vorgesetzte untersteht selbst dieser Person.", "Bucle jerárquico: este responsable depende de este empleado.", "Ciclo gerarchico: questo responsabile dipende da questo collaboratore."],
    "Doublon potentiel : un collaborateur avec les mêmes nom, prénom et date de naissance existe déjà.": ["Possible duplicate: an employee with the same last name, first name and date of birth already exists.", "Mögliches Duplikat: Eine Person mit gleichem Nachnamen, Vornamen und Geburtsdatum existiert bereits.", "Posible duplicado: ya existe un empleado con el mismo apellido, nombre y fecha de nacimiento.", "Possibile duplicato: esiste già un collaboratore con stesso cognome, nome e data di nascita."],
    # --- Règles métier
    "La fiche contient des erreurs : corrigez-les avant d'enregistrer.": ["The record contains errors: correct them before saving.", "Der Datensatz enthält Fehler: bitte vor dem Speichern korrigieren.", "La ficha contiene errores: corríjalos antes de guardar.", "La scheda contiene errori: correggerli prima di salvare."],
    "Doublon potentiel détecté : confirmez qu'il s'agit bien d'une autre personne.": ["Possible duplicate detected: confirm that this is a different person.", "Mögliches Duplikat erkannt: bitte bestätigen, dass es sich um eine andere Person handelt.", "Posible duplicado detectado: confirme que se trata de otra persona.", "Possibile duplicato rilevato: confermare che si tratta di un'altra persona."],
    "Collaborateur introuvable ou hors de votre périmètre.": ["Employee not found or outside your scope.", "Person nicht gefunden oder außerhalb Ihres Bereichs.", "Empleado no encontrado o fuera de su ámbito.", "Collaboratore non trovato o fuori dal suo perimetro."],
    "Ce collaborateur est déjà inactif.": ["This employee is already inactive.", "Diese Person ist bereits inaktiv.", "Este empleado ya está inactivo.", "Questo collaboratore è già inattivo."],
    "Motif de sortie obligatoire.": ["Leaving reason required.", "Austrittsgrund erforderlich.", "Motivo de salida obligatorio.", "Motivo di uscita obbligatorio."],
    "Choisissez un motif.": ["Choose a reason.", "Bitte einen Grund wählen.", "Elija un motivo.", "Scegliere un motivo."],
    "Date de sortie invalide.": ["Invalid leaving date.", "Ungültiges Austrittsdatum.", "Fecha de salida no válida.", "Data di uscita non valida."],
    "Date invalide.": ["Invalid date.", "Ungültiges Datum.", "Fecha no válida.", "Data non valida."],
    "La date de sortie précède la date de début de contrat.": ["The leaving date is before the contract start date.", "Das Austrittsdatum liegt vor dem Vertragsbeginn.", "La fecha de salida es anterior al inicio del contrato.", "La data di uscita precede l'inizio del contratto."],
    "Antérieure au début du contrat.": ["Before the contract start.", "Vor Vertragsbeginn.", "Anterior al inicio del contrato.", "Precedente all'inizio del contratto."],
    "Ce collaborateur est déjà actif.": ["This employee is already active.", "Diese Person ist bereits aktiv.", "Este empleado ya está activo.", "Questo collaboratore è già attivo."],
    "Indiquez une nouvelle date de fin (aujourd'hui ou plus tard), ou laissez vide pour un contrat sans fin.": ["Enter a new end date (today or later), or leave empty for an open-ended contract.", "Neues Enddatum angeben (heute oder später) oder für einen unbefristeten Vertrag leer lassen.", "Indique una nueva fecha de fin (hoy o posterior) o déjela vacía para un contrato indefinido.", "Indicare una nuova data di fine (oggi o successiva) o lasciare vuoto per un contratto senza scadenza."],
    "Réactivation impossible : corrigez les informations indiquées.": ["Reactivation not possible: correct the information shown.", "Reaktivierung nicht möglich: bitte die angezeigten Angaben korrigieren.", "No se puede reactivar: corrija la información indicada.", "Riattivazione impossibile: correggere le informazioni indicate."],
    "Impossible : ce collaborateur est le manager de {n} collaborateur(s) actif(s). Changez d'abord leur manager.": ["Not possible: this employee manages {n} active employee(s). Change their manager first.", "Nicht möglich: Diese Person ist Vorgesetzte(r) von {n} aktiven Personen. Bitte zuerst deren Vorgesetzte ändern.", "No es posible: este empleado es responsable de {n} empleado(s) activo(s). Cambie primero su responsable.", "Impossibile: questo collaboratore è responsabile di {n} collaboratore/i attivo/i. Cambiare prima il loro responsabile."],
    "Choisissez d'abord l'établissement : il entre dans la composition du matricule.": ["Choose the hotel first: it is part of the employee ID.", "Bitte zuerst das Hotel wählen: es ist Teil der Personalnummer.", "Elija primero el establecimiento: forma parte del n.º de empleado.", "Scegliere prima la struttura: fa parte della matricola."],
    "Référentiel non enregistré.": ["Reference list not saved.", "Referenzliste nicht gespeichert.", "Lista de referencia no guardada.", "Elenco di riferimento non salvato."],
    "Paramètres non enregistrés.": ["Settings not saved.", "Einstellungen nicht gespeichert.", "Parámetros no guardados.", "Parametri non salvati."],
    "Domaine invalide : {d}": ["Invalid domain: {d}", "Ungültige Domain: {d}", "Dominio no válido: {d}", "Dominio non valido: {d}"],
    "Au moins un domaine autorisé est requis.": ["At least one allowed domain is required.", "Mindestens eine zulässige Domain ist erforderlich.", "Se requiere al menos un dominio autorizado.", "È richiesto almeno un dominio consentito."],
    "Modèle invalide : lettres, chiffres, - et _ et les repères {PAYS}, {ETAB}, {AAAA}, {AA}, avec un seul {N}.": ["Invalid pattern: letters, digits, - and _ and the markers {PAYS}, {ETAB}, {AAAA}, {AA}, with a single {N}.", "Ungültiges Muster: Buchstaben, Ziffern, - und _ sowie die Platzhalter {PAYS}, {ETAB}, {AAAA}, {AA}, mit genau einem {N}.", "Modelo no válido: letras, cifras, - y _ y los marcadores {PAYS}, {ETAB}, {AAAA}, {AA}, con un solo {N}.", "Modello non valido: lettere, cifre, - e _ e i segnaposto {PAYS}, {ETAB}, {AAAA}, {AA}, con un solo {N}."],
    "Nombre de chiffres entre 3 et 12.": ["Number of digits between 3 and 12.", "Anzahl der Ziffern zwischen 3 und 12.", "Número de cifras entre 3 y 12.", "Numero di cifre tra 3 e 12."],
    "Numéro de départ : entier positif.": ["First number: positive integer.", "Startnummer: positive ganze Zahl.", "Número inicial: entero positivo.", "Numero iniziale: intero positivo."],
    # --- Référentiels (contrôle des listes)
    "Référentiel inconnu.": ["Unknown reference list.", "Unbekannte Referenzliste.", "Lista de referencia desconocida.", "Elenco di riferimento sconosciuto."],
    "Liste attendue.": ["List expected.", "Liste erwartet.", "Se esperaba una lista.", "Elenco atteso."],
    "(vide)": ["(empty)", "(leer)", "(vacío)", "(vuoto)"],
    "Ligne {i} : format invalide.": ["Line {i}: invalid format.", "Zeile {i}: ungültiges Format.", "Línea {i}: formato no válido.", "Riga {i}: formato non valido."],
    "Ligne {i} : code « {code} » invalide (lettres, chiffres, - et _, 20 caractères max).": ["Line {i}: invalid code “{code}” (letters, digits, - and _, 20 characters max).", "Zeile {i}: ungültiger Code „{code}“ (Buchstaben, Ziffern, - und _, max. 20 Zeichen).", "Línea {i}: código «{code}» no válido (letras, cifras, - y _, 20 caracteres máx.).", "Riga {i}: codice «{code}» non valido (lettere, cifre, - e _, max 20 caratteri)."],
    "Ligne {i} : le code {code} est en double.": ["Line {i}: code {code} is duplicated.", "Zeile {i}: Code {code} ist doppelt.", "Línea {i}: el código {code} está duplicado.", "Riga {i}: il codice {code} è duplicato."],
    "Ligne {i} : libellé obligatoire pour {code}.": ["Line {i}: label required for {code}.", "Zeile {i}: Bezeichnung für {code} erforderlich.", "Línea {i}: etiqueta obligatoria para {code}.", "Riga {i}: etichetta obbligatoria per {code}."],
    "Ligne {i} : pays « {pays} » inconnu pour {code}.": ["Line {i}: unknown country “{pays}” for {code}.", "Zeile {i}: unbekanntes Land „{pays}“ für {code}.", "Línea {i}: país «{pays}» desconocido para {code}.", "Riga {i}: paese «{pays}» sconosciuto per {code}."],
    "Codes utilisés par des collaborateurs, impossibles à supprimer (désactivez-les) : {codes}": ["Codes used by employees cannot be deleted (deactivate them): {codes}", "Von Personen verwendete Codes können nicht gelöscht werden (bitte deaktivieren): {codes}", "Códigos utilizados por empleados, no se pueden eliminar (desactívelos): {codes}", "Codici utilizzati da collaboratori, non eliminabili (disattivarli): {codes}"],
    "Pays utilisés par des établissements, impossibles à supprimer : {codes}": ["Countries used by hotels cannot be deleted: {codes}", "Von Hotels verwendete Länder können nicht gelöscht werden: {codes}", "Países utilizados por establecimientos, no se pueden eliminar: {codes}", "Paesi utilizzati da strutture, non eliminabili: {codes}"],
    # --- API
    "Action non autorisée pour votre profil.": ["Action not allowed for your profile.", "Aktion für Ihr Profil nicht erlaubt.", "Acción no autorizada para su perfil.", "Azione non consentita per il suo profilo."],
    "Fichier manquant.": ["Missing file.", "Datei fehlt.", "Falta el archivo.", "File mancante."],
    "Fichier trop volumineux (5 Mo maximum).": ["File too large (5 MB maximum).", "Datei zu groß (max. 5 MB).", "Archivo demasiado grande (5 MB máximo).", "File troppo grande (massimo 5 MB)."],
    "Fichier illisible : utilisez un Excel (.xlsx) ou un CSV.": ["Unreadable file: use an Excel (.xlsx) or CSV file.", "Datei nicht lesbar: bitte Excel (.xlsx) oder CSV verwenden.", "Archivo ilegible: utilice un Excel (.xlsx) o un CSV.", "File illeggibile: utilizzare un Excel (.xlsx) o un CSV."],
    "Fichier vide.": ["Empty file.", "Leere Datei.", "Archivo vacío.", "File vuoto."],
    "Colonnes attendues : code, nom, pays (code ISO à 2 lettres ou nom du pays).": ["Expected columns: code, nom, pays (2-letter ISO code or country name).", "Erwartete Spalten: code, nom, pays (2-stelliger ISO-Code oder Ländername).", "Columnas esperadas: code, nom, pays (código ISO de 2 letras o nombre del país).", "Colonne attese: code, nom, pays (codice ISO a 2 lettere o nome del paese)."],
    "Confirmation manquante : saisir EFFACER.": ["Missing confirmation: type EFFACER.", "Bestätigung fehlt: EFFACER eingeben.", "Falta la confirmación: escriba EFFACER.", "Conferma mancante: digitare EFFACER."],
    "Format attendu : xlsx ou csv.": ["Expected format: xlsx or csv.", "Erwartetes Format: xlsx oder csv.", "Formato esperado: xlsx o csv.", "Formato atteso: xlsx o csv."],
    "Adresse e-mail invalide.": ["Invalid email address.", "Ungültige E-Mail-Adresse.", "Correo electrónico no válido.", "Indirizzo e-mail non valido."],
    "Rôle inconnu.": ["Unknown role.", "Unbekannte Rolle.", "Rol desconocido.", "Ruolo sconosciuto."],
    "Établissements inconnus : {codes}": ["Unknown hotels: {codes}", "Unbekannte Hotels: {codes}", "Establecimientos desconocidos: {codes}", "Strutture sconosciute: {codes}"],
    "Un directeur d'hôtel doit avoir au moins un établissement.": ["A hotel manager must have at least one hotel.", "Ein(e) Hoteldirektor(in) braucht mindestens ein Hotel.", "Un director de hotel debe tener al menos un establecimiento.", "Un direttore d'albergo deve avere almeno una struttura."],
    "Vous ne pouvez pas retirer votre propre rôle d'administrateur.": ["You cannot remove your own administrator role.", "Sie können Ihre eigene Administratorrolle nicht entfernen.", "No puede retirar su propio rol de administrador.", "Non può rimuovere il proprio ruolo di amministratore."],
    "Vous ne pouvez pas supprimer votre propre accès.": ["You cannot remove your own access.", "Sie können Ihren eigenen Zugriff nicht entfernen.", "No puede eliminar su propio acceso.", "Non può eliminare il proprio accesso."],
    "Utilisateur inconnu.": ["Unknown user.", "Unbekannte(r) Benutzer(in).", "Usuario desconocido.", "Utente sconosciuto."],
    "Endpoint inconnu.": ["Unknown endpoint.", "Unbekannter Endpunkt.", "Endpoint desconocido.", "Endpoint sconosciuto."],
    "Langue non prise en charge.": ["Language not supported.", "Sprache nicht unterstützt.", "Idioma no disponible.", "Lingua non supportata."],
    # --- Indicateurs et qualité
    "Non renseigné": ["Not specified", "Nicht angegeben", "Sin especificar", "Non indicato"],
    "Doublons potentiels (nom, prénom, date de naissance)": ["Possible duplicates (last name, first name, date of birth)", "Mögliche Duplikate (Nachname, Vorname, Geburtsdatum)", "Posibles duplicados (apellido, nombre, fecha de nacimiento)", "Possibili duplicati (cognome, nome, data di nascita)"],
    "Fiches incomplètes": ["Incomplete records", "Unvollständige Datensätze", "Fichas incompletas", "Schede incomplete"],
    "Actifs dont le contrat est terminé": ["Active employees whose contract has ended", "Aktive Personen mit beendetem Vertrag", "Activos cuyo contrato ha finalizado", "Attivi con contratto terminato"],
    "Actifs rattachés à un manager inactif ou absent": ["Active employees with an inactive or missing manager", "Aktive Personen mit inaktiver(m) oder fehlender(m) Vorgesetzten", "Activos con un responsable inactivo o ausente", "Attivi con responsabile inattivo o assente"],
    "Valeurs inconnues ou désactivées dans les référentiels": ["Unknown or deactivated reference values", "Unbekannte oder deaktivierte Referenzwerte", "Valores desconocidos o desactivados en las listas de referencia", "Valori sconosciuti o disattivati negli elenchi di riferimento"],
    "Adresses e-mail hors des domaines autorisés": ["Email addresses outside the allowed domains", "E-Mail-Adressen außerhalb der zulässigen Domains", "Correos fuera de los dominios autorizados", "Indirizzi e-mail fuori dai domini consentiti"],
    "Mêmes informations que : {autres}": ["Same details as: {autres}", "Gleiche Angaben wie: {autres}", "Mismos datos que: {autres}", "Stessi dati di: {autres}"],
    "Manquant : {champs}": ["Missing: {champs}", "Fehlt: {champs}", "Falta: {champs}", "Mancante: {champs}"],
    "Fin de contrat le {date}": ["Contract ended on {date}", "Vertragsende am {date}", "Fin de contrato el {date}", "Fine contratto il {date}"],
    "Manager supprimé de la base": ["Manager deleted from the database", "Vorgesetzte(r) aus der Datenbank gelöscht", "Responsable eliminado de la base", "Responsabile eliminato dalla banca dati"],
    "Manager inactif : {nom}": ["Inactive manager: {nom}", "Inaktive(r) Vorgesetzte(r): {nom}", "Responsable inactivo: {nom}", "Responsabile inattivo: {nom}"],
    "{type} « {code} » inconnu": ["{type} “{code}” unknown", "{type} „{code}“ unbekannt", "{type} «{code}» desconocido", "{type} «{code}» sconosciuto"],
    "{type} « {libelle} » désactivé": ["{type} “{libelle}” deactivated", "{type} „{libelle}“ deaktiviert", "{type} «{libelle}» desactivado", "{type} «{libelle}» disattivato"],
}
