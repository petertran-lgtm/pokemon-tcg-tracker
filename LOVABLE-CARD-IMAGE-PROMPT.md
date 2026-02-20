# Paste This Into Lovable to Show Card Images

Open your PokéMarket project in Lovable, then paste the text below into the chat. Lovable will add card images to the watchlist.

---

## Copy everything between the lines below:

---

Display the card image on each watchlist card.

**What to do:**
- Each card in GET `/api/cards` now includes an `image_url` field (a URL to the card art).
- For each card in the watchlist grid, show the card image using this URL.
- Put the image at the top or left of each card tile, before the card name.
- Use a reasonable size (e.g. 150–200px width) so the card is recognizable but doesn't dominate the layout.
- If `image_url` is null or empty, show a placeholder (e.g. a gray box with a card icon, or "No image") so the layout doesn't break.
- Add a subtle border or shadow around the image so it looks like a card.

**Example structure for each card tile:**
```
[Card image]  Card name
              Set name
              Rarity badge
              $X.XX
              [Remove button]
```

The API already returns `image_url` for each card. Use it in an `<img>` tag with `src={card.image_url}` and appropriate `alt` text (e.g. the card name).

---

## That's it

Paste the text above into Lovable's chat. Your watchlist cards will show their artwork.
