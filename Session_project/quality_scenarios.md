# Quality Szenarios

Die Quality Szenarios beschreiben die nicht-funktionalen Eigenschaften von **ChatDoc** messbar. Sie folgen dem Schema aus arc42 bzw. Bass/Clements/Kazman:

| Teil | Bedeutung |
|---|---|
| **Quelle** | Wer oder was löst das Szenario aus |
| **Stimulus** | Das Ereignis |
| **Artefakt** | Betroffener Teil des Systems |
| **Umgebung** | Zustand bzw. Betriebsbedingungen |
| **Antwort** | Wie das System reagiert |
| **Antwortmaß** | Woran man prüft, ob das Szenario erfüllt ist |

Die Qualitätsmerkmale orientieren sich an ISO/IEC 25010. Die drei wichtigsten Qualitätsziele (siehe Canvas) sind **Nachvollziehbarkeit**, **Datenschutz** und **Deploybarkeit**.

## Übersicht

| ID | Qualitätsmerkmal | Kurzbeschreibung | Priorität | Umsetzung |
|---|---|---|---|---|
| QS-01 | Nachvollziehbarkeit (Funktionale Eignung) | Jede Antwort zeigt ihre Quellen | hoch | #12 |
| QS-02 | Funktionale Korrektheit | Ehrliches „weiß ich nicht“ bei fehlendem Wissen | hoch | #10 |
| QS-03 | Sicherheit / Datenschutz | Keine Daten verlassen das Gerät | hoch | Architektur |
| QS-04 | Übertragbarkeit / Deploybarkeit | Start mit einem Befehl auf frischem System | hoch | #15 |
| QS-05 | Zuverlässigkeit / Persistenz | Chatverlauf übersteht Neustarts | mittel | #13 |
| QS-06 | Performance | Antwort beginnt schnell | mittel | #10 |
| QS-07 | Wartbarkeit / Änderbarkeit | Modellwechsel ohne Codeänderung | mittel | #10, #15 |
| QS-08 | Zuverlässigkeit / Fehlertoleranz | Ausfall von Ollama führt nicht zum Absturz | mittel | #10 |
| QS-09 | Benutzbarkeit | Erste Frage ohne Anleitung | mittel | #10 |
| QS-10 | Wartbarkeit / Analysierbarkeit | Schlechte Antworten sind auswertbar | niedrig | #14 |

---

## QS-01 – Quellen sind nachvollziehbar
| | |
|---|---|
| **Quelle** | Studentin (P1) |
| **Stimulus** | stellt eine Frage zum Buch |
| **Artefakt** | Chatbot-UI, RAG-Chain |
| **Umgebung** | Normalbetrieb |
| **Antwort** | Unter der Antwort werden die abgerufenen Chunks mit Seitenzahl angezeigt |
| **Antwortmaß** | 100 % der Antworten haben einen Bereich „Sources“ mit Seitenzahl; die Seitenzahl stimmt mit dem PDF überein |

## QS-02 – Kein Halluzinieren bei fehlendem Wissen
| | |
|---|---|
| **Quelle** | Studentin (P1) |
| **Stimulus** | fragt etwas, das nicht im Buch steht (z. B. „Wer hat die Fußball-WM 2014 gewonnen?“) |
| **Artefakt** | Prompt der RAG-Chain |
| **Umgebung** | Normalbetrieb, Modell `llama3.2:1b` |
| **Antwort** | Der Chatbot sagt, dass er die Antwort im Dokument nicht findet |
| **Antwortmaß** | Bei 10 buchfremden Testfragen antwortet der Chatbot in mindestens 8 Fällen mit „I don't know“ o. ä. |

## QS-03 – Daten bleiben lokal
| | |
|---|---|
| **Quelle** | Dozentin (P3), Datenschutzbeauftragte |
| **Stimulus** | prüft, wohin Fragen und Antworten übertragen werden |
| **Artefakt** | Gesamtsystem (Chatbot, Ollama, ChromaDB, SQLite) |
| **Umgebung** | Normalbetrieb nach dem ersten Start (Modelle geladen) |
| **Antwort** | Alle Komponenten laufen als Container auf dem Gerät, die Kommunikation läuft nur im Docker-Netz `app-network` |
| **Antwortmaß** | 0 Anfragen an externe Server während einer Chat-Sitzung (prüfbar mit getrenntem Netzwerk: der Chatbot funktioniert weiter) |

## QS-04 – Start mit einem Befehl
| | |
|---|---|
| **Quelle** | Laboringenieur (P4) |
| **Stimulus** | führt `docker compose up --build` auf einem frischen Rechner aus |
| **Artefakt** | `docker-compose.yml`, `Dockerfile`, Initialisierung des Chatbots |
| **Umgebung** | Docker installiert, Internetzugang beim ersten Start, leerer `container_cache` |
| **Antwort** | Images werden gebaut, Modelle geladen, das Buch indexiert, danach ist die UI erreichbar |
| **Antwortmaß** | 1 Befehl, 0 manuelle Zwischenschritte; Linux/Windows/macOS (`docker-compose.yml`) und Jetson (`docker-compose-jetson.yml`) |

## QS-05 – Chatverlauf übersteht Neustarts
| | |
|---|---|
| **Quelle** | Studentin (P1) |
| **Stimulus** | lädt die Seite neu bzw. der Rechner wird neu gestartet (`docker compose down` / `up`) |
| **Artefakt** | SQLite-Datenbank `chatbot.db` im Volume `container_cache/sqlite` |
| **Umgebung** | nach einem Neustart der Container |
| **Antwort** | Alle Chats, Nachrichten, Quellen und Bewertungen sind wieder da |
| **Antwortmaß** | 100 % der gespeicherten Nachrichten sind nach dem Neustart vorhanden |

## QS-06 – Antwort beginnt schnell
| | |
|---|---|
| **Quelle** | Studentin (P1) |
| **Stimulus** | sendet eine Frage |
| **Artefakt** | Retriever (ChromaDB), LLM (Ollama) |
| **Umgebung** | Jetson Orin Nano mit GPU, Modell `llama3.2:1b`, Modelle bereits geladen |
| **Antwort** | Die Antwort wird gestreamt |
| **Antwortmaß** | Retrieval < 2 s, erstes Token < 10 s, vollständige Antwort (≤ 3 Sätze) < 30 s |

## QS-07 – Modellwechsel ohne Codeänderung
| | |
|---|---|
| **Quelle** | Dozentin (P3) |
| **Stimulus** | möchte `llama3.2:3b` statt `llama3.2:1b` verwenden |
| **Artefakt** | Konfiguration in `docker-compose.yml` |
| **Umgebung** | Entwicklung / Betrieb |
| **Antwort** | `MODEL_NAME` wird geändert, beim Neustart wird das Modell automatisch geladen |
| **Antwortmaß** | 1 geänderte Zeile, 0 Codeänderungen, Umstellung < 5 Minuten (ohne Download-Zeit) |

## QS-08 – Fehlertoleranz bei Ausfall des LLM
| | |
|---|---|
| **Quelle** | Betrieb |
| **Stimulus** | der Ollama-Container ist während einer Anfrage nicht erreichbar |
| **Artefakt** | Chatbot-UI (`main.py`) |
| **Umgebung** | Fehlerfall |
| **Antwort** | Die UI zeigt eine verständliche Fehlermeldung, die App läuft weiter, die Frage bleibt im Verlauf |
| **Antwortmaß** | Kein Absturz der Streamlit-App; nach dem Neustart von Ollama funktioniert die nächste Frage ohne Neustart des Chatbots |

## QS-09 – Bedienung ohne Anleitung
| | |
|---|---|
| **Quelle** | neue Studentin (P1) |
| **Stimulus** | öffnet ChatDoc zum ersten Mal |
| **Artefakt** | Streamlit-UI |
| **Umgebung** | Normalbetrieb |
| **Antwort** | Eingabefeld, Begrüßung und Seitenleiste sind selbsterklärend |
| **Antwortmaß** | Erste Frage gestellt innerhalb von 1 Minute, ohne Anleitung (Test mit 3 Personen) |

## QS-10 – Schlechte Antworten sind auswertbar
| | |
|---|---|
| **Quelle** | Dozentin (P3) |
| **Stimulus** | möchte wissen, welche Fragen schlecht beantwortet wurden |
| **Artefakt** | Tabelle `feedback` in SQLite, Seitenleiste |
| **Umgebung** | Normalbetrieb nach einigen Tagen Nutzung |
| **Antwort** | Statistik 👍/👎 und Liste der negativ bewerteten Fragen mit Antwort |
| **Antwortmaß** | Jede 👎-Bewertung ist mit Frage und Antwort per SQL-Abfrage auffindbar |
