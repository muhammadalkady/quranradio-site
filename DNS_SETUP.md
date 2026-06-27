# DNS Setup — quranradio.app (Hostinger)

Point the domain at GitHub Pages.

## Where to go in Hostinger
hPanel → **Domains** → select `quranradio.app` → **DNS / Nameservers** → **DNS Records**
(Make sure you're using Hostinger's default nameservers so this DNS zone is active.)

## 1. Delete conflicting records first
Remove any existing **A record** with name `@` and any existing **CNAME** with name `www`
(Hostinger usually adds a parking A record — delete it, or the site won't point to GitHub).

## 2. Add these records

### Apex domain (quranradio.app) — 4 A records
| Type | Name | Points to / Value | TTL   |
|------|------|---------------------|-------|
| A    | @    | 185.199.108.153     | 14400 |
| A    | @    | 185.199.109.153     | 14400 |
| A    | @    | 185.199.110.153     | 14400 |
| A    | @    | 185.199.111.153     | 14400 |

### www subdomain (optional, recommended) — 1 CNAME
| Type  | Name | Points to / Value          | TTL   |
|-------|------|----------------------------|-------|
| CNAME | www  | muhammadalkady.github.io   | 14400 |

> Hostinger uses `@` for the root/apex domain. Enter the IPs exactly.
> For the CNAME value, some panels require a trailing dot: `muhammadalkady.github.io.`

## 3. After saving
- DNS propagation: a few minutes up to a few hours.
- Check it's live:  `dig +short quranradio.app`  → should return the four 185.199.x.x IPs.
- Then in the repo: **Settings → Pages → enable "Enforce HTTPS"** (free auto SSL).

## Reference
- Repo:        https://github.com/muhammadalkady/quranradio-site
- GitHub URL:  https://muhammadalkady.github.io/quranradio-site/
- Final URL:   https://quranradio.app
