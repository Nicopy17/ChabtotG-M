# User Stories

Format: *Als &lt;Persona&gt; möchte ich &lt;Funktion&gt;, damit &lt;Nutzen&gt;.*
Die Personas sind in [personas.md](personas.md) beschrieben, die nicht-funktionalen Anforderungen in [quality_scenarios.md](quality_scenarios.md).
Jede Story ist einem GitHub-Issue und einem Branch zugeordnet.

| ID | Kurzname | Persona | Priorität | Issue | Branch |
|---|---|---|---|---|---|
| US-01 | Frage zum Buch stellen | P1 Lena | Must | #10 | `session-5` |
| US-02 | Antwort live mitlesen | P1 Lena | Should | #10 | `session-5` |
| US-03 | Quellen der Antwort sehen | P1 Lena, P2 Jonas | Must | #12 | `feature/quellen-anzeigen` |
| US-04 | Chatverlauf bleibt erhalten | P1 Lena | Must | #13 | `feature/chatverlauf-sql` |
| US-05 | Frühere Chats verwalten | P1 Lena | Should | #13 | `feature/chatverlauf-sql` |
| US-06 | Folgefragen stellen | P2 Jonas | Should | #13 | `feature/chatverlauf-sql` |
| US-07 | Antwort bewerten | P2 Jonas | Must | #14 | `feature/antwort-feedback` |
| US-08 | Schlechte Antworten auswerten | P3 Prof. Weber | Should | #14 | `feature/antwort-feedback` |
| US-09 | Ganzes Buch durchsuchbar | P1 Lena | Must | #15 | `feature/vollstaendige-indexierung` |
| US-10 | Start mit einem Befehl | P4 Tim | Must | #15 | `feature/vollstaendige-indexierung` |
| US-11 | Modell per Konfiguration wechseln | P3 Prof. Weber | Could | #10 | `session-5` |

---

## US-01 – Frage zum Buch stellen
**Als** Studentin (P1) **möchte ich** im Browser eine Frage zum Lehrbuch stellen, **damit** ich Begriffe schnell erklärt bekomme, ohne das Buch zu durchsuchen.

**Akzeptanzkriterien**
- Die Weboberfläche ist unter `http://localhost:5001` erreichbar.
- Die Antwort basiert auf den Textstellen, die aus ChromaDB abgerufen wurden (RAG).
- Steht die Antwort nicht im Kontext, sagt der Chatbot, dass er es nicht weiß.

## US-02 – Antwort live mitlesen
**Als** Studentin (P1) **möchte ich** die Antwort Wort für Wort entstehen sehen, **damit** ich nicht vor einem leeren Bildschirm warte.

**Akzeptanzkriterien**
- Die Antwort wird gestreamt (`astream_events`, Event `on_chat_model_stream`).
- Während der Suche zeigt die Oberfläche einen Lade-Hinweis.

## US-03 – Quellen der Antwort sehen
**Als** Studentin (P1) bzw. Tutor (P2) **möchte ich** zu jeder Antwort die verwendeten Textstellen mit Seitenzahl sehen, **damit** ich die Antwort im Buch nachprüfen und Fehler im Retrieval erkennen kann.

**Akzeptanzkriterien**
- Unter jeder Antwort gibt es einen aufklappbaren Bereich „Sources“.
- Jede Quelle zeigt die Seitenzahl im PDF und den Textauszug.
- Die Quellen bleiben auch in älteren Nachrichten sichtbar.

## US-04 – Chatverlauf bleibt erhalten
**Als** Studentin (P1) **möchte ich**, dass mein Chatverlauf gespeichert wird, **damit** ich nach einem Neuladen oder am nächsten Tag weiterlernen kann.

**Akzeptanzkriterien**
- Alle Fragen und Antworten werden in der SQL-Datenbank (SQLite, Tabellen `conversations` und `messages`) gespeichert.
- Nach einem Neuladen der Seite und nach einem Neustart der Container ist der Verlauf noch vorhanden.

## US-05 – Frühere Chats verwalten
**Als** Studentin (P1) **möchte ich** in der Seitenleiste neue Chats anlegen, alte öffnen und löschen, **damit** ich Themen getrennt halten kann.

**Akzeptanzkriterien**
- Button „New chat“ startet einen leeren Chat.
- Frühere Chats sind mit ihrer ersten Frage als Titel auswählbar (neueste zuerst).
- „Delete this chat“ löscht den Chat inklusive Nachrichten und Feedback.

## US-06 – Folgefragen stellen
**Als** Tutor (P2) **möchte ich** Folgefragen stellen können, die sich auf die vorherige Antwort beziehen, **damit** ich ein Thema Schritt für Schritt vertiefen kann.

**Akzeptanzkriterien**
- Die letzten Nachrichten des Chats werden als Verlauf an das LLM übergeben.
- Für die Suche in ChromaDB wird die vorherige Frage mit einbezogen.
- Beispiel: „What is supervised learning?“ → „Which algorithms can be used there?“ liefert Algorithmen des Supervised Learning.

## US-07 – Antwort bewerten
**Als** Tutor (P2) **möchte ich** jede Antwort mit 👍 oder 👎 bewerten, **damit** schlechte Antworten erkannt werden.

**Akzeptanzkriterien**
- Unter jeder gespeicherten Antwort gibt es 👍/👎.
- Die Bewertung wird in der Tabelle `feedback` gespeichert und kann geändert oder zurückgenommen werden.

## US-08 – Schlechte Antworten auswerten
**Als** Dozentin (P3) **möchte ich** sehen, wie viele Antworten gut oder schlecht bewertet wurden und welche Fragen schlecht beantwortet wurden, **damit** ich Prompt, Chunking oder Modell gezielt verbessern kann.

**Akzeptanzkriterien**
- Die Seitenleiste zeigt die Anzahl 👍 und 👎.
- Die letzten 👎-Antworten werden mit der zugehörigen Frage angezeigt.

## US-09 – Ganzes Buch durchsuchbar
**Als** Studentin (P1) **möchte ich**, dass der Chatbot das komplette Buch kennt, **damit** er auch Fragen zu späteren Kapiteln beantworten kann.

**Akzeptanzkriterien**
- Alle Chunks des Buchs (ca. 1.270 bei `chunk_size=1000`) sind in ChromaDB.
- Mehrfaches Indexieren erzeugt keine Duplikate.

## US-10 – Start mit einem Befehl
**Als** Laboringenieur (P4) **möchte ich** den Chatbot mit `docker compose up --build` starten, **damit** ich ihn ohne manuelle Schritte auf vielen Rechnern bereitstellen kann.

**Akzeptanzkriterien**
- LLM und Embedding-Modell werden beim ersten Start automatisch geladen.
- Eine leere Vektordatenbank wird beim ersten Start automatisch gefüllt.
- Der Chatbot wartet, bis Ollama und ChromaDB bereit sind (Healthchecks).

## US-11 – Modell per Konfiguration wechseln
**Als** Dozentin (P3) **möchte ich** das LLM über eine Umgebungsvariable wechseln, **damit** ich größere Modelle testen kann, ohne Code zu ändern.

**Akzeptanzkriterien**
- `MODEL_NAME` in `docker-compose.yml` bestimmt das Modell (z. B. `llama3.2:3b`).
- Das Modell wird beim Start automatisch geladen.
