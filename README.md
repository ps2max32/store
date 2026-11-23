# store

The catalogue of MXSTORE, the store of mx OS on the PS2: which programs it offers, their
descriptions and art, and the site it reads, <https://ps2max32.github.io/store/> (also a web
page with every project). The store app itself is part of MXSHELL2
([ps2max32/mxshell](https://github.com/ps2max32/mxshell), `store/`).

- `catalog/<id>/`: one program each: its `game.ini` (the shell's, with the store's keys beside
  them) and its pictures. An install writes that `game.ini` and the cover, so the store and the
  shell's shelf show the same.
- `tools/mkindex.py`: the site from the catalogue and the newest release of each program
  (`site/`: `index.ini`, its signature, the pictures, `index.html`).
- `tools/mkart.py`: covers for programs without art of their own.
- `docs/index-format.md`: the format, the packages, system updates, and how the store checks
  what it loads.

## Adding a program

1. Its repository makes a release whose asset is the package (`docs/index-format.md`, "The
   package"): a zip of `<id>/` with the ELF and its `game.ini`.
2. Add `catalog/<id>/game.ini` (an existing one shows the keys) with `repo=` and `asset=`.
3. Pictures: `catalog/<id>/cover.png` (any size, cut to 1 : 1.41), `hero.png`, `shot1.png` ...
   (16 : 9), `trailer.mp4`; all optional but the cover, which
   `tools/mkart.py <id>` makes when there is none.
   The games' covers are their publishers' own art (the games and their art belong to their
   owners; a cover is taken down when an owner asks); the apps' covers are ours.
4. Push: the site is made again; also every day, for new releases.

`python3 tools/mkindex.py` makes the site locally (Pillow; a trailer needs ffmpeg). The
index is signed with the `STORE_KEY` secret (an EC P-256 key, PEM); its public half is in the
store app.

The fonts in `fonts/` are Inter Tight and JetBrains Mono, under the SIL Open Font License
(`fonts/OFL-*.txt`).
