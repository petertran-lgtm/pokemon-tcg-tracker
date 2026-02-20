# How to Add and Remove Cards (No Coding Required)

This guide is for using the Pokemon TCG tracker without any technical experience.

---

## Use Your PokéMarket App (Recommended)

**To add this to your app:** Open the file **LOVABLE-ADD-REMOVE-CARDS-PROMPT.md** in this folder. Copy the prompt from that file and paste it into your Lovable project's chat. Lovable will add the buttons for you.

After that, you can:
1. Type a card name (e.g. "Charizard ex" or "Pikachu") and click **Add**
2. Click **Remove** next to any card to take it off your watchlist

---

## Backup: Edit the Watchlist File Directly

You can add or remove cards by editing a single file on your computer.

**Step 1: Find the file**

1. Open **Finder** (Mac) or **File Explorer** (Windows).
2. Go to: `Documents` → `PM-OS` → `pokemon-tcg-tracker` → `config`
3. Open the file named **watchlist.json** (double-click; it will open in a text editor).

**Step 2: What you'll see**

The file looks something like this:

```json
{
  "card_ids": ["swsh4-25"],
  "card_names": ["Flareon V", "Jolteon V", "Vaporeon V", "Flareon VMAX", "Jolteon VMAX", "Vaporeon VMAX"]
}
```

- **card_ids** = Cards added by their exact ID (e.g. swsh4-25). You can look these up on [tcgdex.dev](https://tcgdex.dev).
- **card_names** = Cards added by name. Type the exact card name as it appears (e.g. "Flareon V", "Charizard ex").

**Step 3: Add a card**

To add **"Pikachu"**:

1. Find the `"card_names"` line.
2. Add your card name in quotes, with a comma before it:
   ```json
   "card_names": ["Flareon V", "Jolteon V", "Vaporeon V", "Flareon VMAX", "Jolteon VMAX", "Vaporeon VMAX", "Pikachu"]
   ```
3. Save the file (Cmd+S on Mac, Ctrl+S on Windows).

**Step 4: Remove a card**

1. Delete the card name (and its comma) from the list.
2. Save the file.

**Rules:**

- Put each name in quotes: `"Charizard ex"`
- Separate names with commas (no comma after the last one)
- Don’t go over 200 cards total

**Step 5: See your new cards in the app**

After editing, the new cards won’t show up until prices are fetched:

- If you run the app **locally**: Run the fetch script (see README).
- If you use the **Railway** site: Call the refresh (or wait for the daily refresh).

---

## After Adding Cards

- **Local app:** Run the fetch to load prices (see the main README).
- **Railway (online) app:** Either call the refresh, or wait for the automatic daily refresh.

---

**See LOVABLE-ADD-REMOVE-CARDS-PROMPT.md for the full prompt to paste into Lovable.**
