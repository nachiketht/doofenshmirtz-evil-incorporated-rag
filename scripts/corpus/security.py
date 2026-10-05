"""IT Security."""

SEC = "IT Security"

PASSWORD_V1 = [
    (
        "Purpose",
        "This policy keeps company systems secure against hackers, rival villains, "
        "and semi-aquatic mammals who are suspiciously good with keyboards.",
    ),
    (
        "Scope",
        "This policy applies to every account on every company system, including the "
        "inator control panels and the Norm-bot maintenance terminal.",
    ),
    (
        "Password Rules",
        [
            (
                "Length",
                "Passwords must be at least 8 characters long. The word 'curses' may not "
                "appear in any password, because it is the first thing anyone guesses.",
            ),
            (
                "Rotation",
                "Passwords must be changed every 90 days. Reusing a password from the "
                "previous three rotations is prohibited.",
            ),
            (
                "Banned Passwords",
                "Banned passwords include 'password', 'perry', 'platypus', 'vanessa', "
                "and the name of any inator currently under construction.",
            ),
        ],
    ),
    (
        "Badge Access",
        [
            (
                "Badge Display",
                "Employee badges must be visible at all times inside the building. "
                "Badges worn on a fedora do not count as visible.",
            ),
            (
                "Tailgating",
                "Employees may not hold secure doors open for anyone, including adorable "
                "teal animals who appear to be lost.",
            ),
        ],
    ),
    (
        "Lost Devices",
        "Lost laptops and phones must be reported to IT Security within 24 hours. "
        "Devices lost inside an inator's blast radius must be reported immediately.",
    ),
    (
        "Acknowledgment",
        "Logging in to any company system constitutes acknowledgment of this policy "
        "and a promise not to write your password on a sticky note shaped like a "
        "platypus.",
    ),
]

FAMILIES = [
    {
        "name": "Password and Access Policy",
        "department": SEC,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-01-22",
                "format": "docx",
                "sections": PASSWORD_V1,
            },
            {
                "version": "2.0",
                "date": "2025-02-17",
                "format": "pdf",
                "base": "1.0",
                "purpose": "Version 2.0 lengthens passwords and adds multi-factor login, "
                "after a penetration test revealed that the master inator console's "
                "password was 'doof123'.",
                "replace": {
                    "Password Rules": (
                        "Password Rules",
                        [
                            (
                                "Length",
                                "Passwords must now be at least 12 characters long, up from "
                                "8 characters. Passphrases made of four random words are "
                                "encouraged.",
                            ),
                            (
                                "Rotation",
                                "Passwords must be changed every 90 days, and may not "
                                "reuse any of the previous five passwords.",
                            ),
                            (
                                "Banned Passwords",
                                "The banned list adds 'doof123', 'gimmelshtump', and any "
                                "password containing the CEO's birthday.",
                            ),
                        ],
                    )
                },
                "add": [
                    (
                        "Multi-Factor Authentication",
                        [
                            (
                                "Requirement",
                                "Multi-factor authentication is required for email, the "
                                "inator control panels, and the payroll system.",
                            ),
                            (
                                "Approved Second Factors",
                                "Approved second factors are an authenticator app or a "
                                "hardware key. Answering a riddle posed by Norm is not an "
                                "approved second factor.",
                            ),
                        ],
                    )
                ],
            },
            {
                "version": "3.0",
                "date": "2026-02-16",
                "format": "md",
                "base": "2.0",
                "purpose": "Version 3.0 drops forced password rotation in line with "
                "modern guidance and introduces retinal scanners, which were already "
                "installed for dramatic effect and are now finally plugged in.",
                "replace": {
                    "Password Rules": (
                        "Password Rules",
                        [
                            (
                                "Length",
                                "Passwords must be at least 14 characters long. Four-word "
                                "passphrases remain encouraged.",
                            ),
                            (
                                "Rotation",
                                "Scheduled 90-day rotation is abolished. Passwords must be "
                                "changed only when a compromise is suspected, or when a "
                                "platypus was seen near your desk.",
                            ),
                            (
                                "Banned Passwords",
                                "The banned list is now checked automatically against a "
                                "list of known breached passwords and every inator name.",
                            ),
                        ],
                    )
                },
                "add": [
                    (
                        "Retinal Scanners",
                        "Retinal scanners now guard the server room and the inator "
                        "vault. Employees wearing an eye patch for dramatic effect must "
                        "remove it before scanning.",
                    )
                ],
            },
        ],
    },
    {
        "name": "Acceptable Use of Inator Network Policy",
        "department": SEC,
        "versions": [
            {
                "version": "1.0",
                "date": "2024-05-06",
                "format": "pdf",
                "sections": [
                    (
                        "Purpose",
                        "This policy explains what employees may and may not do on the "
                        "Inator Network, the company's internal network connecting every "
                        "inator, laptop, and smart toaster in the building.",
                    ),
                    (
                        "Scope",
                        "This policy applies to every device connected to the Inator "
                        "Network, including personal phones on the guest network.",
                    ),
                    (
                        "Permitted Use",
                        [
                            (
                                "Business Use",
                                "The network is for company business, including research, "
                                "scheming, and watching instructional videos about lasers.",
                            ),
                            (
                                "Personal Use",
                                "Limited personal use is allowed during breaks, provided it "
                                "does not slow down any inator currently charging.",
                            ),
                        ],
                    ),
                    (
                        "Prohibited Use",
                        [
                            (
                                "Streaming",
                                "Streaming video on the inator subnet is prohibited, because "
                                "it once caused the Shrink-inator to buffer mid-shrink.",
                            ),
                            (
                                "Remote Control",
                                "Connecting an inator to the public internet is prohibited. "
                                "Remote control of inators is allowed only from inside the "
                                "building.",
                            ),
                        ],
                    ),
                    (
                        "Monitoring",
                        "IT Security monitors network traffic for threats. Traffic to "
                        "websites about platypus care is flagged for review.",
                    ),
                    (
                        "Acknowledgment",
                        "Connecting to the Inator Network constitutes acknowledgment of "
                        "this policy.",
                    ),
                ],
            },
            {
                "version": "2.0",
                "date": "2025-06-02",
                "format": "docx",
                "base": "1.0",
                "purpose": "Version 2.0 adds rules for AI assistants and smart devices "
                "after the office smart fridge joined a botnet and began ordering "
                "pickles.",
                "add": [
                    (
                        "AI Assistants",
                        [
                            (
                                "Approved Assistants",
                                "Only IT-approved AI assistants may be used for company "
                                "work. Assistants may not be asked to design inators "
                                "without a human reviewing the blueprint.",
                            ),
                            (
                                "Confidential Prompts",
                                "Employees may not paste confidential evil plans into "
                                "public chatbots, no matter how good the chatbot is at "
                                "naming inators.",
                            ),
                        ],
                    ),
                    (
                        "Smart Devices",
                        "Smart appliances must be registered with IT Security and placed "
                        "on an isolated subnet. Any appliance found ordering pickles is "
                        "disconnected immediately.",
                    ),
                ],
            },
        ],
    },
]
