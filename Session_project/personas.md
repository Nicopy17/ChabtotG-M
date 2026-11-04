# Personas

Die Personas beschreiben die typischen Nutzer:innen unseres Chatbots **ChatDoc**. ChatDoc beantwortet Fragen zum Lehrbuch (`AI_Book.pdf`) per Retrieval-Augmented Generation (RAG) und läuft komplett lokal auf einem NVIDIA Jetson Orin Nano bzw. einem PC mit Docker.

Die User Stories in [user_stories.md](user_stories.md) verweisen auf diese Personas.

---

## P1 – Lena, die Prüfungslernende

| | |
|---|---|
| **Alter** | 21 |
| **Rolle** | Studentin Wirtschaftsinformatik, 3. Semester |
| **Technikaffinität** | mittel: nutzt Apps und Browser sicher, programmiert wenig |
| **Nutzungskontext** | lernt abends und am Wochenende für die Klausur „Grundlagen KI“, meist am Laptop im Browser |

**Ziele**
- Begriffe aus dem Buch schnell und verständlich erklärt bekommen („Was ist Overfitting?“)
- Sicher sein, dass die Antwort wirklich aus dem Buch kommt und nicht erfunden ist
- An einer Lerneinheit vom Vortag weiterarbeiten

**Frustrationen**
- Allgemeine Chatbots erfinden Antworten, die nicht zum Vorlesungsstoff passen
- Sie findet die passende Stelle im 500-seitigen Buch nicht
- Chatverläufe sind nach dem Schließen des Browsers weg

**Zitat**
> „Ich will nicht nur eine Antwort, ich will wissen, auf welcher Seite das steht, damit ich es nachlesen kann.“

---

## P2 – Jonas, der Tutor

| | |
|---|---|
| **Alter** | 24 |
| **Rolle** | Master-Student Informatik, Tutor für das Labor „Build your own Chatbot“ |
| **Technikaffinität** | hoch: Python, Docker, Git |
| **Nutzungskontext** | bereitet Tutorien vor, stellt viele Folgefragen hintereinander |

**Ziele**
- Mehrstufige Fragen stellen („Was ist supervised learning?“ → „Welche Algorithmen gibt es dort?“)
- Die abgerufenen Textstellen prüfen, um schlechte Antworten zu erklären
- Rückmelden, welche Antworten falsch waren

**Frustrationen**
- Folgefragen werden ohne Kontext missverstanden
- Er kann nicht erkennen, ob ein Fehler am Retrieval oder am LLM liegt

**Zitat**
> „Wenn die Antwort falsch ist, will ich sehen, welche Chunks das Modell bekommen hat.“

---

## P3 – Prof. Dr. Weber, die Dozentin

| | |
|---|---|
| **Alter** | 52 |
| **Rolle** | Professorin, verantwortlich für Vorlesung und Labor |
| **Technikaffinität** | mittel bis hoch |
| **Nutzungskontext** | stellt den Chatbot den Studierenden bereit und wertet die Qualität aus |

**Ziele**
- Die Studierenden sollen Fragen zum Lehrbuch stellen können, ohne dass Daten an externe Cloud-Dienste gehen (Datenschutz)
- Sehen, welche Fragen schlecht beantwortet werden, um Material oder Konfiguration zu verbessern
- Ein anderes oder größeres Modell testen, ohne Code anzupassen

**Frustrationen**
- Cloud-Chatbots sind aus Datenschutzgründen an der Hochschule nur eingeschränkt erlaubt
- Ohne Feedback der Studierenden weiß sie nicht, ob das Werkzeug hilft

**Zitat**
> „Ich muss wissen, wo der Chatbot danebenliegt, sonst kann ich ihn nicht guten Gewissens einsetzen.“

---

## P4 – Tim, der Laboringenieur

| | |
|---|---|
| **Alter** | 35 |
| **Rolle** | Laboringenieur im Digital Engineering Lab |
| **Technikaffinität** | sehr hoch: Linux, Docker, Jetson |
| **Nutzungskontext** | setzt die Labor-PCs (Jetson Orin Nano) vor jedem Semester neu auf |

**Ziele**
- Den Chatbot mit einem einzigen Befehl (`docker compose up`) starten
- Keine manuellen Schritte wie Modelle laden oder Buch indexieren
- Daten (Index, Chatverlauf) sollen einen Neustart überstehen

**Frustrationen**
- Lange Installationsanleitungen mit vielen Einzelschritten
- Container, die nach einem Neustart wieder bei null anfangen

**Zitat**
> „Wenn ich mehr als einen Befehl brauche, mache ich das bei 20 Rechnern nicht.“
