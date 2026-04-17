#!/usr/bin/env python3
"""Generate USPTO demo PowerPoint deck — clean, validated approach."""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.enum.shapes import MSO_SHAPE_TYPE
import pptx.oxml

# ── colours ────────────────────────────────────────────────────────────────────
NAVY   = RGBColor(0x23, 0x2F, 0x3E)
ORANGE = RGBColor(0xFF, 0x99, 0x00)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
LGRAY  = RGBColor(0xF2, 0xF2, 0xF2)
DGRAY  = RGBColor(0x44, 0x44, 0x44)
MGRAY  = RGBColor(0x88, 0x88, 0x88)
RED    = RGBColor(0xC0, 0x39, 0x2B)
GREEN  = RGBColor(0x1E, 0x8E, 0x4C)
BLUE   = RGBColor(0x00, 0x73, 0xBB)
PURPLE = RGBColor(0x7B, 0x2D, 0x8B)
DGREEN = RGBColor(0x1A, 0x5F, 0x3C)

SCREENS = os.path.join(os.path.dirname(__file__), "..", "mock_screens")
OUT     = os.path.join(os.path.dirname(__file__), "..", "presentation", "aws-health-tracker-deck.pptx")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]   # blank layout


# ── primitive helpers ──────────────────────────────────────────────────────────

def rect(slide, l, t, w, h, fill_rgb=None, line_rgb=None, line_pt=0.75):
    """Add a plain rectangle. fill_rgb=None means transparent background."""
    from pptx.util import Pt as _Pt
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    shp = slide.shapes.add_shape(
        1,  # MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE=5, RECTANGLE=1
        l, t, w, h
    )
    shp.line.fill.background()  # no line by default
    if fill_rgb is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill_rgb
    if line_rgb:
        shp.line.color.rgb = line_rgb
        shp.line.width = _Pt(line_pt)
    else:
        shp.line.fill.background()
    return shp


def txt(slide, l, t, w, h, text, size=16, bold=False,
        color=WHITE, align=PP_ALIGN.LEFT, italic=False, wrap=True):
    """Add a textbox."""
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    para = tf.paragraphs[0]
    para.alignment = align
    run = para.add_run()
    run.text = text
    run.font.size   = Pt(size)
    run.font.bold   = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return tb


def img(slide, path, l, t, w, h):
    if os.path.exists(path):
        slide.shapes.add_picture(path, l, t, w, h)


def header(slide, title, subtitle=None):
    """Navy header bar + orange underline."""
    rect(slide, 0, 0, prs.slide_width, Inches(1.15), fill_rgb=NAVY)
    rect(slide, 0, Inches(1.15), prs.slide_width, Inches(0.055), fill_rgb=ORANGE)
    txt(slide, Inches(0.4), Inches(0.12), Inches(10), Inches(0.6),
        title, size=26, bold=True, color=WHITE)
    if subtitle:
        txt(slide, Inches(0.4), Inches(0.7), Inches(11.5), Inches(0.38),
            subtitle, size=12, color=ORANGE)


def footer(slide):
    rect(slide, 0, Inches(7.12), prs.slide_width, Inches(0.38), fill_rgb=NAVY)
    txt(slide, Inches(0.3), Inches(7.15), Inches(9), Inches(0.3),
        "AWS Health Notifications Tracker  |  USPTO AWS Innovation Team",
        size=9, color=MGRAY)
    txt(slide, Inches(10.5), Inches(7.15), Inches(2.5), Inches(0.3),
        "April 2026", size=9, color=MGRAY, align=PP_ALIGN.RIGHT)


def card(slide, l, t, w, h, title, body,
         title_bg=NAVY, title_fg=WHITE, body_bg=LGRAY, body_fg=DGRAY,
         title_size=12, body_size=10):
    rect(slide, l, t, w, Inches(0.4), fill_rgb=title_bg)
    txt(slide, l + Inches(0.1), t + Inches(0.05), w - Inches(0.15),
        Inches(0.35), title, size=title_size, bold=True, color=title_fg)
    rect(slide, l, t + Inches(0.4), w, h - Inches(0.4), fill_rgb=body_bg,
         line_rgb=RGBColor(0xCC, 0xCC, 0xCC))
    txt(slide, l + Inches(0.1), t + Inches(0.48), w - Inches(0.18),
        h - Inches(0.56), body, size=body_size, color=body_fg, wrap=True)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — Title
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
# full background
rect(s, 0, 0, prs.slide_width, prs.slide_height, fill_rgb=NAVY)
# left accent bar
rect(s, 0, 0, Inches(0.2), prs.slide_height, fill_rgb=ORANGE)
# title
txt(s, Inches(0.55), Inches(1.5), Inches(11.5), Inches(1.2),
    "AWS Health Notifications Tracker",
    size=40, bold=True, color=WHITE)
# orange rule
rect(s, Inches(0.55), Inches(2.9), Inches(10), Inches(0.07), fill_rgb=ORANGE)
# subtitle
txt(s, Inches(0.55), Inches(3.1), Inches(11.5), Inches(0.7),
    "Centralized Visibility & AI-Powered Insights for 200+ Account AWS Organizations",
    size=20, color=RGBColor(0xCC, 0xCC, 0xCC))
# meta
txt(s, Inches(0.55), Inches(4.5), Inches(9), Inches(0.45),
    "Demo Presentation  |  USPTO AWS Innovation Team  |  April 2026",
    size=14, color=ORANGE)
# badge
rect(s, Inches(10.5), Inches(6.4), Inches(2.5), Inches(0.7), fill_rgb=ORANGE)
txt(s, Inches(10.5), Inches(6.45), Inches(2.5), Inches(0.55),
    "Powered by AWS", size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — The Problem
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
header(s, "The Challenge",
       "Managing AWS Health events at scale across a large AWS Organization")
footer(s)

problems = [
    ("Missed Deadlines",
     "Critical maintenance windows and deprecation notices are buried in 200 individual account "
     "dashboards. There is no organization-wide view, so teams regularly miss required actions."),
    ("Manual, Fragmented Tracking",
     "Operations teams must manually check each account in the AWS Console. Spreadsheets used "
     "to track follow-up status become stale within hours and have no ownership workflow."),
    ("No Prioritization or AI Assistance",
     "Raw AWS Health events contain dense technical text with no plain-English summary. Teams "
     "cannot distinguish Critical from Low urgency at a glance, and there is no automated "
     "action recommendation."),
]

y = Inches(1.35)
for title, body in problems:
    rect(s, Inches(0.35), y, Inches(0.07), Inches(1.3), fill_rgb=ORANGE)
    rect(s, Inches(0.42), y, Inches(12.5), Inches(1.3),
         fill_rgb=LGRAY, line_rgb=RGBColor(0xDD, 0xDD, 0xDD))
    txt(s, Inches(0.6), y + Inches(0.1), Inches(12), Inches(0.4),
        title, size=15, bold=True, color=NAVY)
    txt(s, Inches(0.6), y + Inches(0.5), Inches(12), Inches(0.72),
        body, size=12, color=DGRAY, wrap=True)
    y += Inches(1.45)

rect(s, Inches(0.35), y + Inches(0.1), Inches(12.5), Inches(0.5), fill_rgb=RED)
txt(s, Inches(0.55), y + Inches(0.13), Inches(12), Inches(0.38),
    "Result: Compliance risk, reactive operations, and engineer burnout from manual account monitoring.",
    size=12, bold=True, color=WHITE)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — Solution Overview
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
header(s, "Solution: AWS Health Notifications Tracker",
       "Automated collection  •  AI summarization  •  Deadline tracking  •  Follow-up workflow")
footer(s)

cols = [
    (NAVY,   "Automated Collection",
     "EventBridge triggers Health Collector Lambda every 15 minutes. "
     "AWS Organizations Health API aggregates events from all 200 accounts automatically."),
    (BLUE,   "AI Summarization",
     "Amazon Bedrock (Claude Haiku) converts raw AWS API events into plain-English summaries, "
     "step-by-step action items, urgency scores, and extracted deadlines."),
    (DGREEN, "Centralized Dashboard",
     "React SPA on CloudFront shows stats cards, service/urgency charts, sortable event list, "
     "and deadline countdowns — all accounts in a single view."),
    (PURPLE, "Proactive Reminders",
     "Daily SNS email digest for events with deadlines within 7 days. "
     "Critical events re-escalate at 3 days remaining."),
    (RGBColor(0xA0, 0x52, 0x2D), "Follow-up Workflow",
     "Per-event owner assignment, status tracking (Pending / In Progress / Resolved), "
     "and free-text notes — persisted to DynamoDB and visible org-wide."),
]

x = Inches(0.25)
cw = Inches(2.5)
for bg, title, body in cols:
    rect(s, x, Inches(1.38), cw, Inches(5.35), fill_rgb=WHITE,
         line_rgb=RGBColor(0xCC, 0xCC, 0xCC))
    rect(s, x, Inches(1.38), cw, Inches(0.5), fill_rgb=bg)
    txt(s, x + Inches(0.1), Inches(1.42), cw - Inches(0.15), Inches(0.42),
        title, size=12, bold=True, color=WHITE)
    txt(s, x + Inches(0.1), Inches(1.95), cw - Inches(0.18), Inches(4.5),
        body, size=11, color=DGRAY, wrap=True)
    x += Inches(2.6)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — Architecture Diagram (text-box based, no connectors)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
header(s, "Architecture",
       "Serverless  •  FedRAMP Authorized  •  us-east-1  •  ~$10–15/month")
footer(s)

BW, BH = Inches(2.0), Inches(0.65)

def abox(sl, l, t, label, sub="", bg=NAVY):
    rect(sl, l, t, BW, BH, fill_rgb=bg)
    txt(sl, l + Inches(0.07), t + Inches(0.05), BW - Inches(0.12),
        Inches(0.33), label, size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    if sub:
        txt(sl, l + Inches(0.07), t + Inches(0.35), BW - Inches(0.12),
            Inches(0.26), sub, size=8, color=ORANGE, align=PP_ALIGN.CENTER)

def arr(sl, l, t, w, h, horiz=True):
    """Draw a thin orange arrow line."""
    rect(sl, l, t, w, h, fill_rgb=ORANGE)

# Column x positions
C1, C2, C3, C4, C5 = Inches(0.25), Inches(2.7), Inches(5.15), Inches(7.6), Inches(10.05)
# Row y positions
R1, R2, R3, R4 = Inches(1.42), Inches(2.35), Inches(3.28), Inches(4.55)

# Row 1 — collection pipeline
abox(s, C1, R1, "EventBridge", "rate(15 min)", bg=PURPLE)
arr(s,  C1+BW, R1+Inches(0.27), Inches(0.45), Inches(0.08))
abox(s, C2, R1, "health-collector", "Lambda  Python 3.12", bg=NAVY)
arr(s,  C2+BW, R1+Inches(0.27), Inches(0.45), Inches(0.08))
abox(s, C3, R1, "DynamoDB", "HealthEvents table", bg=DGREEN)
arr(s,  C3+BW, R1+Inches(0.27), Inches(0.45), Inches(0.08))
abox(s, C4, R1, "llm-summarizer", "Lambda  Python 3.12", bg=NAVY)
arr(s,  C4+BW, R1+Inches(0.27), Inches(0.45), Inches(0.08))
abox(s, C5, R1, "Amazon Bedrock", "Claude Haiku", bg=PURPLE)

# Downward arrows from DynamoDB → Stream label, and collector → S3
arr(s, C3+BW/2, R1+BH, Inches(0.08), Inches(0.25))

# Row 2 — streams label
txt(s, C3+Inches(0.5), R1+BH+Inches(0.27), Inches(1.0), Inches(0.25),
    "DynamoDB Streams", size=8, color=MGRAY, align=PP_ALIGN.CENTER)

# Downward from collector to S3 archive
arr(s, C2+BW/2, R1+BH, Inches(0.08), Inches(0.9))
abox(s, C2, R2+Inches(0.28), "S3 Archive", "Raw event JSON", bg=RGBColor(0x56, 0x7B, 0x1C))

# Row 2 — reminder pipeline
abox(s, C1, R2+Inches(0.28), "EventBridge", "cron(0 9 * * ?)", bg=PURPLE)
arr(s,  C1+BW, R2+Inches(0.28)+Inches(0.27), Inches(0.45), Inches(0.08))
abox(s, C2+Inches(2.45), R2+Inches(0.28), "deadline-reminder", "Lambda  Python 3.12", bg=NAVY)
arr(s,  C2+Inches(2.45)+BW, R2+Inches(0.28)+Inches(0.27), Inches(0.45), Inches(0.08))
abox(s, C4, R2+Inches(0.28), "SNS Topic", "Email digest", bg=RGBColor(0xE8, 0x55, 0x1B))

# Row 3 — API / Frontend
txt(s, C3+Inches(0.05), R3, Inches(1.9), Inches(0.28),
    "API reads from DynamoDB", size=8, color=MGRAY)
arr(s, C3+BW/2, R1+BH+Inches(1.65), Inches(0.08), Inches(0.55))
abox(s, C3, R3+Inches(0.3), "api-handler", "Lambda  Python 3.12", bg=NAVY)
arr(s,  C3+BW, R3+Inches(0.3)+Inches(0.27), Inches(0.45), Inches(0.08))
abox(s, C4, R3+Inches(0.3), "API Gateway", "HTTP API (open)", bg=RGBColor(0xA0, 0x52, 0x2D))
arr(s,  C4+BW, R3+Inches(0.3)+Inches(0.27), Inches(0.45), Inches(0.08))
abox(s, C5, R3+Inches(0.3), "CloudFront", "React SPA + S3", bg=BLUE)

# Users
txt(s, C5+Inches(0.3), R4, BW-Inches(0.3), Inches(0.28),
    "Users (browser)", size=9, bold=True, color=NAVY)
arr(s, C5+BW/2, R3+Inches(0.3)+BH, Inches(0.08), Inches(0.5))

# legend
legend_items = [
    (PURPLE, "EventBridge Scheduler"),
    (NAVY,   "Lambda Functions"),
    (DGREEN, "DynamoDB"),
    (BLUE,   "CloudFront / S3"),
    (RGBColor(0xA0,0x52,0x2D), "API Gateway"),
    (RGBColor(0xE8,0x55,0x1B), "SNS"),
]
lx = Inches(0.25)
for bg, label in legend_items:
    rect(s, lx, Inches(6.72), Inches(0.22), Inches(0.22), fill_rgb=bg)
    txt(s, lx + Inches(0.27), Inches(6.71), Inches(1.7), Inches(0.26),
        label, size=9, color=DGRAY)
    lx += Inches(2.1)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — AWS Services Table
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
header(s, "AWS Services Used",
       "All FedRAMP Authorized  •  us-east-1 commercial  •  No NAT Gateways, no always-on EC2")
footer(s)

table_data = [
    ("AWS Health API (Orgs)",  "Source of all health events across all accounts", "FedRAMP Auth", "~$0"),
    ("Lambda (x4)",            "health-collector, llm-summarizer, deadline-reminder, api-handler", "FedRAMP Auth", "~$1–2"),
    ("DynamoDB (on-demand)",   "Primary store — events, status, follow-up tracking", "FedRAMP Auth", "~$5–10"),
    ("Amazon Bedrock",         "Claude Haiku — plain-English summaries & action extraction", "FedRAMP Auth", "~$1–2"),
    ("S3 (x2 buckets)",        "Raw event archive + React SPA static assets", "FedRAMP Auth", "<$1"),
    ("CloudFront",             "CDN for React SPA with Origin Access Control", "FedRAMP Auth", "<$1"),
    ("API Gateway HTTP API",   "REST backend for the React frontend (no auth required)", "FedRAMP Auth", "~$1"),
    ("EventBridge Scheduler",  "rate(15 min) for collector + cron(09:00 UTC) for reminders", "FedRAMP Auth", "<$1"),
    ("SNS",                    "Deadline alert email digests to the ops team", "FedRAMP Auth", "<$1"),
    ("CloudWatch Logs",        "All Lambda logs with 30-day retention", "FedRAMP Auth", "<$1"),
]

CX = [Inches(0.3), Inches(2.55), Inches(9.55), Inches(11.6)]
CW = [Inches(2.2),  Inches(6.95),  Inches(2.0),   Inches(1.45)]
RH = Inches(0.43)
HDRS = ["Service", "Purpose", "FedRAMP Status", "Est./mo"]

y = Inches(1.35)
for ci, h in enumerate(HDRS):
    rect(s, CX[ci], y, CW[ci], Inches(0.38), fill_rgb=NAVY)
    txt(s, CX[ci]+Inches(0.06), y+Inches(0.05), CW[ci]-Inches(0.1),
        Inches(0.3), h, size=10, bold=True, color=WHITE)
y += Inches(0.38)

for ri, row in enumerate(table_data):
    bg = LGRAY if ri % 2 == 0 else WHITE
    for ci, cell in enumerate(row):
        rect(s, CX[ci], y, CW[ci], RH, fill_rgb=bg,
             line_rgb=RGBColor(0xDD, 0xDD, 0xDD))
        clr = GREEN if cell == "FedRAMP Auth" else DGRAY
        txt(s, CX[ci]+Inches(0.06), y+Inches(0.07), CW[ci]-Inches(0.1),
            RH-Inches(0.1), cell, size=9, color=clr)
    y += RH

rect(s, Inches(0.3), y+Inches(0.1), Inches(12.7), Inches(0.42), fill_rgb=NAVY)
txt(s, Inches(0.5), y+Inches(0.14), Inches(9), Inches(0.3),
    "Total estimated monthly cost at steady state (50K events, 200 accounts, 500 Bedrock calls):",
    size=10, bold=False, color=WHITE)
txt(s, Inches(10.0), y+Inches(0.14), Inches(3), Inches(0.3),
    "~$10–15 / month", size=12, bold=True, color=ORANGE, align=PP_ALIGN.RIGHT)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — Dashboard Screenshot
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
header(s, "Dashboard",
       "Real-time stats, urgency charts, and upcoming critical deadlines at a glance")
footer(s)
img(s, os.path.join(SCREENS, "01_dashboard.png"),
    Inches(0.3), Inches(1.3), Inches(12.7), Inches(5.7))
txt(s, Inches(0.3), Inches(7.03), Inches(12.5), Inches(0.26),
    "Stats cards  •  Events by Service bar chart  •  Events by Urgency chart  •  Top critical events table",
    size=9, color=MGRAY, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — Notifications List
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
header(s, "Notifications List",
       "All 200 accounts in one sortable, searchable table — with deadline countdowns")
footer(s)
img(s, os.path.join(SCREENS, "02_notification_list.png"),
    Inches(0.3), Inches(1.3), Inches(12.7), Inches(5.7))
txt(s, Inches(0.3), Inches(7.03), Inches(12.5), Inches(0.26),
    "Search  •  Filter by Service / Urgency / Status / Account  •  Deadline countdown  •  CSV export",
    size=9, color=MGRAY, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — Filtered View
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
header(s, "Intelligent Filtering",
       "Instantly surface Critical events across all accounts — filter by any dimension")
footer(s)
img(s, os.path.join(SCREENS, "03_notification_list_filtered.png"),
    Inches(0.3), Inches(1.3), Inches(12.7), Inches(5.7))
txt(s, Inches(0.3), Inches(7.03), Inches(12.5), Inches(0.26),
    "Filter to Critical urgency — all accounts — sorted by soonest deadline first",
    size=9, color=MGRAY, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — Event Detail + AI Summary
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
header(s, "AI-Generated Event Detail",
       "Amazon Bedrock (Claude Haiku) turns raw Health API events into actionable guidance")
footer(s)
img(s, os.path.join(SCREENS, "04_notification_detail.png"),
    Inches(0.3), Inches(1.3), Inches(7.8), Inches(5.7))

callouts = [
    (BLUE,   "Plain-English Summary",
     "2–3 sentence stakeholder-ready description generated by Claude Haiku via Amazon Bedrock."),
    (GREEN,  "Recommended Actions",
     "3–5 specific, step-by-step action items extracted from the raw event description."),
    (RED,    "Urgency + Deadline",
     "Auto-classified: Critical / High / Medium / Low. Deadline extracted in ISO 8601 format."),
    (NAVY,   "Follow-up Tracker",
     "Assign an owner, set status (Pending / In Progress / Resolved), add notes. Saved to DynamoDB."),
]

y = Inches(1.32)
for bg, title, body in callouts:
    rect(s, Inches(8.3), y, Inches(4.75), Inches(1.3), fill_rgb=bg)
    txt(s, Inches(8.45), y + Inches(0.08), Inches(4.5), Inches(0.38),
        title, size=12, bold=True, color=WHITE)
    txt(s, Inches(8.45), y + Inches(0.46), Inches(4.5), Inches(0.76),
        body, size=10, color=WHITE, wrap=True)
    y += Inches(1.38)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — Security & Compliance
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
header(s, "Security & Compliance",
       "FedRAMP Authorized services only  •  IAM least-privilege  •  No data leaves us-east-1")
footer(s)

sec_items = [
    ("FedRAMP Authorized Services Only",
     "Every AWS service used — Lambda, DynamoDB, S3, CloudFront, API Gateway, Bedrock, "
     "EventBridge, SNS, CloudWatch — is FedRAMP Authorized in us-east-1 commercial."),
    ("IAM Least-Privilege Roles",
     "Each of the four Lambda functions has a dedicated IAM execution role scoped to only "
     "the exact actions and resources it requires. No wildcard actions, no shared roles."),
    ("Encryption at Rest & in Transit",
     "DynamoDB tables encrypted with AWS-managed keys. S3 buckets use S3-managed encryption. "
     "All API traffic uses TLS 1.2+. CloudFront enforces HTTPS redirect."),
    ("No Public Access",
     "S3 frontend bucket is private — served exclusively through CloudFront with Origin Access "
     "Control. Archive S3 bucket blocks all public access. No public DynamoDB endpoints."),
    ("Audit & Observability",
     "All Lambda invocations log to CloudWatch with 30-day retention. DynamoDB Point-in-Time "
     "Recovery enabled. EventBridge Scheduler retries failed Lambda invocations automatically."),
]

y = Inches(1.35)
for title, body in sec_items:
    rect(s, Inches(0.3), y, Inches(0.1), Inches(1.05), fill_rgb=ORANGE)
    rect(s, Inches(0.4), y, Inches(12.55), Inches(1.05),
         fill_rgb=LGRAY, line_rgb=RGBColor(0xDD, 0xDD, 0xDD))
    txt(s, Inches(0.6), y + Inches(0.08), Inches(12), Inches(0.35),
        title, size=13, bold=True, color=NAVY)
    txt(s, Inches(0.6), y + Inches(0.43), Inches(12), Inches(0.55),
        body, size=10, color=DGRAY, wrap=True)
    y += Inches(1.13)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — Roadmap
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK)
header(s, "Roadmap & Next Steps",
       "Phase 2 enhancements to further reduce operational toil for USPTO cloud teams")
footer(s)

phases = [
    (GREEN,  "Phase 1  —  Complete",
     ["Automated event collection across all 200 accounts",
      "AI summaries and action items via Amazon Bedrock",
      "React dashboard: stats, filtering, search, CSV export",
      "Follow-up ownership tracking with deadline reminders"]),
    (NAVY,   "Phase 2  —  Near-term",
     ["Slack / Teams integration for real-time notifications",
      "ServiceNow ticketing — auto-create incident for Critical",
      "Cognito / SSO authentication when federation available",
      "Multi-region failover support (us-west-2)"]),
    (DGRAY,  "Phase 3  —  Strategic",
     ["AWS Systems Manager automated remediation runbooks",
      "Account tag-based team ownership routing",
      "Historical trend analysis via Bedrock insights",
      "USPTO ITSM / CMDB integration for asset correlation"]),
]

x = Inches(0.3)
pw = Inches(4.2)
for bg, phase_title, bullets in phases:
    rect(s, x, Inches(1.38), pw, Inches(0.48), fill_rgb=bg)
    txt(s, x+Inches(0.12), Inches(1.43), pw-Inches(0.2), Inches(0.38),
        phase_title, size=13, bold=True, color=WHITE)
    rect(s, x, Inches(1.86), pw, Inches(4.95),
         fill_rgb=LGRAY, line_rgb=RGBColor(0xCC, 0xCC, 0xCC))
    by = Inches(2.0)
    for b in bullets:
        rect(s, x+Inches(0.15), by+Inches(0.12), Inches(0.12), Inches(0.12), fill_rgb=bg)
        txt(s, x+Inches(0.38), by, pw-Inches(0.5), Inches(0.55),
            b, size=11, color=DGRAY, wrap=True)
        by += Inches(1.15)
    x += Inches(4.37)

txt(s, Inches(0.3), Inches(7.03), Inches(12.5), Inches(0.26),
    "Repository: github.com/saspto/aws-health-notifications-tracker   "
    "  Live app: https://d2vuz8nfxuvkbe.cloudfront.net",
    size=9, color=MGRAY, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# Save
# ══════════════════════════════════════════════════════════════════════════════
prs.save(OUT)
print(f"Saved {prs.slides.__len__()} slides to: {OUT}")
