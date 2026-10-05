// Food-Pairing-Finder für bierspot.de
// Die Daten kommen aus data/pairing.yaml, data/stile.yaml und den Biertests (siehe layouts/pairing.html).
(function () {
  "use strict";
  var datenEl = document.getElementById("pf-daten");
  if (!datenEl) return;
  var D = JSON.parse(datenEl.textContent);

  var suche = document.getElementById("pf-suche");
  var katBox = document.querySelector(".pf__kategorien");
  var gerBox = document.querySelector(".pf__gerichte");
  var ergebnis = document.querySelector(".pf__ergebnis");

  var kategorien = ["Alle"];
  D.gerichte.forEach(function (g) {
    if (kategorien.indexOf(g.kategorie) === -1) kategorien.push(g.kategorie);
  });
  var kat = "Alle";
  var gewaehlt = null;

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function zeigeKategorien() {
    katBox.innerHTML = "";
    kategorien.forEach(function (k) {
      var b = el("button", "pf__kat", k);
      b.type = "button";
      b.setAttribute("aria-pressed", String(k === kat));
      b.addEventListener("click", function () { kat = k; zeigeKategorien(); zeigeGerichte(); });
      katBox.appendChild(b);
    });
  }

  function zeigeGerichte() {
    var q = suche.value.trim().toLowerCase();
    var liste = D.gerichte.filter(function (g) {
      return (kat === "Alle" || g.kategorie === kat) && g.name.toLowerCase().indexOf(q) !== -1;
    });
    gerBox.innerHTML = "";
    if (!liste.length) {
      gerBox.appendChild(el("p", "pf__leer", "Kein Gericht gefunden. Versuch es mit einem anderen Wort."));
      return;
    }
    liste.forEach(function (g) {
      var b = el("button", "pf__gericht", g.name);
      b.type = "button";
      b.setAttribute("aria-pressed", String(gewaehlt === g));
      b.addEventListener("click", function () { waehle(g, true); });
      gerBox.appendChild(b);
    });
  }

  function passendeBiere(g) {
    var stile = g.biere.map(function (b) { return b.stil; });
    return D.biere.filter(function (bier) {
      var perStil = (bier.stile || []).some(function (s) { return stile.indexOf(s) !== -1; });
      var perGericht = (bier.passt_zu || []).indexOf(g.name) !== -1;
      return perStil || perGericht;
    });
  }

  function zeigeErgebnis() {
    ergebnis.innerHTML = "";
    if (!gewaehlt) { ergebnis.hidden = true; return; }
    var g = gewaehlt;
    ergebnis.appendChild(el("h2", null, "Zu " + g.name + " passt"));

    g.biere.forEach(function (b) {
      var box = el("div", "pf__bier");
      var h = el("h3");
      var link = D.stillinks[b.stil];
      if (link) {
        var a = el("a", null, b.stil);
        a.href = link;
        h.appendChild(a);
      } else {
        h.appendChild(document.createTextNode(b.stil));
      }
      h.appendChild(el("span", "pf__prinzip", b.prinzip));
      box.appendChild(h);
      box.appendChild(el("p", null, b.warum));
      if (D.stile[b.stil]) box.appendChild(el("p", "pf__stiltext", D.stile[b.stil]));
      ergebnis.appendChild(box);
    });

    if (g.hinweis) {
      var tipp = el("p", "pf__tipp");
      tipp.appendChild(el("strong", null, "Tipp: "));
      tipp.appendChild(document.createTextNode(g.hinweis));
      ergebnis.appendChild(tipp);
    }

    var biere = passendeBiere(g);
    var getestet = biere.filter(function (b) { return !b.kurz; });
    var kurz = biere.filter(function (b) { return b.kurz; });
    var MAX_KURZ = 6;

    if (getestet.length) {
      var t = el("div", "pf__tests");
      t.appendChild(el("h3", null, "Aus meinen Biertests"));
      var ul = el("ul");
      getestet.forEach(function (bier) {
        var li = el("li");
        var a = el("a", null, bier.titel);
        a.href = bier.url;
        li.appendChild(a);
        if (bier.fazit) li.appendChild(el("span", null, bier.fazit));
        ul.appendChild(li);
      });
      t.appendChild(ul);
      ergebnis.appendChild(t);
    }

    if (kurz.length) {
      var k = el("div", "pf__tests pf__tests--kurz");
      k.appendChild(el("h3", null, "Schon getrunken, kurz notiert"));
      var p = el("p", "pf__kurzliste");
      kurz.slice(0, MAX_KURZ).forEach(function (bier, i) {
        if (i) p.appendChild(document.createTextNode(" · "));
        var a = el("a", null, bier.titel);
        a.href = bier.url;
        p.appendChild(a);
      });
      if (kurz.length > MAX_KURZ) {
        p.appendChild(document.createTextNode(" und " + (kurz.length - MAX_KURZ) + " weitere"));
      }
      k.appendChild(p);
      ergebnis.appendChild(k);
    }
    ergebnis.hidden = false;
  }

  function waehle(g, scrollen) {
    gewaehlt = g;
    zeigeGerichte();
    zeigeErgebnis();
    try {
      var url = new URL(window.location.href);
      url.searchParams.set("gericht", g.name);
      window.history.replaceState(null, "", url);
    } catch (e) { /* ältere Browser */ }
    if (scrollen && ergebnis.getBoundingClientRect().top > window.innerHeight) {
      ergebnis.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  suche.addEventListener("input", zeigeGerichte);
  zeigeKategorien();
  zeigeGerichte();

  // Gericht aus der Adresse vorauswählen, z. B. /food-pairing/?gericht=Pizza
  var vorwahl = new URLSearchParams(window.location.search).get("gericht");
  if (vorwahl) {
    var treffer = D.gerichte.filter(function (g) { return g.name === vorwahl; })[0];
    if (treffer) waehle(treffer, false);
  }
})();
