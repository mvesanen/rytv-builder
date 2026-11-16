# rytv-builder

Julkaisumoottori RYTV-aineistoille. Kontti lukee julkaisurepon ja kirjoittaa sen `artefact/`-kansioon PDF:n, HTML:n ja kopion koneluettavista tiedostoista.

Julkaisurepo ei sisällä tätä koodia. Se kiinnittää kontin version ja tuo vain aineiston.

## Komento

```bash
python -m builder /polku/julkaisurepoon
```

Kontissa oletuspolku on `/publication`:

```bash
docker build -t rytv-builder .
docker run --rm -v C:\polku\julkaisuun:/publication rytv-builder
```

Komento lukee `publication.json`, piirtää `diagrams/*.mmd`-tiedostot PNG-kuviksi ja ajaa Pandocin. Skeemat, IDS-tiedostot ja `.bpmn`-kuvaukset kopioidaan artefaktiin sellaisenaan.

## Mitä tämä versio ei vielä tee

XSD-, JSON Schema- ja IDS-tabulaattorit, BPMN:n piirtäminen SVG:ksi, GitHub Pagesin versioarkisto ja kuvien zoomaus tulevat seuraavaksi. Nykyinen komento kokoaa jo kirjoitetun markdownin ja säilyttää koneluettavat lähdetiedostot julkaisupaketissa.

## Kuvan julkaisu

GitHub Actions julkaisee kuvan GHCR:ään. Push `main`-haaraan julkaisee tagin `edge`. Git-tagi `v0.1.1` julkaisee `0.1.1` ja `0.1`. Julkaisurepo kiinnittää versionumeron, jotta vanha julkaisu rakentuu myöhemmin samalla moottorilla.

Nykyinen kiinnitys on `ghcr.io/mvesanen/rytv-builder:0.1.1`.
