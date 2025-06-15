**Funktionell Specifikation / Projektplan: Kameo Budgivningsautomation**

**(Version 1.0 - Baserad på befintliga anteckningar)**

**1. Introduktion och Syfte**

- **Projekt:** Kameo Budgivningsautomation
- **Syfte:** Att skapa ett automatiserat system (en "bot") som hanterar hela processen för att lägga bud på lån på peer-to-peer-låneplattformen Kameo. Målet är att effektivisera investeringsprocessen genom att automatiskt identifiera och bjuda på lämpliga lån baserat på fördefinierade kriterier och vid rätt tidpunkt.
- **Målgrupp för detta dokument:** Utvecklare som ska (vidare)utveckla och färdigställa applikationen. Dokumentet beskriver den tänkta funktionaliteten i det färdiga systemet.
- **Målgrupp för applikationen:** Användare (initialt projektägaren) som vill automatisera sina investeringar på Kameo.

**2. Övergripande Arkitektur (Färdigt Läge)**

Systemet ska bestå av två huvuddelar:

- **Backend (Python):** Kärnan i systemet som hanterar all logik för webbinteraktion, datainsamling, autentisering och budgivning. Den ska vara modulärt uppbyggd med tydlig separation av ansvar  
- **Frontend (Webbapplikation - Valfritt men rekommenderat):** Ett användargränssnitt som kommunicerar med backend via ett API. Detta gränssnitt ska möjliggöra enkel konfiguration, övervakning i realtid, manuell kontroll och rapportering.

**3. Kärnfunktioner (Detaljerad Beskrivning av Färdig App)**

När applikationen är produktionsklar ska den kunna utföra följande:

- **3.1 Konfiguration:**

  - **Centraliserad Hantering:** All konfiguration (inloggningsuppgifter, OTP-nyckel, budparametrar, URL:er, timeouts, loggnivåer etc.) ska hanteras centralt, primärt via miljövariabler för säkerhet och flexibilitet. Undvik hårdkodade värden.
  - **Säkerhet:** Känslig information (lösenord, OTP-nyckel) ska hanteras säkert (t.ex. via miljövariabler eller en säker konfigurationshanterare, _inte_ hårdkodat eller i klartext i källkoden).
  - **(Frontend):** Ett gränssnitt för att enkelt kunna se och (eventuellt, med försiktighet) modifiera vissa konfigurationsparametrar (t.ex. standardbudbelopp, filterkriterier).

- **3.2 Autentisering och Sessionshantering:**

  - **Automatisk Inloggning:** Systemet ska kunna logga in på Kameo med användarnamn och lösenord.
  - **2FA/OTP-hantering:** Systemet ska hantera tvåfaktorsautentisering (Google Authenticator/annan lösning) automatiskt med den konfigurerade OTP-nyckeln.
  - **Cookie-hantering:** Spara och återanvända sessionscookies för att bibehålla inloggningen mellan körningar och minimera antalet fulla inloggningar. Hantera cookie consent-popups automatiskt.
  - **Sessionsvalidering:** Innan en operation påbörjas, verifiera att sessionen är giltig (kontrollera t.ex. specifik cookie eller sidinnehåll). Om sessionen är ogiltig, initiera en ny inloggningsprocess automatiskt.
  - **Felhantering vid Inloggning:** Upptäcka och logga specifika inloggningsfel (t.ex. "Fel lösenord", "Fel användarnamn") baserat på felmeddelanden på sidan.

- **3.3 Datainsamling (Lån):**

  - **Identifiering av Lån:** Automatiskt navigera till Kameos marknadsplats/lista över lån.
  - **Extrahering av Data:** Samla in relevant information om tillgängliga/kommande lån (t.ex. titel, beskrivning, ränta, lånebelopp, återstående belopp, öppningstid, deadline, status).
  - **Lagring (Rekommenderat):** Spara insamlad lånedata i en databas (PostgreSQL) för historik, analys och för att undvika upprepad insamling.
  - **(Frontend):** Visa en lista över insamlade/kommande lån med deras status.

- **3.3.1 Temporär Datalagring:**

  - **JSON-filslagring:** Initialt sparas all insamlad data i JSON-filer med tydlig struktur som speglar framtida databasschema.
    - Separata JSON-filer för olika datatyper (lån, budhistorik, etc.).
    - Filnamn innehåller datum/timestamp för enkel spårning.
  
  - **Förberedd för Databasmigrering:**
    - Datastrukturer designade för enkel överföring till PostgreSQL.
    - Använd Pydantic-modeller för datavalidering och serialisering.
    - Implementera abstrakta gränssnitt/interfaces för dataåtkomst.
    - Separera datahanterings-logik från affärslogik.

  - **Planerad Databasstruktur:**
    - Spara datan i Bulk men i sektioner baserat på vart infon kom ifrån.
    - Logiskt separera den sparade datan

  - **Migreringsstrategi:**
    - Kod strukturerad för enkel övergång till PostgreSQL.
    - Datamodeller kompatibla med SQLAlchemy/annat ORM.
    - Möjlighet att migrera historisk JSON-data till databas.

- **3.4 Budgivningsprocess:**

  - **Automatisk Start:** Processen ska kunna startas antingen manuellt eller automatiskt vid en schemalagd tidpunkt (t.ex. strax innan ett specifikt lån öppnar för budgivning).
  - **Förkontroller (Pre-bid Checks):** För varje potentiellt lån (som matchar filterkriterier):
    - Navigera till den specifika lånesidan (via dess unika URL).
    - Verifiera att lånet är öppet för budgivning.
    - Verifiera att lånet inte redan är fulltecknat.
    - Verifiera att användaren inte redan har lagt ett bud på detta lån.
    - Om någon kontroll misslyckas, avbryt för detta lån och gå vidare till nästa (eller logga och avsluta om det bara var ett lån).
  - **Budplacering:**
    - Navigera till/aktivera budformuläret på lånesidan.
    - Verifiera tillgängligt saldo på Kameo-kontot.
    - Fyll i budformuläret med det konfigurerade/beräknade budbeloppet (ta hänsyn till maxbelopp, tillgängligt saldo, eventuell strategi).
    - Skicka in budet.
    - Hantera eventuella bekräftelsesteg (klicka på bekräfta-knapp).
  - **Verifiering efter Bud:**
    - Efter att budet skickats och bekräftats, verifiera att budet faktiskt har registrerats (t.ex. genom att leta efter texten "Ditt bud" eller liknande på sidan, samma kontroll som i punkt 3.4 Förkontroller).
  - **Datainsamling efter Bud:** Hämta och logga/spara detaljer om det lagda budet (belopp, ränta, status "Anbudsprocess pågår", återstående saldo på kontot).
  - **Budstrategier (Framtida):** Systemet ska vara byggt så att olika budstrategier kan implementeras (t.ex. fast belopp, procent av totalbelopp, dynamiskt baserat på återstående tid/belopp). Användning av Strategy Pattern rekommenderas.

- **3.5 Schemaläggning:**

  - Systemet ska kunna konfigureras att automatiskt köra datainsamling och/eller budgivningsprocessen vid specifika tider (t.ex. dagligen för att hitta nya lån, eller exakt när ett visst lån öppnar). Detta kan hanteras externt (t.ex. cronjob) eller internt i applikationen.

- **3.6 Felhantering och Loggning:**

  - **Robust Felhantering:** Använda try-except block för att fånga förväntade och oväntade fel under webbinteraktion (TimeoutException, NoSuchElementException etc.).
  - **Retry-mekanism:** Implementera en flexibel retry-mekanism (t.ex. via en decorator) för kritiska operationer som kan misslyckas intermittent (t.ex. klicka på knappar, ladda sidor). Konfigurerbart antal försök och fördröjning.
  - **Detaljerad Loggning:** Använda ett bibliotek som Loguru för att logga detaljerad information om systemets körning, inklusive DEBUG-nivå för felsökning. Skapa separata loggfiler för olika körningar eller dagar.
  - **Specifika Loggers (Valfritt):** Möjlighet att ha specifika loggers för olika moduler, som kan aktiveras vid behov.
  - **Skärmdumpar/HTML vid Fel:** Vid kritiska fel, spara automatiskt en skärmdump och/eller HTML-källkoden för den aktuella sidan för att underlätta felsökning.
  - **(Frontend):** Visa viktiga loggmeddelanden och statusuppdateringar. Implementera ett notifikationssystem för viktiga händelser (lyckat bud, kritiskt fel).

- **3.7 Användargränssnitt och API (TBD):**
    - Skall implementeras och skapas. 
    - Skall förberedas för att bli implementerat i framtiden. 

**4. Tekniska Förutsättningar / Stack (Baserat på befintlig kod och förslag)**

- **Backend:** Python 3.x
- **Loggning:** Loguru
- **Konfiguration:** python-dotenv (för .env-filer), miljövariabler
- **Databas (Rekommenderat):** PostgreSQL
- **Beroenden:** Hanteras via `requirements.txt`

**5. Vision: Användarupplevelse (Readme/FAQ-känsla)**

När systemet är klart ska en användare (via det tänkta GUI) kunna:

1.  **Logga in** säkert i administrationsgränssnittet.
2.  **Konfigurera** sina Kameo-inloggningsuppgifter, OTP-nyckel och grundläggande budparametrar (t.ex. standardbelopp, max exponering per lån, ev. filter för ränta/typ).
3.  **Övervaka** systemets status på en dashboard: Är boten igång? Är den inloggad på Kameo? Vilket är nuvarande saldo? Vilka lån bevakas/har nyligen bearbetats?
4.  **Se en lista** över kommande och pågående lån som systemet har identifierat.
5.  **Starta/Stoppa** den automatiska budgivningsprocessen.
6.  **Få notiser** om viktiga händelser (t.ex. "Bud på 2000 SEK lagt på Lån X", "Kritiskt fel: Kunde inte logga in").
7.  **Se en historik** över lagda bud och deras resultat (när detta blir tillgängligt från Kameo).
8.  **(Avancerat):** Se enkel **analys** av budgivningsframgång och avkastning.

Systemet ska i bakgrunden sköta inloggning, sessionshantering, datainsamling och budgivning enligt konfigurationen, med robust felhantering och loggning.

