# Selitev lokalnih skrbnikov UniFi za večmestne namestitve (neuradno)

**Različica:** 1.0.0-alpha · **Datum:** 31. 10. 2026

Ta paket rešuje specifično težavo: pri prehodu s starega samostojnega **UniFi Network Serverja** na **UniFi OS Server** se lahko uspešno obnovijo mesta in naprave, lokalni skrbniki pa ne dobijo delujočih novih prijav in ustreznih pravic.

Paket je pripravljen na podlagi uspešnega preizkusa na **UniFi OS Server 5.1.42 / Network 10.5.67**. Ni uradno orodje Ubiquitija; interni API je **nedokumentiran**. Posamezne verzije lahko delujejo drugače. Pred uporabo pri strankah je obvezen lasten test in popolna varnostna kopija.

## Vrstni red

1. **Pred migracijo:** varnostna kopija celotnega VM-ja, Network `.unf` backup, seznam mest, naprav in uporabnikov. Zapiši vrata in preveri port forwarding (posebej inform `8080` ter gostujoči portal). Nikoli ne poganjaj dveh aktivnih produkcijskih krmilnikov za iste naprave.
2. **Stari Network Server:** izvedi samo bralni izvoz adminov in pravic z `scripts/export_legacy.js`. To je treba izvesti na **stari** MongoDB `ace` (pred zamenjavo VM-ja oziroma na izolirani kopiji starega VM-ja). Izvoz vsebuje osebne podatke.
3. **Prehod na UniFi OS Server:** uporabi uradna Ubiquitijeva navodila. Na Linuxu se lahko postopek razlikuje od samodejne migracije na Windows/macOS. Obnovi konfiguracijo na način, primeren za tvojo namestitev; preveri dejansko stanje vseh mest in naprav. Zabeleži različico in naslov HTTPS.
4. **Novi UniFi OS Server:** na **novi** MongoDB `ace` preberi samo identifikatorje mest z `scripts/export_target_sites.js`. Tako preverimo, da dovoljenja ne kažejo na druga mesta.
5. **Excel:** kopiraj `templates/administrators_TEMPLATE.xlsx` v `administrators.xlsx` na zasebnem računalniku. Demo vrstice izbriši. Vnesi nova uporabniška imena, ime, priimek, e-pošto, število pozitivnih mest, **nova gesla**, izvorno staro uporabniško ime in način `import` ali `manual`. Če se ime spremeni, mora biti `legacy_username` eksplicitno in pravilno.
6. **Konfiguracija:** kopiraj `config.example.json` v `config.json`, popravi `base_url` in seznam Super Adminov. `allow_insecure_tls=false` naj ostane privzeto.
7. **Predogled:** v zaščiteni mapi (PowerShell):

   ```powershell
   python -m pip install -r requirements.txt
   python scripts/migrate_admins.py --preview
   ```

8. **Eden za preizkus:** odstrani prejšnje testne račune, če je to potrebno in varno, nato preveri v People, da izbrano novo uporabniško ime ne obstaja. Zaženi:

   ```powershell
   python scripts/migrate_admins.py --user novo_uporabnisko_ime
   ```

   Prijavi se kot lokalni lastnik v novem Chrome oknu, potrdi uvoz. Nato v **ločeni** prijavi preveri natančen seznam mest, `admin`/`readonly` in odsotnost drugih mest. Ponovno se prijavi in preveri trajnost pravic.

9. **Množični uvoz:** ko je preizkus potrjen, preveri People in napravi po potrebi uvoz po manjših sklopih:

   ```powershell
   python scripts/migrate_admins.py --all --limit 3
   python scripts/migrate_admins.py --all
   ```

   Program zahteva potrditev `IMPORT N`. Po vsakem koraku shrani kontrolni dnevnik `import_state.json`; ob napaki preneha, brez avtomatičnega ponavljanja zahtevka.

10. **Zaključek:** Super Admin/Owner ustvari ročno prek People, preveri vloge, naprave, Hotspot, DNS, certifikate, mobilni dostop in varnostne kopije. Delovno datoteko z gesli odstrani oziroma gesla shrani v upravljalnik gesel.

## Izvoz iz stare zbirke (samo branje)

Stari MongoDB `ace` in `mongo` lupina morata biti na voljo. Na starem Linux krmilniku v zaščitenem delovnem imeniku:

```bash
umask 077
mongo --quiet --host 127.0.0.1 --port 27117 ace scripts/export_legacy.js > legacy_privileges.jsonl
```

Preveri število vrstic in podatkov. **Ne objavi izvoda.** Ukaz ne spreminja baze. Dejanska namestitvena pot in vrata se lahko razlikujejo; pred zagonom preveri, da je to res *stara* podatkovna zbirka.

## Izvoz mest iz nove zbirke (samo branje)

Za UniFi OS Server je bil preizkušen dostop prek `uosserver shell`, kjer teče nova zbirka. Skripto `scripts/export_target_sites.js` je treba predhodno prenesti v vsebnik (na primer z `podman cp`; identifikator vsebnika preveri z `podman ps`). Nato znotraj vsebnika:

```bash
mongo --quiet --host 127.0.0.1 --port 27117 ace /tmp/export_target_sites.js > /tmp/target_sites.jsonl
```

Datoteko prenesi iz vsebnika na zaščiten Windows računalnik, na katerem teče uvoznik. Če stara in nova namestitev nista ohranili **istih ID-jev mest**, se uvoz ne sme nadaljevati.

## Vhodni podatki

V prvi Excelovi preglednici naj bodo stolpci:

| username | first_name | last_name | email | site_count | password | legacy_username | mode |
|---|---|---|---|---:|---|---|---|
| nov-alice | Alice | Test | alice@example.invalid | 2 | (lokalno geslo) | old-alice | import |
| platformadmin1 | Admin | Test | admin@example.invalid | 200 | (prazno) | old-admin | manual |

`mode=manual` je namenjen posebej skrbnikom z ravnjo Super Admin/Owner. Takih računov skripta **ne ustvarja** kot običajne Site Admine. Gesla za uvozne račune so v Excelu v navadnem besedilu: datoteke ne pošiljaj v klepet, ne shranjuj v oblak, ne pripenjaj v GitHub.

## Kaj skript preverja

- prepozna uparjanje po starem uporabniškem imenu; preimenovanja ne ugiba po e-pošti ali številu mest;
- zavrne podvojene uvozne uporabnike in preslikave dveh novih računov na en star račun;
- preveri, da vsak pozitivni stari `site_id` obstaja na cilju in da se notranje ime mesta ujema;
- pretvori staro `admin` v `s-ID-admin` in `readonly` v `s-ID-readonly`;
- ignorira `nobody` in posebno mesto `super`;
- uporabi **lokalno** prijavljeno sejo Chroma z zaščito CSRF (žetona ne izpiše);
- ne dostopa neposredno do zapisovanja v MongoDB ali PostgreSQL;
- ustavi se ob nejasnem rezultatu API-ja, preden bi ustvarjal naslednje uporabnike.

## Pomembne omejitve

Nobena uspešna koda HTTP **ni dokaz**, da imajo uporabniki pravilne dejanske pravice; prijavo in vidnost mest preveri ročno. Skripta ne zazna zanesljivo vseh računov, ki so bili ustvarjeni izven nje: pred uvozom obvezno preveri People. Delnega uvoza ne ponavljaj z brisanjem `import_state.json`.

**Pozor:** če v določeni verziji UniFi OS Serverja API, polja, CSRF ali dovoljenja delujejo drugače, uvoz ustavi. Priporočena pot je vedno najprej uradno podprt postopek Ubiquitija.

Uradna dokumentacija je navedena v [README.md](README.md). Informacije o obnovitvi in odpravljanju težav so v [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).