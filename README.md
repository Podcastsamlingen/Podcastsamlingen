# Mine fire danske podcasts – automatisk RSS

Dette projekt samler **CEPOS Bag om Nyhederne, Borgerlig Tabloid, Liberal Alliance og Supertrends** i ét podcast-feed. Afsnittene sorteres efter **oprindelig publiceringsdato**, og der laves et nyt feed **hver tredje time** via GitHub Actions.

## Opsætning (gratis offentlig GitHub-konto)

1. Opret en gratis konto på https://github.com/signup.
2. Vælg **New repository** på https://github.com/new. Kald det præcis `podcast-github`, vælg **Public**, og opret repository.
3. Upload **`build_feed.py` og `README.md` samt hele `.github/workflows/publish.yml`** til repository. Nemmest er at udpakke ZIP-filen lokalt og uploade via **Add file → Upload files**. **Vigtigt:** GitHub-webupload kan håndtere skjulte `.github`-mapper, men kontrollér at filen ender under `.github/workflows/publish.yml`. Hvis den mangler, kan du oprette den via **Add file → Create new file** og skrive `.github/workflows/publish.yml` som filnavn og indsætte indholdet fra ZIP-filen.
4. Gå til **Settings → Pages → Build and deployment → Source** og vælg **GitHub Actions**.
5. Gå til **Actions → Opdater podcast-RSS → Run workflow** for at køre første gang.
6. Når den grønne kørsel er færdig, er feedet på:

   `https://DIT_BRUGERNAVN.github.io/podcast-github/podcast.xml`

   Erstat `DIT_BRUGERNAVN` med dit GitHub-brugernavn (med små bogstaver).
7. Test linket i browseren og derefter i YouTube Music: https://music.youtube.com/library/podcasts?addrssfeed=

## Vigtige forbehold

- **YTM-kompatibilitet er ikke garanteret.** Først når YTM accepterer den offentlige adresse, ved vi, at løsningen fungerer.
- Scriptet henter **alle afsnit, som de fire oprindelige RSS-feeds stiller til rådighed**. Hvis udgiverne begrænser bagkataloget i RSS, kan scriptet ikke hente resten automatisk.
- Koden bevarer lydlinks hos de oprindelige udgivere og genudgiver **ikke** lydfilerne. Et afsnit kan derfor stoppe med at fungere, hvis originaludgiveren fjerner det.
- GitHub Actions' planlagte kørsler kan blive forsinket eller deaktiveret efter længere tids inaktivitet. De kan startes manuelt fra Actions.
- Podcast-coveret genbruges fra et af kildefeedene. Et speciallavet fælles cover er muligt senere.
- Ved netværksfejl for et af de fire feeds **stopper opdateringen** frem for at offentliggøre en mangelfuld version; det senest publicerede feed bliver liggende.
- Dette er et personligt feed. Respektér ophavsret og udgivernes vilkår.

## Lokal test

`python build_feed.py`

Resultat: `docs/podcast.xml`, `docs/index.html`, `docs/status.json`.

Du kan begrænse antal afsnit midlertidigt med miljøvariablen `MAX_EPISODES=10` (standard er 0 = alle).
