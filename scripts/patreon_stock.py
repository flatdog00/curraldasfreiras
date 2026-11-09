"""Atualiza data/stock.json com o número de membros de cada escalão do Patreon.

Corre no GitHub Actions (ver .github/workflows/patreon-stock.yml).
Precisa do segredo PATREON_TOKEN (Creator's Access Token do portal de programadores do Patreon).
Só usa a biblioteca padrão do Python.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

API = "https://www.patreon.com/api/oauth2/v2/campaigns"
FIELDS = "?include=tiers&fields%5Btier%5D=title,patron_count,user_limit,remaining,published"
STOCK = os.path.join(os.path.dirname(__file__), "..", "data", "stock.json")


def get(url, token):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "User-Agent": "curraldasfreiras-stock/1.0",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def norm(s):
    return " ".join((s or "").lower().split())


def main():
    token = os.environ.get("PATREON_TOKEN", "").strip()
    if not token:
        print("PATREON_TOKEN não definido; nada a fazer.")
        return 0

    data = get(API + FIELDS, token)
    tiers = [t for t in data.get("included", []) if t.get("type") == "tier"]
    by_title = {norm(t["attributes"].get("title")): t["attributes"] for t in tiers}

    with open(STOCK, encoding="utf-8") as f:
        stock = json.load(f)

    changed = False
    for tier in stock["tiers"]:
        attrs = by_title.get(norm(tier.get("match") or tier["name"]))
        if not attrs:
            print(f"Escalão não encontrado no Patreon: {tier['name']}")
            continue
        count = int(attrs.get("patron_count") or 0)
        limit = attrs.get("user_limit") or tier.get("limit")
        if tier.get("count") != count or tier.get("limit") != limit:
            tier["count"], tier["limit"] = count, limit
            changed = True
        print(f"{tier['name']}: {count} de {limit}")

    if changed or stock.get("source") != "patreon":
        stock["source"] = "patreon"
        stock["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(STOCK, "w", encoding="utf-8") as f:
            json.dump(stock, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
