# Kameo Bot – Enkel Användarguide

Välkommen! Den här guiden hjälper dig att snabbt komma igång med Kameo Bot, steg för steg. Du behöver inga förkunskaper om programmering.

---

## 1. Installera programmet

1. **Ladda ner projektet**
   - Be någon skicka dig mappen, eller ladda ner från internet (t.ex. GitHub).

2. **Öppna en terminal**
   - På Mac: Sök efter "Terminal" i Spotlight.
   - På Windows: Sök efter "Kommandotolken" eller "PowerShell".

3. **Gå till projektmappen**
   - Skriv `cd` följt av sökvägen till mappen, t.ex.:
     ```bash
     cd Sökväg/till/kameoBotRebuild
     ```

4. **Skapa en virtuell miljö (frivilligt men rekommenderas)**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # På Windows: .venv\Scripts\activate
   ```

5. **Installera nödvändiga program**
   ```bash
   pip install -r requirements.txt
   ```

---

## 2. Ställ in dina uppgifter

1. **Kopiera exempel-filen för inställningar**
   ```bash
   cp .env.example .env
   ```

2. **Öppna `.env`-filen**
   - Fyll i din e-post och ditt lösenord till Kameo.
   - Spara filen.

---

## 3. Använd programmet

### Vanliga kommandon

- **Samla in lån och spara i databasen:**
  ```bash
  python -m src.cli loans fetch
  ```

- **Visa statistik om lån:**
  ```bash
  python -m src.cli loans stats
  ```

- **Lista tillgängliga lån för budgivning:**
  ```bash
  python -m src.cli bidding list
  ```

- **Lägga bud på ett lån:**
  ```bash
  python -m src.cli bidding bid <lånets_id> <belopp>
  ```
  _Exempel:_
  ```bash
  python -m src.cli bidding bid 1234 5000
  ```

- **Kör en demo:**
  ```bash
  python -m src.cli demo
  ```

---

## 4. Felsökning

- Om du får felmeddelanden, kontrollera att:
  - Du har fyllt i rätt e-post och lösenord i `.env`-filen.
  - Du har internetanslutning.
  - Du har installerat alla program med `pip install -r requirements.txt`.

Behöver du mer hjälp? Fråga någon med mer datorvana eller kontakta projektets utvecklare.

---

**Klart! Nu kan du använda Kameo Bot för att samla in och analysera lån.** 