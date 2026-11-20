# The store's index

The store of mx OS (an app of MXSHELL2, like Media) shows the programs made with ps2max,
installs them and keeps them up to date. Everything it needs is on GitHub:

- **the catalogue**: one site on GitHub Pages, made by this repository's CI: the index,
  the pictures, and the same catalogue as a web page for people;
- **the programs**: the release assets of each program's own repository, as its CI makes
  them (`ps2max32/docker`'s `build.yml`, a release at a tag `v*`).

The PS2 reads the site with `src/https.c` (DNS, TLS 1.3, redirects); the pictures are JPEG for
`<mx/pic.h>`, a trailer is MPEG for the IPU (`<mx/movie.h>`).

## The site

```
https://ps2max32.github.io/store/
  index.ini            the catalogue (below), at most 256 KiB
  index.sig            its signature: ECDSA P-256 over SHA-256 of index.ini, 64 bytes (r, s)
  index.html           the same catalogue for a browser, with links to every project
  img/<id>/cover.jpg   256 x 361: the tile on the shelf (a DVD case, 1 : 1.41)
  img/<id>/hero.jpg    640 x 360: the wide picture behind the program's page
  img/<id>/shot<n>.jpg 640 x 360: screenshots, 1 to 6
  img/<id>/trailer.mpg optional: MPEG-1 video, 640 x 360 at most, without sound or with MP2,
                       at most 8 MiB, at most 30 s
```

The pictures are baseline JPEG (not progressive), Y Cb Cr 4:2:0, quality 85: `mx_pic_decode`
takes about 0.08 s for one, and a page needs at most eight. The CI makes them from the
sources in any size and format (below). What the store has loaded it keeps on the device
(`<device>/PS2MAX/.store/img/`) by its SHA-256, so a picture that did not change is not
loaded again.

## index.ini

Lines `key=value`, as the shell's `game.ini`; a line `[name]` starts a section. UTF-8, but
only the characters the shell's font has (ASCII and Latin-1). Lines end with `\n`, at most
1024 bytes; a value has no `\n` of its own: in `description` the two characters `\n` are a
new line. Unknown keys are left alone (a newer index for an older store); an unknown
`format` is not read at all.

```ini
[store]
format=1
generated=2026-11-20T21:00:00Z
base=https://ps2max32.github.io/store/

[quake1]
title=Quake
kind=game
section=games
summary=The first person shooter that started it, on GLQuake.
description=Fight through four episodes...\nSplit screen for up to four players.
genre=Shooter
year=1996
developer=id Software
players=1-4
version=1.2.0
date=2026-11-18
url=https://github.com/ps2max32/quake1/releases/download/v1.2.0/quake1-ps2max.zip
size=1843210
sha256=9f2c...e1
installed=4718592
kernel=46
needs=id1/pak0.pak
needs_text=The PAK files of Quake (shareware or full) in id1/.
cover=img/quake1/cover.jpg 1b0e...44
hero=img/quake1/hero.jpg 77aa...0c
shots=img/quake1/shot1.jpg 51c3...9e,img/quake1/shot2.jpg 02fd...71
trailer=img/quake1/trailer.mpg c0de...5a
source=https://github.com/ps2max32/quake1
license=GPL-2.0
```

`[store]`: `format` (1), `generated` (when the CI made it, UTC), `base` (what the
relative paths below are relative to).

Each other section is one program; its name is its **id**: `a`-`z`, `0`-`9`, `-`, at most 31
characters, also its directory on the device (`PS2MAX/<id>/`). In the order the shelf
shows them. Its keys:

| Key | | |
|---|---|---|
| `title` | required | at most 40 characters |
| `kind` | required | `game`, `emulator`, `app`, `system` (the kernel, the shell: later) |
| `section` | | the shell's section it goes to: `games` (default), `emulation`, `media`, `apps` |
| `summary` | required | one line under the tile, at most 80 characters |
| `description` | | the program's page, at most 600 characters |
| `genre`, `year`, `developer`, `players` | | shown on its page; `players` as `1`, `1-4`, `2` |
| `version` | required | the release's tag without its `v`; a different one is an update |
| `date` | required | the release's date, `YYYY-MM-DD` |
| `url` | required | the package (below), a release asset: `https://github.com/...` |
| `size`, `sha256` | required | the package's bytes and SHA-256 (hex); the store keeps nothing that differs |
| `installed` | | bytes on the device after unpacking: the store checks the free space |
| `kernel` | | the lowest kernel version it runs on; an older kernel shows it greyed out, "needs a newer system" |
| `needs`, `needs_text` | | files the user brings: game data the store cannot give (`,` between them, relative to `PS2MAX/<id>/`). Missing ones are shown with `needs_text`; installing is allowed, starting waits until they are there |
| `cover`, `hero`, `shots`, `trailer` | | pictures: a path below `base`, a space, its SHA-256; `shots` several, `,` between them |
| `source`, `license` | | the project and its licence, shown on its page |

## The package

A zip (stored or deflated, no encryption, no zip64), with everything below one directory,
the id:

```
quake1/
  quake1.elf
  game.ini         title=, elf=, cover_hd=coverhd.t8, ... (the shell's, docs/mx-os.md "Packaging")
  coverhd.t8       256 x 361, apps/mxshell/tools/mk-cover.py's format
  <files of its own: configs, shaders, never game data>
```

The store unpacks it to `<device>/PS2MAX/<id>/`, where the shell finds it as any game. It
first checks size and SHA-256 against the index, then writes into `PS2MAX/.store/new/<id>/`
and moves the files into place only when all are there; what it wrote is listed in
`PS2MAX/<id>/.store` (the version and the files), for the next update and for removing it.
Files that are not in the package (the game data, saves, configs the program wrote) are
never touched; a file of an older version that the new one no longer has is removed.

## Trust

TLS (`certs/`: the roots of github.com and github.io) says the files came from GitHub. The
signature says the index came from this repository's CI: the store has the public key and
refuses an index whose `index.sig` does not match. The index holds the SHA-256 of every
package and picture, so a release asset that changes after the index was made is refused
too (the index is made again, by the CI, when a program has a new release).

## This repository

```
catalog/<id>.ini      what is written by hand: title, kind, summary, description, genre, year,
                      developer, players, needs, needs_text, license, and
                      repo=ps2max32/quake1, asset=*-ps2max.zip (which release asset)
catalog/<id>/         the pictures as made: cover.*, hero.*, shot*.*, trailer.* (any size, PNG,
                      JPEG or a video); the CI cuts and converts them
tools/mkindex.py      the newest release of each repo (GitHub's API), its asset's size and
                      SHA-256, the pictures, index.ini, index.sig, index.html into site/
.github/workflows/    mkindex.py on a push, every day and on a dispatch; site/ to GitHub Pages
```

A program joins the store with a `catalog/<id>.ini`, its pictures, and a release whose
asset is the package above. The private key is a secret of this repository
(`STORE_KEY`, PEM); its public half is in the store app.
