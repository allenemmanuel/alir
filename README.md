# ALIR Cat & Dog Shelter website

A fast, accessible static site for ALIR (Animals Lovers Independent Rescuer), a no-kill shelter in Sabah, Malaysia. It replaces the Blogger front end at alirsabah.blogspot.com. The blog stays where it is, and full rescue stories still link to it.

## Build

You need Python 3.9 or newer. There are no other dependencies.

```bash
python build.py           # builds the site into dist/
python build.py --watch   # rebuilds every time a file in src/ changes
```

To preview the site, open `dist/index.html` in a browser, or run `python -m http.server -d dist 8000` and go to http://localhost:8000.

## Deploy

Upload the contents of `dist/` to any static host: Netlify (drag and drop the folder), Cloudflare Pages, GitHub Pages or Vercel. Once you have a domain, set `SITE_URL` in `build.py` so the canonical and social-sharing tags use it.

## Editing content

| To change… | Edit |
| --- | --- |
| Rescue case cards (home and Rescues pages) | `src/data/cases.json`. The cards are generated from this file. |
| Shelter photo gallery | `src/data/gallery.txt`. Each line is `filename|blogger-image-key`. |
| Page text | `src/pages/*.html` |
| Menu, urgent banner, footer | `src/partials/header.html` and `src/partials/footer.html` |
| Colours, type, spacing | The tokens at the top of `src/assets/css/styles.css` |

To add a new rescue, copy an entry in `cases.json`. For the photo, take the image URL from the Blogger post and replace the size part (for example `/s1080/`) with `/s{size}/`. The build then requests a suitably sized version for each screen.

## Design

- **Concept:** the rescue case card. Each animal is shown with the details from its intake: where it was found, its condition and the vet bill. Three cards fan out in the home page hero.
- **Colour:** rainforest green `#0E3B2C`, collar-tag yellow `#FFC93C`, mist `#EEF2EC`, and alert red `#C8412A` (used only for urgent status).
- **Type:** Bricolage Grotesque for headings. Atkinson Hyperlegible Next for body text, a typeface the Braille Institute designed for readers with low vision.
- **Motion:** the hero cards fan in once when the page loads. Every other animation responds to something you do. All motion respects reduced-motion settings.

### Alternative design

`designs/kennel-wall/` holds a complete alternative version: cardboard signs, taped photos, ALIR's real logo and a vet-receipt layout. To preview it, run `python designs/kennel-wall/build.py`. It builds into `designs/kennel-wall/dist/`. Its `src/assets/img/` folder also contains clean transparent PNG crops of ALIR's real logo, which can be reused here.
