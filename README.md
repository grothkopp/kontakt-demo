# kontakt.

Dieses Demo-Repository begleitet den Kurs **Quality & Observability im Agentic Engineering**
von **Stefan Grothkopp** bei der [Digitale Leute School](https://school.digitale-leute.de/).
An einer kleinen Kontaktverwaltung verbessern wir im Workshop einen Pull Request schrittweise:
mit klaren Anforderungen, automatischen Tests, CI-Workflows, Evals und Code-Reviews.

- [Digitale Leute](https://www.digitale-leute.de/)
- [Stefan Grothkopp – Homepage](https://grothkopp.com/)
- [Stefan Grothkopp auf LinkedIn](https://www.linkedin.com/in/grothkopp/)

Die Anwendung ist bewusst einfach gehalten und dient als Ausgangslage für die Kursübungen.

Python 3.13, Django 5.2 LTS, SQLite und uv. Keine JavaScript-Abhängigkeiten, kein Frontend-Build,
keine externen Schriften oder Dienste.

## Starten

Im Verzeichnis dieses Repositories:

```sh
uv sync --locked
uv run python manage.py migrate
uv run python manage.py loaddata demo
uv run python manage.py runserver
```

Öffne http://127.0.0.1:8000/.

Innerhalb des Obsidian-Workspaces kann die Umgebung außerhalb des Vaults liegen,
damit dessen Strukturprüfung keine Python-Symlinks beanstandet. Dazu vor den obigen
Befehlen setzen (in dieser Sitzung verwendet):

```sh
export UV_PROJECT_ENVIRONMENT=/tmp/dl-contact-demo-venv
```

Nach einem Neustart kann `/tmp` leer sein; `uv sync --locked` erstellt die Umgebung erneut.
Außerhalb des Vaults ist die normale `.venv` ausreichend.

| Benutzername | Passwort | Kontakte | Davon Kunden |
| --- | --- | ---: | ---: |
| anna | Workshop-2026! | 3 | 1 |
| ben | Workshop-2026! | 3 | 2 |

Die Demo-Zugangsdaten sind absichtlich öffentlich und werden auch auf der Loginseite angezeigt.
Beide Nutzer sind gewöhnliche Django-Nutzer ohne Adminrechte. Alle Personen und Daten sind fiktiv.
Das Projekt ist für lokalen Workshopbetrieb gedacht; die Einstellungen sind keine Produktionskonfiguration.

## Was funktioniert?

- Anmeldung mit Django LoginView und Abmeldung per CSRF-geschütztem POST.
- Kontaktliste, Tags und Notizen aus SQLite, strikt auf den angemeldeten Nutzer begrenzt.
- Zähler für Kontakte, Unternehmen und Kunden aus den tatsächlich sichtbaren Daten.
- Responsive Oberfläche mit lokalem CSS und leerem Zustand für Konten ohne Kontakte.

Es gibt noch keinen Tag-Filter, keine Bearbeitung oder Neuanlage, keine REST-API, keine CI
und keine E2E-Suite. Die Tags sind Labels. Diese Baseline enthält keine absichtlich eingebauten
Fehler. Das Filterfeature kann später in einem eigenen PR entwickelt werden.

## Daten und Neustart

Die Schema-Migration liegt in `contacts/migrations/`. Die Fixture `contacts/fixtures/demo.json`
enthält zwei Nutzer mit gehashten Passwörtern und sechs Kontakte. Das Laden erfolgt bewusst
separat von `migrate`, damit die Demo-Konten nicht ungefragt in jeder Datenbank angelegt werden.

`uv run python manage.py loaddata demo` stellt die Fixture-Datensätze wieder her. Das überschreibt
auch die Passwörter der beiden Demo-Konten, löscht aber keine zusätzlich angelegten Datensätze.
Für einen vollständigen lokalen Neustart: Server stoppen, die lokale Datei `db.sqlite3` entfernen,
danach Migrationen und Fixture erneut laden.

SQLite-Datei, virtuelle Umgebung und der automatisch erzeugte lokale Django-Schlüssel bleiben
außerhalb von Git. Der Schlüssel bleibt über Serverneustarts stabil.

## Prüfen

```sh
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py test
```

Fünf Basistests prüfen Loginpflicht, Nutzertrennung, echten Login/Logout mit CSRF, ungültige
Zugangsdaten und externe Weiterleitungen sowie den leeren Zustand. Keine GitHub-Workflows
vorinstalliert: deren Aufbau bleibt Teil des Workshops.

## Orientierung

- `contacts/models.py`: ein Contact-Modell, ein Tag pro Kontakt.
- `contacts/views.py`: eine geschützte Listenansicht.
- `config/urls.py`: Liste, Login und Logout.
- `templates/`: Basislayout und zwei Seiten.
- `static/app.css`: das gesamte Styling.
- `contacts/fixtures/demo.json`: wiederholbar ladbare Demodaten.

## Repository

[grothkopp/kontakt-demo auf GitHub](https://github.com/grothkopp/kontakt-demo)

```sh
git clone https://github.com/grothkopp/kontakt-demo.git
cd kontakt-demo
```

Danach die Schritte unter **Starten** ausführen. Die bewusst öffentlichen Fixture-Zugangsdaten
sind keine Zugangsdaten zu einem realen Dienst.

## Browser-Tests (Workshop-Backup)

```sh
uv sync --locked --group e2e
uv run --group e2e python -m playwright install chromium
uv run --group e2e python manage.py test e2e.browser_tests
# Optional mit sichtbarem Browser:
HEADED=1 uv run --group e2e python manage.py test e2e.browser_tests
```

Django startet selbst einen Testserver mit separater Testdatenbank und Fixtures.
Kein laufender Entwicklungsserver und kein manuelles Laden der Daten nötig.
`uv run manage.py test` führt weiterhin nur die schnellen Django-Tests aus.
Unter Linux installiert `playwright install --with-deps chromium` auch Systempakete.

Auf dem unveränderten Filter-Stand schlagen zwei Browser-Tests absichtlich aufgrund
der bestehenden Anwendungsfehler fehl; Login/Logout und ungefilterte Nutzertrennung
bestehen. Nach Korrektur der Anwendung sollen alle vier Tests grün sein.
Die GitHub Action führt dieselben Tests aus und lädt Traces auch bei Fehlern hoch.
Traces liegen lokal unter `output/playwright/`; öffnen mit:

```sh
uv run --group e2e python -m playwright show-trace output/playwright/test_filtered_count_and_reset.zip
```

Die Suite enthält nur synthetische Daten. Traces nicht mit echten Kontaktdaten teilen.
