# The store's index

The store of mx OS, MXSTORE (an app beside MXSHELL2: a tile in its Apps section), shows
the programs made with ps2max, installs them and keeps them up to date: the games and
emulators, and mx OS itself (MXBOOT, MXKERNEL with its IOP modules, MXSHELL, and MXSTORE).
Only MXBOOT and MXKERNEL live on the memory card; everything else, MXSHELL and MXSTORE too, is
a program in `<device>/PS2MAX/<id>/` like any game.
Everything it needs is on GitHub:

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
  img/<id>/cover.t8    256 x 361: the tile on the shelf (a DVD case, 1 : 1.41), in the
                       shell's own format (below); cover.jpg the same for the web page
  img/<id>/hero.jpg    640 x 360: the wide picture behind the program's page
  img/<id>/shot<n>.jpg 640 x 360: screenshots, 1 to 6
  img/<id>/trailer.mpg optional: MPEG-1 video, 640 x 360 at most, without sound or with MP2,
                       at most 8 MiB, at most 30 s
```

The cover is the shell's `coverhd.t8` (a CLUT of 256 RGBA entries in the GS's CSM1 order,
then 256 x 361 indices; `apps/mxshell/tools/mk-cover.py`): the store shows that file, and an
install writes it as the program's cover, so the store and the shelf show the same picture,
byte for byte. The other pictures are baseline JPEG (not progressive), Y Cb Cr 4:2:0, quality
85: `mx_pic_decode` takes about 0.08 s for one, and a page needs at most eight. The CI makes them from the
sources in any size and format (below). What the store has loaded it keeps on the device
(`<device>/PS2MAX/.store/img/`) by its SHA-256, so a picture that did not change is not
loaded again.

## index.ini

Lines `key=value`; a line `[name]` starts a section. Each program's section **is its
`game.ini`** (the shell's, `docs/mx-os.md` "Packaging"): the shell's keys with the same names
and meaning, and the store's keys beside them, which the shell leaves alone. UTF-8, but only
the characters the shell's font has (ASCII and Latin-1). Lines end with `\n`, at most 1024
bytes; a value has no new line. Unknown keys are left alone (a newer index for an older store);
an unknown `format` is not read at all.

```ini
[store]
format=1
generated=2026-11-20T21:00:00Z
base=https://ps2max32.github.io/store/

[quake1]
title=Quake
type=Shooter
year=1996
description=The first person shooter that started it, on GLQuake. Four episodes...
order=10
kind=game
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
cover=img/quake1/cover.t8 1b0e...44
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
The shell's keys (`apps/mxshell` `src/games.c`; together at most 640 bytes, so that they and
`elf=`, `args=`, `saves=` fit the 768 bytes an older shell reads):

| Key | | |
|---|---|---|
| `title` | required | at most 40 characters |
| `section` | | the shell's section: `games` (default), `emulation`, `media`, `apps`; `system`: not on the shelf (MXSHELL itself) |
| `type`, `year` | | the line under the title, in the store and on the shelf |
| `description` | required | at most 400 characters: all of it on the store's page, its first lines on the shell's |
| `order` | | the order on the shelf and in the store, lowest first |

The store's keys:

| Key | | |
|---|---|---|
| `kind` | required | `game`, `emulator`, `app`, `system` (mx OS itself: below) |
| `developer`, `players` | | shown on its page; `players` as `1`, `1-4`, `2` |
| `version` | required | the release's tag without its `v`; a different one is an update |
| `date` | required | the release's date, `YYYY-MM-DD` |
| `url` | required | the package (below), a release asset: `https://github.com/...` |
| `size`, `sha256` | required | the package's bytes and SHA-256 (hex); the store keeps nothing that differs |
| `installed` | | bytes on the device after unpacking: the store checks the free space |
| `kernel` | | the lowest kernel version it runs on; an older kernel shows it greyed out, "needs a newer system" |
| `needs`, `needs_text` | | files the user brings: game data the store cannot give (`,` between them, relative to `PS2MAX/<id>/`). Missing ones are shown with `needs_text`; installing is allowed, starting waits until they are there |
| `cover`, `hero`, `shots`, `trailer` | | pictures: a path below `base`, a space, its SHA-256; `shots` several, `,` between them |
| `source`, `license` | | the project and its licence, shown on its page |

## One game.ini, in the store and on the shelf

What the store shows and what the shell shows after an install are one file: the catalogue's
`catalog/<id>/game.ini`, which is the index's section. An install writes the program's
`game.ini` as that section: first its shell keys and `cover_hd=coverhd.t8`, then the keys of
the package's own `game.ini` that belong to the program (`elf`, `args`, `saves`), then the
store's keys (with `version`; without `url`, `size`, `sha256` and the pictures' lines); and the
cover (`coverhd.t8`) over the package's. The shell reads the first 2 KiB of a `game.ini`.
A program changes its look in the catalogue, not in its package; the shell may show any of the
store's keys too (`developer`, `players`, `version`). `apps/mxshell/package-games.sh` (games put
on a stick by hand) takes the same file from the catalogue.

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

The store loads it to `<device>/PS2MAX/.store/<id>.zip`, checks size and SHA-256 against the
index, then unpacks it to `<device>/PS2MAX/<id>/`, where the shell finds it as any game (each
file's CRC checked; names outside `<id>/` left out). mx OS has no rename yet, so the files are
written in place: `PS2MAX/<id>/.store` (the version, `state=`, the files) says `state=partial`
until all are there, and the store offers to repair such an install. That list is also what
the next update and Remove go by: files that are not in the package (the game data, saves,
configs the program wrote) are never touched; a file of an older version that the new one no
longer has is removed. A copy put there by hand (a `game.ini` without `.store`) is shown as
such and replaced only after the user confirms.

## mx OS itself (`kind=system`)

Four entries: `mxboot` (MXBOOT), `mxos` (MXKERNEL, its IOP modules and the host link's
service), `mxshell` (MXSHELL), `mxstore` (MXSTORE). `mxshell` and `mxstore` are programs as any
other: a package of `<id>/`, installed to `<device>/PS2MAX/mxshell/` (`section=system`, so not on
the shelf; the kernel starts it as the shell) and `<device>/PS2MAX/mxstore/` (`section=apps`, a
tile). `mxboot` and `mxos` start the console and stay on the memory card in slot 1: their
packages are zips of files at their places there (`MXOS/MXKERNEL.ELF`, `MXOS/mxsock.irx`,
`MXBOOT/MXBOOT.ELF`), and the store writes those only there, only `mc0:`. More keys:

| Key | | |
|---|---|---|
| `update` | `mxboot`, `mxos` | how it is put in place on the card, below: `kernel` or `boot` |
| `kernel` | | the kernel version it needs; `mxos` gives the version it brings as `provides=` |
| `provides` | `mxos` | the kernel version of this package |

They are shown in the store's own System row and in Updates, not on the shelf. The store
installs `mxshell` and `mxstore` now; `mxboot` and `mxos` need mx OS changes first (a rename
on the memory card, and `mx_kernel_path`), and are installed from the PC until then. An update of
several goes in this order: `mxos`, `mxshell`, `mxstore`, `mxboot`; an entry whose `kernel=` the
running kernel does not meet waits for `mxos`.

- **without `update`** (MXSHELL, MXSTORE): as any program (below "The package"). The running
  shell and store are in memory, not read from their files, so they are replaced in place;
  the new one runs from its next start (the shell: after the store asks for a restart of the
  shell). Which shell the kernel starts: `docs/mx-os.md`, "The shell".
- **`kernel`** (MXKERNEL and its modules, which belong together): the files go to `MXOS/NEW/`;
  mxboot's one-shot (`BOOTONCE.CFG`) starts `MXOS/NEW/MXKERNEL.ELF` at the next boot, which the
  store asks for ("restart to finish": the user resets). If that kernel comes up, the store
  (at its next start) moves the old set to `MXOS/BACKUP/` and `NEW/` into place; if it does
  not, the next reset boots the old kernel again and the store says the update failed. This
  needs the kernel to say where it was started from (`mx_kernel_path`, an mx OS change still
  to be made).
- **`boot`** (MXBOOT): only phase 2, `MXBOOT/MXBOOT.ELF`: written as `MXBOOT.NEW` and read
  back, the old one moved to `MXBOOT/BACKUP/`, the new one renamed into place. Phase 1 (the system update KELF, bound to the card) stays the installer's
  (`mxboot-install`): a card whose phase 1 is wrong boots nothing, so no store writes it.

## Trust

TLS (`certs/`: the roots of github.com and github.io) says the files came from GitHub. The
signature says the index came from this repository's CI: the store has the public key and
refuses an index whose `index.sig` does not match. The index holds the SHA-256 of every
package and picture, so a release asset that changes after the index was made is refused
too (the index is made again, by the CI, when a program has a new release).

## This repository

```
catalog/<id>/game.ini what is written by hand: the keys above, and repo=ps2max32/quake1,
                      asset=*.zip (which release asset; a repo without a release is left out)
catalog/<id>/         the pictures as made: cover.*, hero.*, shot*.*, trailer.* (any size, PNG,
                      JPEG or a video); the CI cuts and converts them
tools/mkindex.py      the newest release of each repo (GitHub's API), its asset's size and
                      SHA-256, the pictures, index.ini, index.sig, index.html into site/
tools/mkart.py        a cover and a wide picture for a program without its own (Penumbra,
                      the shell's ground colours, fonts/)
.github/workflows/    mkindex.py on a push, every day and by hand; site/ to GitHub Pages
```

A program joins the store with a `catalog/<id>/game.ini`, its pictures, and a release whose
asset is the package above. `mxos`'s release tags are its kernel version (`v46`): that is the
`provides=` of its entry. The private key is a secret of this repository (`STORE_KEY`, PEM);
its public half is in the store app.
