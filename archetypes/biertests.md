---
title: "{{ replace .File.ContentBaseName "-" " " | title }}"
date: {{ .Date }}
draft: true
brauerei: ""
herkunft: ""
# Stil genau wie in data/stile.yaml, z. B. "Märzen", "Pale Ale", "IPA"
stile: [""]
alkohol:          # z. B. 5.2
ibu:              # optional
# Je 1 bis 5, siehe /so-bewerte-ich/
profil:
  bittere:
  malz:
  frucht:
  roest:
  koerper:
# Gerichte genau wie in data/pairing.yaml
passt_zu: []
fazit: ""
---
