"""
Synthetic support ticket data generator.
Generates 100 realistic tickets with balanced categories, varied tones, churn signals, and VIP markers.
"""

import csv
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict

# Category distribution (totals to 100)
CATEGORIES = {
    "Billing": 15,
    "Technical": 20,
    "Account": 15,
    "Shipping": 10,
    "Refund": 10,
    "Feature Request": 15,
    "Security": 10,
    "General Inquiry": 5,
}

SUBCATEGORIES = {
    "Billing": ["duplicate charge", "wrong amount", "refund request", "subscription cancel"],
    "Technical": ["login issue", "app crash", "slow performance", "feature not working"],
    "Account": ["password reset", "account locked", "email change", "profile update"],
    "Shipping": ["delayed delivery", "wrong item", "damaged package", "tracking issue"],
    "Refund": ["refund status", "partial refund", "refund denied"],
    "Feature Request": ["new feature ask", "improvement suggestion", "integration request"],
    "Security": ["suspicious activity", "data breach concern", "2FA issue", "account hacked"],
    "General Inquiry": ["misc"],
}

TONES = ["angry", "frustrated", "neutral", "polite", "urgent"]
TONE_WEIGHTS = [0.15, 0.25, 0.30, 0.20, 0.10]

CHANNELS = ["email", "chat", "web", "phone"]

# Realistic ticket templates by category
TICKET_TEMPLATES = {
    "Billing": [
        "I was charged twice for my subscription this month. My account shows two transactions of ${amount} on {date}. I need this fixed immediately as it's affecting my bank balance. This is the second time this has happened.",
        "The amount charged to my card doesn't match what was advertised. I signed up for the ${advertised} plan but was charged ${actual}. Your pricing is misleading and I want a refund for the difference.",
        "I've been trying to get a refund for over two weeks now. I cancelled my subscription within the trial period but still got charged. This is unacceptable customer service.",
        "I need to cancel my subscription but the cancel button doesn't work on the website. I've tried multiple times and it keeps giving me an error. Please help me cancel before the next billing cycle.",
        "There's an unauthorized charge on my account from last week. I didn't authorize this transaction and I want it reversed immediately. This better not affect my credit score.",
    ],
    "Technical": [
        "I can't log into my account for the past 3 hours. The password reset email never arrives. I've checked spam folder multiple times. I need to access my data urgently for a presentation.",
        "The mobile app crashes every time I try to open the dashboard. I'm using iOS {version} and this started after the latest update. I've tried reinstalling but nothing works.",
        "The website is incredibly slow today. Pages take over 30 seconds to load. This is affecting my team's productivity and we're considering switching to a competitor if this continues.",
        "The export feature stopped working yesterday. When I click export, nothing happens. I have a deadline tomorrow and desperately need to export my data. Please fix this ASAP.",
        "I've been locked out of my account after entering the correct password. The system says my credentials are invalid but I know they're right. This is extremely frustrating.",
    ],
    "Account": [
        "I need to reset my password but the reset link expires before I can use it. I've requested it 5 times already. Can you please send a link that actually works?",
        "My account has been locked and I don't know why. I haven't violated any terms. I need access for work tomorrow morning. This is a critical issue for my business.",
        "I need to change the email on my account but there's no option in settings. The old email is being decommissioned by my company. Please help me update this urgently.",
        "Someone changed my profile information without authorization. My phone number and address are different from what I set. I'm concerned about account security.",
        "I've been trying to update my profile picture for days. The upload keeps failing with a generic error. Is there a file size limit that's not documented?",
    ],
    "Shipping": [
        "My order was supposed to arrive 5 days ago. The tracking hasn't updated in a week. I paid for express shipping and this is completely unacceptable. I need this delivered by tomorrow.",
        "I received the wrong item in my package. I ordered product X but got product Y. I need the correct item shipped immediately and a prepaid return label for this mistake.",
        "The package arrived completely damaged. The box was crushed and the product inside is broken. I want either a replacement or full refund. This is very disappointing.",
        "The tracking number you provided doesn't work. It says 'invalid tracking ID' on the courier website. How am I supposed to know where my package is? This is poor communication.",
        "It's been 3 weeks and my international order still hasn't cleared customs. Your website said 7-10 business days. I need this for an event next week. What's happening?",
    ],
    "Refund": [
        "I submitted a refund request 2 weeks ago and haven't heard back. The status page just says 'processing'. How long does this take? I need that money back.",
        "I was only partially refunded. The amount in my account is less than what I was supposed to get back. There's a discrepancy of ${amount} that needs to be addressed.",
        "My refund was denied even though I qualify under your policy. I cancelled within the 30-day window. This is false advertising and I'm considering a chargeback.",
        "The refund was processed to the wrong account. I originally paid with credit card but the refund went to a different method. Please correct this immediately.",
        "I was told I'd receive my refund in 5-7 business days. It's been 15 days now. Your customer service keeps giving me different answers. I want a supervisor.",
    ],
    "Feature Request": [
        "I love your product but it really needs a dark mode option. My eyes strain when using it at night. This is a basic feature that all competitors already have.",
        "Could you add integration with Slack? Our team uses Slack for everything and having notifications there would improve our workflow significantly.",
        "The mobile app needs offline functionality. I travel frequently and lose connection often. Being able to work offline and sync later would be a game changer.",
        "Please add bulk edit capabilities. Editing items one by one is incredibly time-consuming when you have hundreds of entries. This is a major productivity killer.",
        "I'd like to see more customization options for the dashboard. Every team has different needs and a one-size-fits-all approach doesn't work for us.",
    ],
    "Security": [
        "I noticed login attempts from countries I've never visited. My account shows sign-ins from Russia and China. I've changed my password but I'm very concerned about a breach.",
        "I think there's been a data breach. I received a phishing email that knew specific details about my account. How did they get this information? This is serious.",
        "Two-factor authentication isn't working. I'm not receiving the SMS codes and the authenticator app shows invalid codes. I'm locked out of my own account.",
        "My account was hacked and the attacker changed all my information. I've lost access to everything. This is a nightmare scenario. I need immediate help recovering my account.",
        "I received a security alert about a password change I didn't make. I still have access but I'm worried someone else has my credentials. What should I do?",
    ],
    "General Inquiry": [
        "I'm evaluating your product for my company. Can you provide information about enterprise pricing and volume discounts? We're looking at 50+ seats.",
        "What's the difference between the Pro and Enterprise plans? The website isn't clear on the specific features. I need a detailed comparison.",
        "Do you offer educational discounts? I'm a student and would like to use this for my thesis project but the regular pricing is out of my budget.",
        "Is there an API available for third-party integrations? I'd like to build a custom connector for our internal tools.",
        "How do I become a partner or reseller in my region? I represent a consulting firm and want to offer your product to our clients.",
    ],
}

# Churn signal phrases to inject
CHURN_SIGNALS = [
    "I'm seriously considering cancelling my subscription",
    "This is making me look at competitors",
    "I've been a loyal customer for {years} years but this is testing my patience",
    "If this isn't resolved, I'm switching to {competitor}",
    "I'm done with this service. Where do I cancel?",
    "This is the last straw. I want my money back and I'm leaving",
    "My company is evaluating other options because of issues like this",
    "I recommended your product to colleagues but now I'm embarrassed",
]

# VIP markers to inject
VIP_MARKERS = [
    "I'm an enterprise customer on the Business plan",
    "As a premium subscriber, I expect better service",
    "Our company has a corporate account with you",
    "I'm on the highest tier plan and this is unacceptable",
    "We're a valued enterprise client with a dedicated account manager",
]


def generate_ticket_id() -> str:
    """Generate unique ticket ID."""
    return f"TKT-{random.randint(10000, 99999)}"


def generate_customer_id() -> str:
    """Generate customer ID."""
    return f"CUST-{random.randint(1000, 9999)}"


def generate_date() -> str:
    """Generate random date in past 30 days."""
    days_ago = random.randint(0, 30)
    date = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
    return date.strftime("%Y-%m-%d %H:%M:%S")


def generate_subject(category: str, tone: str) -> str:
    """Generate realistic subject line."""
    subjects = {
        "Billing": ["Urgent: Duplicate charge on my account", "Billing discrepancy", "Refund needed ASAP", "Unauthorized transaction", "Subscription cancellation issue"],
        "Technical": ["Cannot access my account", "App keeps crashing", "Extremely slow performance", "Feature broken", "Locked out - need help"],
        "Account": ["Password reset not working", "Account locked unexpectedly", "Need to update email", "Profile changed without permission", "Profile update failing"],
        "Shipping": ["Where is my order?", "Wrong item received", "Damaged package", "Tracking not working", "International shipping delay"],
        "Refund": ["Refund status inquiry", "Partial refund received", "Refund denied unfairly", "Refund to wrong account", "Refund overdue"],
        "Feature Request": ["Feature suggestion: dark mode", "Integration request: Slack", "Offline mode needed", "Bulk edit functionality", "Dashboard customization"],
        "Security": ["Suspicious login activity", "Possible data breach", "2FA not working", "Account hacked - need help", "Unauthorized password change"],
        "General Inquiry": ["Enterprise pricing inquiry", "Plan comparison question", "Student discount available?", "API documentation", "Partner program information"],
    }
    return random.choice(subjects.get(category, ["Support inquiry"]))


def generate_body(category: str, tone: str, include_churn: bool = False, include_vip: bool = False) -> str:
    """Generate realistic ticket body."""
    base_body = random.choice(TICKET_TEMPLATES.get(category, TICKET_TEMPLATES["General Inquiry"]))

    # Fill in template variables
    body = base_body.replace("{amount}", str(random.randint(50, 500)))
    body = body.replace("{date}", (datetime.now() - timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"))
    body = body.replace("{advertised}", str(random.randint(29, 99)))
    body = body.replace("{actual}", str(random.randint(59, 199)))
    body = body.replace("{version}", f"{random.randint(14, 17)}.{random.randint(0, 5)}")
    body = body.replace("{years}", str(random.randint(1, 5)))
    body = body.replace("{competitor}", random.choice(["CompetitorX", "RivalCorp", "AltService", "OtherBrand"]))

    # Add tone modifiers
    tone_prefixes = {
        "angry": "This is absolutely ridiculous! ",
        "frustrated": "I'm really frustrated at this point. ",
        "neutral": "",
        "polite": "Hi, I hope you can help me with this. ",
        "urgent": "URGENT - NEED IMMEDIATE ASSISTANCE! ",
    }

    tone_suffixes = {
        "angry": " Fix this NOW or there will be consequences!",
        "frustrated": " I really hope this gets resolved soon because I'm at my wit's end.",
        "neutral": " Thanks for looking into this.",
        "polite": " Thank you so much for your help!",
        "urgent": " Please respond within the hour!",
    }

    body = tone_prefixes.get(tone, "") + body + tone_suffixes.get(tone, "")

    # Add churn signal
    if include_churn:
        churn_phrase = random.choice(CHURN_SIGNALS)
        churn_phrase = churn_phrase.replace("{years}", str(random.randint(1, 5)))
        churn_phrase = churn_phrase.replace("{competitor}", random.choice(["CompetitorX", "RivalCorp", "AltService"]))
        body += f" {churn_phrase}"

    # Add VIP marker
    if include_vip:
        vip_marker = random.choice(VIP_MARKERS)
        body = vip_marker + ". " + body

    return body


def generate_synthetic_tickets(num_tickets: int = 100) -> List[Dict]:
    """Generate synthetic support tickets."""
    tickets = []

    # Calculate tickets per category
    category_list = []
    for category, count in CATEGORIES.items():
        category_list.extend([category] * count)

    random.shuffle(category_list)

    for i in range(num_tickets):
        category = category_list[i] if i < len(category_list) else random.choice(list(CATEGORIES.keys()))
        subcategory = random.choice(SUBCATEGORIES[category])
        tone = random.choices(TONES, weights=TONE_WEIGHTS)[0]
        channel = random.choice(CHANNELS)

        # 20% churn risk, 10% VIP
        include_churn = random.random() < 0.20
        include_vip = random.random() < 0.10

        # Priority hint based on category and tone
        priority_hint = "low"
        if category == "Security" or tone in ["angry", "urgent"]:
            priority_hint = "high"
        elif category in ["Billing", "Technical"] and tone == "frustrated":
            priority_hint = "medium"

        # Churn risk hint
        churn_risk_hint = "high" if include_churn else ("medium" if tone in ["angry", "frustrated"] else "low")

        ticket = {
            "ticket_id": generate_ticket_id(),
            "customer_id": generate_customer_id(),
            "channel": channel,
            "category": category,
            "subcategory": f"{category} > {subcategory}",
            "priority_hint": priority_hint,
            "churn_risk_hint": churn_risk_hint,
            "subject": generate_subject(category, tone),
            "body": generate_body(category, tone, include_churn, include_vip),
            "created_at": generate_date(),
        }
        tickets.append(ticket)

    return tickets


def save_tickets_to_csv(tickets: List[Dict], filepath: str) -> None:
    """Save tickets to CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    fieldnames = [
        "ticket_id", "customer_id", "channel", "category", "subcategory",
        "priority_hint", "churn_risk_hint", "subject", "body", "created_at"
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tickets)


def generate_and_save(filepath: str = "data/synthetic_tickets.csv", num_tickets: int = 100) -> str:
    """Generate synthetic tickets and save to CSV."""
    tickets = generate_synthetic_tickets(num_tickets)
    save_tickets_to_csv(tickets, filepath)
    return filepath


if __name__ == "__main__":
    filepath = generate_and_save()
    print(f"Generated {filepath} with 100 synthetic tickets")
