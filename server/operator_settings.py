"""Optional server-local owner draft, never a public key/payment endpoint."""
import json
from pathlib import Path

from .billing import BankInput
from .pricing import PricingInput, store_quote


def seed_owner_draft(db):
    import os
    if os.getenv('LOAD_OWNER_DRAFT', 'true').lower() != 'true':
        return
    path = Path(__file__).resolve().parent.parent / '.private' / 'operator-preferences.json'
    if not path.is_file():
        return
    prefs = json.loads(path.read_text())
    bank = BankInput.model_validate(prefs.get('bank', {}))
    if not db.execute('SELECT 1 FROM billing_settings WHERE id=1').fetchone():
        db.execute('INSERT INTO billing_settings VALUES (1,?,?,?)', (bank.card_number, bank.holder, bank.bank))
    if not db.execute('SELECT 1 FROM billing_price_quotes').fetchone():
        # Requesting receiving is not an effective activation. No invented USD
        # prices, card order, bank name or exchange quote are populated.
        store_quote(db, PricingInput(receiving_requested=prefs.get('receiving_requested', False)))
