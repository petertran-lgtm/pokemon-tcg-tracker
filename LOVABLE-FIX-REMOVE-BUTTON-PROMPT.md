# Fix the Remove Button (Paste Into Lovable)

The Remove (X) button isn't working because it's sending the card's **name** to the API, but some cards (like Charizard) were added by **ID**. The API needs the card's **id** to remove it.

**Paste this into Lovable to fix it:**

---

Fix the Remove button so it actually removes cards from the watchlist.

**The problem:** The Remove button is calling DELETE with `card_name`, but cards like Charizard were added by `card_id`. The API needs the correct parameter.

**The fix:** When the user clicks Remove (the X) on a card:
1. Call DELETE with `card_id` using the card's **id** from the API response (e.g. "swsh4-25", "swsh7-169"). Every card object has an "id" field. Use: `DELETE /api/watchlist?card_id=[card.id]`
2. If that returns 404, try `DELETE /api/watchlist?card_name=[card.name]` as a fallback
3. On success, reload the cards from GET /api/cards
4. Show a brief "Card removed" message

The key change: **use `card_id` first** (the card's id property), not `card_name`.

---
