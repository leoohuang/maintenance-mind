"""Generate synthetic maintenance work orders with the configured LLM."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.llm import client

EQUIPMENT = [
    "Tablet press",
    "Blister packaging machine",
    "High shear mixer",
    "Fluid bed dryer",
    "Coating pan",
    "Capsule filling machine",
    "Vial filling line",
    "Autoclave sterilizer",
]
ORDERS_PER_EQUIPMENT = 8
FAILURE_MODES = {
    "Tablet press": [
        ("weight variation", "feeder paddle buildup", "Cleaned the feeder and verified fill depth."),
        ("tablet capping", "pre-compression force drift", "Adjusted pre-compression and checked tooling."),
        ("sticking on punches", "granule moisture too high", "Inspected punch faces and escalated material check."),
        ("lower output rate", "turret lubrication alarm", "Cleared lubrication line restriction."),
    ],
    "Blister packaging machine": [
        ("weak blister seals", "sealing temperature drift", "Recalibrated sealing temperature loop."),
        ("misaligned cutting", "web registration sensor contamination", "Cleaned sensor and verified registration."),
        ("forming pocket defects", "forming air leak", "Replaced cracked pneumatic tube."),
        ("feed jams", "worn guide rail", "Realigned and replaced guide rail insert."),
    ],
    "High shear mixer": [
        ("motor overload", "impeller buildup", "Cleaned impeller and checked current draw."),
        ("seal leak", "worn shaft seal", "Replaced shaft seal and leak tested."),
        ("batch inconsistency", "chopper speed mismatch", "Verified recipe speeds against batch record."),
        ("abnormal vibration", "blade wear", "Inspected blade clearance and scheduled replacement."),
    ],
    "Fluid bed dryer": [
        ("slow drying", "inlet filter restriction", "Changed filter and confirmed air flow."),
        ("temperature overshoot", "temperature probe drift", "Calibrated probe and checked controller."),
        ("product loss", "bag filter tear", "Replaced bag filter and inspected seals."),
        ("spray nozzle pulsing", "atomizing air instability", "Checked regulator and air line."),
    ],
    "Coating pan": [
        ("poor coating uniformity", "bed depth imbalance", "Adjusted load and pan speed."),
        ("spray interruption", "nozzle blockage", "Cleaned nozzle and verified spray pattern."),
        ("excess tackiness", "drying air temperature low", "Checked air heater and exhaust flow."),
        ("pan vibration", "drive belt wear", "Tensioned drive belt and inspected bearings."),
    ],
    "Capsule filling machine": [
        ("low capsule fill weight", "dosing disc wear", "Inspected dosing disc and retuned vacuum."),
        ("capsule separation jam", "vacuum loss", "Replaced cracked vacuum hose."),
        ("powder spill", "tamping pin alignment", "Aligned tamping station and cleaned guides."),
        ("rejected capsules", "sensor lens contamination", "Cleaned inspection sensor lens."),
    ],
    "Vial filling line": [
        ("underfilled vials", "pump calibration drift", "Recalibrated fill pump and sampled volumes."),
        ("stopper placement faults", "stopper bowl feed issue", "Cleared bowl track and checked vibration."),
        ("line stoppage", "photoeye contamination", "Cleaned photoeye and verified trigger."),
        ("drip at needle", "worn fill needle seal", "Replaced seal and performed drip check."),
    ],
    "Autoclave sterilizer": [
        ("cycle temperature deviation", "steam trap restriction", "Inspected steam trap and condensate flow."),
        ("door seal alarm", "gasket wear", "Replaced door gasket and pressure tested."),
        ("slow vacuum pull-down", "vacuum pump filter clog", "Changed filter and checked leak rate."),
        ("wet load after cycle", "drain blockage", "Cleaned drain strainer and verified drying phase."),
    ],
}
PROMPT_TEMPLATE = """You are a senior pharmaceutical maintenance engineer.

Generate {n} realistic and varied work orders for this equipment:
{equipment}

Each work order must be a JSON object with:
- order_id, date, equipment, equipment_id
- reported_issue, diagnosis, actions_taken
- parts_replaced, root_cause, resolution_time_hours
- technician_notes

Mix common, uncommon, and rare failure modes. Include realistic maintenance
terminology. Output only a JSON array of {n} objects."""


def generate_for_equipment(equipment: str, count: int) -> list[dict]:
    response = client.chat(
        messages=[
            {"role": "system", "content": "You output only valid JSON."},
            {
                "role": "user",
                "content": PROMPT_TEMPLATE.format(
                    equipment=equipment,
                    n=count,
                ),
            },
        ],
        temperature=0.8,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or ""
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        print(f"  ! JSON parse failed for {equipment}: {content[:200]}")
        return []
    if isinstance(parsed, dict):
        for value in parsed.values():
            if isinstance(value, list):
                return value
        return []
    return parsed if isinstance(parsed, list) else []


def generate_fallback_orders(equipment: str, count: int) -> list[dict]:
    """Create deterministic demo orders when an LLM key is unavailable."""
    failure_modes = FAILURE_MODES[equipment]
    orders = []
    for index in range(count):
        issue, root_cause, action = failure_modes[index % len(failure_modes)]
        sequence = EQUIPMENT.index(equipment) * count + index + 1
        orders.append(
            {
                "order_id": f"WO-2024-{sequence:04d}",
                "date": f"2024-{(sequence % 12) + 1:02d}-{(sequence % 24) + 1:02d}",
                "equipment": equipment,
                "equipment_id": f"{equipment.replace(' ', '-')}-{(index % 5) + 1:02d}",
                "reported_issue": (
                    f"Operator reported {issue} on {equipment.lower()} during "
                    f"routine production run {sequence}."
                ),
                "diagnosis": (
                    f"Technician reproduced the symptom and identified "
                    f"{root_cause} as the leading cause."
                ),
                "actions_taken": [
                    "Made equipment safe and reviewed recent alarms.",
                    action,
                    "Ran verification checks before release to production.",
                ],
                "parts_replaced": (
                    [root_cause] if "wear" in root_cause or "seal" in root_cause else []
                ),
                "root_cause": root_cause,
                "resolution_time_hours": round(1.25 + (index % 5) * 0.75, 2),
                "technician_notes": (
                    "Demo work order generated offline for retrieval testing."
                ),
            }
        )
    return orders


def main():
    all_orders = []
    llm_available = True
    for equipment in EQUIPMENT:
        print(f"Generating for {equipment}...")
        orders = []
        if llm_available:
            try:
                orders = generate_for_equipment(equipment, ORDERS_PER_EQUIPMENT)
            except Exception as error:
                print(f"  ! LLM generation unavailable: {type(error).__name__}")
                llm_available = False
        if not orders:
            orders = generate_fallback_orders(equipment, ORDERS_PER_EQUIPMENT)
            print("  -> using offline demo fallback")
        print(f"  -> got {len(orders)} orders")
        all_orders.extend(orders)

    output_path = Path("data/synthetic_orders.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(all_orders, indent=2, ensure_ascii=False))
    print(f"\nTotal: {len(all_orders)} orders written to {output_path}")


if __name__ == "__main__":
    main()
