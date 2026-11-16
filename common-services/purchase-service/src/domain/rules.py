# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Purchase order lines, receipt and the text sent to the supplier (ORD-03, ORD-05..07)."""
from __future__ import annotations


def _price(value) -> float:
    """A unit price: 0 or more, up to a hundred million, to 4 decimals. Raises INVALID_PRICE."""
    try:
        number = round(float(value), 4)
    except (TypeError, ValueError):
        raise ValueError("INVALID_PRICE")
    if number < 0 or number > 100_000_000:
        raise ValueError("INVALID_PRICE")
    return int(number) if number.is_integer() else number


def _qty(value, allow_zero: bool = False) -> float:
    try:
        number = round(float(value), 4)
    except (TypeError, ValueError):
        raise ValueError("INVALID_QUANTITY")
    if number < 0 or (number == 0 and not allow_zero) or number > 1_000_000:
        raise ValueError("INVALID_QUANTITY")
    return int(number) if number.is_integer() else number


def clean_lines(lines) -> list[dict]:
    """[{item_id, qty, recommended?, price?}] - zero lines dropped, an item listed twice adds up (the last price given wins)."""
    out: dict[str, dict] = {}
    for line in lines or []:
        item = str((line or {}).get("item_id") or "").strip()
        if not item:
            raise ValueError("UNKNOWN_ITEM")
        qty = _qty(line.get("qty"), allow_zero=True)
        if qty == 0:
            continue
        row = out.setdefault(item, {"item_id": item, "qty": 0})
        row["qty"] = round(row["qty"] + qty, 4)
        if line.get("recommended") not in (None, ""):
            row["recommended"] = _qty(line["recommended"], allow_zero=True)
        if line.get("price") not in (None, ""):            # the price agreed with the supplier for one (else the goods' cost)
            row["price"] = _price(line["price"])
    if not out:
        raise ValueError("NO_LINES")
    return list(out.values())


def received_lines(ordered: list[dict], changed: list[dict] | None) -> list[dict]:
    """ORD-07: receive in full (no changes) or with changed quantities (and serial numbers); an item not on the order may arrive too."""
    price = {l["item_id"]: l["price"] for l in ordered if l.get("price") is not None}
    if not changed:
        return [{"item_id": l["item_id"], "qty": l["qty"], **({"price": l["price"]} if l.get("price") is not None else {})} for l in ordered]
    got: dict[str, dict] = {}
    for line in changed:
        item = str(line.get("item_id") or "")
        if not item:
            raise ValueError("UNKNOWN_ITEM")
        got[item] = {"item_id": item, "qty": _qty(line.get("qty"), allow_zero=True)}
        given = line.get("price") if line.get("price") not in (None, "") else price.get(item)
        if given is not None:                        # what one cost: as ordered, or as the supplier's invoice says
            got[item]["price"] = _price(given)
        serials = [str(x).strip() for x in line.get("serials") or [] if str(x).strip()]
        if serials:                                  # products that track units (IMEI / serial) pass them on to stock
            got[item]["serials"] = serials
    return [l for l in got.values() if l["qty"] > 0]


def message(business: str, supplier: str, number: str, deliver_to: str, lines: list[dict], names: dict, note: str = "") -> str:
    """ORD-06: the order as plain text to paste into WhatsApp."""
    rows = [(f"- {names.get(l['item_id'], {}).get('name', l['item_id'])}: {l['qty']} {names.get(l['item_id'], {}).get('unit', '')}".rstrip()
             + (f" @ {l['price']:g}" if l.get("price") is not None else "")) for l in lines]
    text = [f"Order {number} from {business}", f"To: {supplier}", f"Deliver to: {deliver_to}", "", *rows]
    if note:
        text += ["", note]
    return "\n".join(text)


def add_up(earlier: list[dict], got: list[dict]) -> list[dict]:
    """What has arrived so far: per item the quantities added, serials put together, the latest price kept."""
    total: dict[str, dict] = {}
    for line in [*(earlier or []), *(got or [])]:
        row = total.setdefault(line["item_id"], {"item_id": line["item_id"], "qty": 0})
        row["qty"] = round(row["qty"] + float(line.get("qty") or 0), 4)
        if float(row["qty"]).is_integer():
            row["qty"] = int(row["qty"])
        if line.get("price") is not None:
            row["price"] = line["price"]
        if line.get("serials"):
            row["serials"] = [*row.get("serials", []), *line["serials"]]
    return list(total.values())


def all_arrived(ordered: list[dict], received: list[dict]) -> bool:
    """Every ordered line has arrived in full (more is fine)."""
    got = {l["item_id"]: float(l.get("qty") or 0) for l in received or []}
    return all(got.get(l["item_id"], 0) >= float(l.get("qty") or 0) for l in ordered or [])
