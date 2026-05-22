"""Generate fallback Markdown manuals with the configured LLM."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.llm import client

TOPICS = [
    (
        "tablet_press_troubleshooting",
        "Tablet Press Troubleshooting Guide",
        "weight variation, capping, sticking, picking, lamination",
    ),
    (
        "blister_packaging_maintenance",
        "Blister Packaging Machine Maintenance",
        "sealing defects, forming issues, cutting alignment, feed problems",
    ),
    (
        "mixer_operation",
        "High Shear Mixer Operation Manual",
        "blade wear, motor overload, seal leaks, batch consistency",
    ),
]
PROMPT = """Write a detailed technical manual section about: {title}

Cover these topics: {topics}

Use Markdown headings. For each topic include symptoms, root causes, diagnostic
steps, and corrective actions. Write 800-1200 words without filler."""
FALLBACK_MANUALS = {
    "tablet_press_troubleshooting": """# Tablet Press Troubleshooting Guide

## Weight variation

Weight variation may follow inconsistent die fill, feeder paddle buildup, poor
granule flow, fill-depth adjustment drift, or compression settings that no
longer match the recipe. Confirm the symptom with a short sample set before
adjusting the press. Check feeder motion, fill cam position, granule level, and
recent cleaning status. Inspect dies and punches for buildup. Corrective action
should start with clearing feed restrictions and verifying the approved recipe
settings before changing compression force.

## Capping and lamination

Capping and lamination can point to air entrapment, worn tooling, high turret
speed, or unsuitable pre-compression. Inspect tooling faces and compare
pre-compression and main compression values to the batch setup. Reduce speed
only through the approved operating procedure and record the verification lot.

## Sticking and picking

Sticking requires a tooling inspection and a material check. Look for moisture,
punch-face residue, heat buildup, and inadequate lubrication. Clean affected
tooling, document the lot condition, and escalate raw-material variation when
the symptom follows the batch rather than the station.""",
    "blister_packaging_maintenance": """# Blister Packaging Machine Maintenance

## Sealing defects

Weak or incomplete seals require inspection of sealing temperature, dwell time,
pressure, platen condition, and web alignment. Confirm sensor readings against
the displayed set point and inspect for residue on sealing surfaces. Record any
temperature calibration adjustment before releasing production.

## Forming and feed problems

Pocket defects may follow forming air leaks, damaged tooling, or film tracking
issues. Feed jams often involve worn guides, web tension, contaminated
registration sensors, or a misaligned transfer. Isolate the station where the
fault begins and verify one corrective action at a time.

## Cutting alignment

Cutting misalignment should be checked against registration mark detection,
indexing motion, and tool wear. Clean the registration sensor, inspect the
cutting station, and perform a dry verification cycle before product restart.""",
    "mixer_operation": """# High Shear Mixer Operation Manual

## Motor overload and vibration

Motor overload can indicate product buildup, excessive load, blade interference,
or mechanical drag. Stop safely, inspect impeller and chopper clearances, review
current trend, and confirm the recipe load. Abnormal vibration requires a blade,
bearing, and fastener inspection before reuse.

## Seal leaks

Leaks around the shaft seal require review of seal wear, cleaning history,
pressure differential, and shaft condition. Replace damaged seals under the
maintenance procedure and leak test before product contact.

## Batch consistency

Inconsistent granulation can follow recipe mismatch, chopper speed drift,
incorrect addition timing, or blade wear. Compare set points with the batch
record, verify speed feedback, and document any corrected recipe parameter.""",
}


def main():
    output_dir = Path("data/manuals")
    output_dir.mkdir(parents=True, exist_ok=True)
    llm_available = True
    for slug, title, topics in TOPICS:
        print(f"Generating: {title}")
        content = ""
        if llm_available:
            try:
                response = client.chat(
                    messages=[
                        {"role": "system", "content": "You write technical manuals."},
                        {
                            "role": "user",
                            "content": PROMPT.format(title=title, topics=topics),
                        },
                    ],
                    temperature=0.5,
                    max_tokens=4096,
                )
                content = response.choices[0].message.content or ""
            except Exception as error:
                print(f"  ! LLM generation unavailable: {type(error).__name__}")
                llm_available = False
        if not content:
            content = FALLBACK_MANUALS[slug]
            print("  -> using offline demo fallback")
        (output_dir / f"{slug}.md").write_text(content)
        print(f"  -> {len(content)} chars")


if __name__ == "__main__":
    main()
