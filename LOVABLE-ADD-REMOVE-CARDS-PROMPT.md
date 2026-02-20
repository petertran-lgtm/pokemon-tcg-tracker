# Paste This Into Lovable to Add "Add Card" and "Remove" Buttons

Open your PokéMarket project in Lovable, then paste the text below into the chat. Lovable will add the buttons for you.

---

## Copy everything between the lines below:

---

Add the ability to add and remove cards from the watchlist directly in the UI.

**1. Add Card Section (put it above the watchlist cards):**
- A text input where users type a card name (e.g. "Charizard ex", "Pikachu", "Flareon V")
- An "Add to Watchlist" button next to it
- When the user clicks Add:
  - Call POST to `/api/watchlist` with the request body: `{ "card_name": "[the text they typed]" }`
  - Use the same API base URL that this app already uses for fetching cards
  - If it succeeds: show a green message "Card added. Refreshing prices..." then call POST `/api/refresh` to fetch prices for the new card, then reload the cards from GET `/api/cards`
  - If it fails: show a red message "Could not add that card. Try the exact card name (e.g. Charizard ex)."
- Add a loading state on the Add button while the request is in progress

**2. Remove Button (on each card):**
- Add a small "Remove" or trash/X icon button on each card row
- When clicked: call DELETE `/api/watchlist?card_id=[this card's id]` 
  - IMPORTANT: Use the card's **id** (e.g. "swsh4-25"), NOT the card's name. Every card from GET /api/cards has an "id" field. Use that.
  - Example: DELETE `/api/watchlist?card_id=swsh4-25`
- If the API returns success, reload the cards from GET `/api/cards`
- If the API returns 404, try DELETE with `card_name=[this card's name]` as a fallback (for cards added by name)

**3. Make sure:**
- All API calls use the same base URL the app already uses (the one that fetches /api/cards)
- After adding a card, call POST /api/refresh before reloading cards (so the new card gets its prices)
- The Add input clears after a successful add

---

## That's it

Paste the text above into Lovable's chat. It will update your PokéMarket app with the Add and Remove features. You can then add and remove cards without touching any files.
