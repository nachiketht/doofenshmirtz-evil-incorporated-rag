"""Facilities."""

FAC = "Facilities"

PARKING_V1 = [
    (
        "Purpose",
        "This policy assigns parking spaces and blimp docking slots at Doofenshmirtz "
        "Evil Incorporated headquarters, the tall purple building you cannot miss "
        "anywhere in the Tri-State Area.",
    ),
    (
        "Scope",
        "This policy applies to every car, scooter, hovercraft and blimp arriving at "
        "headquarters.",
    ),
    (
        "Car Parking",
        [
            (
                "Assigned Spaces",
                "Parking spaces are assigned by seniority. The CEO's space is the one "
                "closest to the door and is painted with a large letter D.",
            ),
            (
                "Visitor Parking",
                "Visitors park in the three spaces nearest the giant neon sign. "
                "Visitors arriving in a flying car must use the roof.",
            ),
        ],
    ),
    (
        "Blimp Docking",
        [
            (
                "Docking Slots",
                "The roof has two blimp docking slots. The company blimp has permanent "
                "priority on slot one.",
            ),
            (
                "Docking Time",
                "Guest blimps may dock for up to 2 hours. Blimps left longer are "
                "deflated and folded by Facilities.",
            ),
        ],
    ),
    (
        "Towing",
        "Vehicles parked in the CEO's space are towed immediately. Hovercraft are "
        "pushed gently instead, because they do not tow well. An inator parked "
        "in a car space is towed to the lab.",
    ),
    (
        "Acknowledgment",
        "Parking at headquarters constitutes acknowledgment of this policy.",
    ),
]

ANIMAL_V1 = [
    (
        "Purpose",
        "This policy governs animals visiting headquarters. It exists for a reason "
        "that everyone knows and nobody will say out loud.",
    ),
    (
        "Scope",
        "This policy applies to pets, service animals, minion mascots, and any "
        "animal that arrives by crashing through a skylight.",
    ),
    (
        "Pet Visits",
        [
            (
                "Bring Your Pet Day",
                "Employees may bring a pet to work on the first Friday of each month. "
                "Pets must be leashed, crated, or otherwise contained.",
            ),
            (
                "Prohibited Animals",
                "Prohibited animals include sharks, alligators, and any animal "
                "wearing a hat.",
            ),
        ],
    ),
    (
        "Platypus Sightings",
        [
            (
                "Reporting",
                "Any platypus seen inside the building must be reported to Facilities "
                "at once, with a description of its hat, if any.",
            ),
            (
                "Response",
                "Employees should not approach the platypus. They should calmly move "
                "away from any inator and alert the CEO, who will want to know.",
            ),
        ],
    ),
    (
        "Allergies",
        "Employees with allergies may request a pet-free floor. The seventh floor is "
        "permanently pet-free, except for the ooze, which is not technically a pet.",
    ),
    (
        "Acknowledgment",
        "Bringing an animal to work constitutes acknowledgment of this policy.",
    ),
]

FAMILIES = [
    {
        "name": "Building and Lair Maintenance Policy",
        "department": FAC,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-02-26",
                "format": "docx",
                "sections": [
                    (
                        "Purpose",
                        "This policy keeps the headquarters building, the volcano lair "
                        "and the backup lair in working order, despite the company's "
                        "habit of exploding things.",
                    ),
                    (
                        "Scope",
                        "This policy covers all company buildings, lairs, secret "
                        "passages and trap doors.",
                    ),
                    (
                        "Maintenance Requests",
                        [
                            (
                                "Request Process",
                                "Maintenance requests are submitted through the Facilities "
                                "portal. Requests shouted from a trap door are not logged.",
                            ),
                            (
                                "Response Times",
                                "Facilities responds to urgent requests within 4 hours and "
                                "to routine requests within 5 business days.",
                            ),
                        ],
                    ),
                    (
                        "Trap Doors",
                        [
                            (
                                "Inspection",
                                "Every trap door is inspected monthly. A trap door that "
                                "opens on its own is classified as urgent.",
                            ),
                            (
                                "Signage",
                                "Trap doors in public hallways must not be marked, which "
                                "Facilities admits is a safety concern.",
                            ),
                        ],
                    ),
                    (
                        "Lair Cleaning",
                        "The volcano lair is cleaned weekly. Lava is not considered a "
                        "cleaning product.",
                    ),
                    (
                        "Acknowledgment",
                        "Occupying any company building constitutes acknowledgment of "
                        "this policy.",
                    ),
                ],
            },
            {
                "version": "2.0",
                "date": "2025-04-07",
                "format": "md",
                "base": "1.0",
                "purpose": "Version 2.0 speeds up urgent repairs and finally adds signs "
                "for trap doors, after the third visitor fell into the alligator pit.",
                "replace": {
                    "Maintenance Requests": (
                        "Maintenance Requests",
                        [
                            (
                                "Request Process",
                                "Maintenance requests are submitted through the Facilities "
                                "portal or by pressing the big purple help button.",
                            ),
                            (
                                "Response Times",
                                "Facilities now responds to urgent requests within 1 hour, "
                                "down from 4 hours, and to routine requests within 3 "
                                "business days.",
                            ),
                        ],
                    ),
                    "Trap Doors": (
                        "Trap Doors",
                        [
                            (
                                "Inspection",
                                "Every trap door is inspected weekly. Trap doors over the "
                                "alligator pit are inspected daily.",
                            ),
                            (
                                "Signage",
                                "Trap doors in public hallways must now be marked with a "
                                "small sign reading 'Probably Fine'.",
                            ),
                        ],
                    ),
                },
            },
        ],
    },
    {
        "name": "Parking and Blimp Docking Policy",
        "department": FAC,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-03-11",
                "format": "pdf",
                "sections": PARKING_V1,
            },
            {
                "version": "2.0",
                "date": "2025-03-24",
                "format": "docx",
                "base": "1.0",
                "purpose": "Version 2.0 shortens guest blimp docking and adds electric "
                "vehicle charging, because the Charge-Everything-inator kept charging "
                "the wrong cars.",
                "replace": {
                    "Blimp Docking": (
                        "Blimp Docking",
                        [
                            (
                                "Docking Slots",
                                "The roof still has two blimp docking slots, and the "
                                "company blimp keeps priority on slot one.",
                            ),
                            (
                                "Docking Time",
                                "Guest blimps may now dock for up to 1 hour, down from 2 "
                                "hours, because the slot was being used as a sky lounge.",
                            ),
                        ],
                    )
                },
                "add": [
                    (
                        "Electric Vehicle Charging",
                        "Four charging stations are available in the garage. Charging "
                        "an inator at a car charger is prohibited.",
                    )
                ],
            },
            {
                "version": "3.0",
                "date": "2026-03-09",
                "format": "md",
                "base": "2.0",
                "purpose": "Version 3.0 adds a third docking slot and a jetpack landing "
                "pad, after the roof became the busiest airport in the Tri-State Area.",
                "replace": {
                    "Blimp Docking": (
                        "Blimp Docking",
                        [
                            (
                                "Docking Slots",
                                "The roof now has three blimp docking slots. Slot three "
                                "is reserved for visiting villains.",
                            ),
                            (
                                "Docking Time",
                                "Guest blimps may dock for up to 1 hour. Overstaying "
                                "blimps are now towed by the company blimp, slowly and "
                                "dramatically.",
                            ),
                        ],
                    )
                },
                "add": [
                    (
                        "Jetpack Landing",
                        "Jetpacks land only on the marked pad on the north side of the "
                        "roof. Landing in the smoking area is considered rude.",
                    )
                ],
            },
        ],
    },
    {
        "name": "Animal Visitor Policy",
        "department": FAC,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-04-15",
                "format": "md",
                "sections": ANIMAL_V1,
            },
            {
                "version": "2.0",
                "date": "2025-05-19",
                "format": "pdf",
                "base": "1.0",
                "purpose": "Version 2.0 tightens the hat rule after a platypus entered the "
                "building simply by removing its fedora at the door.",
                "replace": {
                    "Pet Visits": (
                        "Pet Visits",
                        [
                            (
                                "Bring Your Pet Day",
                                "Bring Your Pet Day moves to the last Friday of each month "
                                "so that it no longer coincides with inator testing.",
                            ),
                            (
                                "Prohibited Animals",
                                "Prohibited animals include sharks, alligators, and any "
                                "animal that has ever worn a hat, even if it is not "
                                "wearing one now.",
                            ),
                        ],
                    )
                },
            },
            {
                "version": "3.0",
                "date": "2026-04-13",
                "format": "docx",
                "base": "2.0",
                "purpose": "Version 3.0 adds a visitor badge for animals, because nobody "
                "could tell which platypus was a pet and which was a secret agent.",
                "add": [
                    (
                        "Animal Badges",
                        "Every visiting animal receives a laminated badge with its "
                        "name and owner. Animals that arrive without an owner are "
                        "escorted to the lobby and offered a snack while Facilities "
                        "calls the CEO.",
                    )
                ],
            },
        ],
    },
]
