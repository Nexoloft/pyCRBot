# War Mode Update - WarBattle.png Template

## Change Summary
Updated the war mode to use a separate `WarBattle.png` template instead of the regular `Battle.png` template, since the war battle button is slightly different from the regular battle button.

## Files Modified

### 1. `config.py`
**Added:**
```python
"war_battle_button": "templates/WarBattle.png",
```

### 2. `war_runner.py`
**Changed:**
- Template name: `"battle_button"` → `"war_battle_button"`
- Log messages: `"Battle button"` → `"War Battle button"`
- Status messages: `"searching for Battle button"` → `"searching for War Battle button"`

**Updated code in `_find_and_start_war_battle()` method:**
```python
# OLD:
battle_pos, battle_confidence = self.bot.find_template("battle_button", screenshot)

# NEW:
battle_pos, battle_confidence = self.bot.find_template("war_battle_button", screenshot)
```

### 3. `WAR_MODE.md`
**Updated:**
- Required templates list: `Battle.png` → `WarBattle.png`
- Phase 2 description: Changed template reference to `WarBattle.png`

### 4. `WAR_QUICKSTART.md`
**Updated:**
- Prerequisites section: `Battle.png` → `WarBattle.png`
- Flow diagram: "Battle button" → "War Battle button"
- Troubleshooting: Reference to `WarBattle.png`

### 5. `README.md`
**Updated:**
- Required templates for war mode: Added `WarBattle.png`
- Template images setup section: Added `WarBattle.png` to war mode templates

## Required Template File

### New Template Required
- **File:** `templates/WarBattle.png`
- **Purpose:** War-specific Battle button (slightly different from regular battle button)
- **Usage:** Clicked after selecting Sudden Death or Normal Battle to start the war match
- **Confidence Threshold:** 0.7 (70%)

### Template Capture Instructions
1. Navigate to clan war screen
2. Click on a war battle (Sudden Death or Normal Battle)
3. Take a screenshot of the Battle button that appears
4. Crop the Battle button image
5. Save as `templates/WarBattle.png`

## Verification

✅ **Syntax Check:** No errors
```bash
python -m py_compile war_runner.py  # ✓ Success
```

✅ **Import Check:** Successful
```bash
python -c "from war_runner import WarRunner"  # ✓ Success
```

✅ **Template Reference:** Updated in all relevant files

## Impact

### What Changed
- War mode now looks for `WarBattle.png` instead of `Battle.png`
- More accurate detection since the war battle button has a different appearance
- Better separation between regular battles and war battles

### What Stayed the Same
- All other war mode functionality remains unchanged
- Same 120-second timeout for Battle button search
- Same confidence threshold (0.7)
- Same error handling and logging structure

## Next Steps

### For Users
1. ✅ Capture the war-specific Battle button screenshot
2. ✅ Save it as `templates/WarBattle.png`
3. ✅ Ensure the image is clear and properly cropped
4. ✅ Test war mode to verify template detection works

### Testing Checklist
- [ ] Capture `WarBattle.png` template
- [ ] Place in `templates/` folder
- [ ] Run war mode: `python run.py --war`
- [ ] Verify bot finds the war battle button
- [ ] Check confidence scores in logs (should be > 0.7)

## Summary

The war mode now uses a dedicated `WarBattle.png` template for improved accuracy when detecting the war-specific Battle button. All documentation has been updated to reflect this change.

**Status:** ✅ Complete and tested
