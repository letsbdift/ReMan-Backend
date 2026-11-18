"""
ReMan AI Copilot - Service Engine
Handles hybrid routing, internal database querying, Google GenAI SDK integration with Search Grounding.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from django.db.models import Sum, Q, Count
from core.models import (
    Project, Site, Contact, Transaction, Expense, Lead, LandDeal,
    FollowUp, Document, SharedPurpose, SharedExpense
)
from .skills import (
    get_combined_system_instruction,
    KARNATAKA_LAND_REVENUE_SKILL,
    CIVIL_ENGINEERING_SKILL,
    LAND_MEASUREMENT_SKILL
)

logger = logging.getLogger(__name__)

def format_indian_currency(amount) -> str:
    """Format currency in Indian numbering system (Lakhs, Crores, or ₹)."""
    try:
        amt = float(amount or 0.0)
    except (ValueError, TypeError):
        amt = 0.0
    abs_amt = abs(amt)
    if abs_amt >= 10_000_000.0:
        return f"₹{amt / 10_000_000.0:.2f} Crores"
    elif abs_amt >= 100_000.0:
        return f"₹{amt / 100_000.0:.2f} Lakhs"
    else:
        return f"₹{amt:,.0f}"


class AICopilotService:
    """Hybrid AI Copilot service supporting internal DB queries and live external Gemini reasoning."""

    @staticmethod
    def classify_intent(query: str, has_api_key: bool) -> str:
        """
        Classify whether user query targets:
        - 'conversational': simple greetings / polite remarks
        - 'internal_db': queries explicitly targeting recorded projects, sites, expenses, contacts
        - 'external_advisory': domain knowledge, regulatory laws, engineering, or general advice
        """
        q = query.lower().strip()
        clean_q = re.sub(r"[^a-zA-Z0-9 ]", "", q).strip()

        # 1. Conversational & Greetings
        greetings = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "how are you", "who are you", "what is reman"}
        if clean_q in greetings or clean_q.startswith("hi ") or clean_q.startswith("hello ") or clean_q.startswith("hey "):
            return "conversational"

        # 2. Check for explicit domain knowledge keywords
        # If the user asks about general real estate concepts, regulations, or construction standards,
        # these must NEVER be intercepted by local DB if an API key is configured.
        domain_keywords = [
            "eka niveshana", "single site", "single-site", "na conversion", "dc conversion",
            "section 95", "11e", "phodi", "tatkal phodi", "ptcl", "bhoomi", "kaveri", "eswathu",
            "e-swathu", "form 9", "form 11", "11a", "11b", "town planning", "dtcp", "uda", "bda",
            "muda", "k-rera", "krera", "rera", "stamp duty", "guidance value", "registration fee",
            "ugd", "underground drainage", "septic tank", "soak pit", "stormwater", "drainage",
            "transformer", "hescom", "bescom", "wbm", "bitumen", "asphalt", "road width",
            "gunta", "cent", "ankana", "survey number rules", "how to convert", "procedure to",
            "what is", "explain", "rules for", "guidelines for", "legal advice"
        ]

        is_domain_query = any(k in q for k in domain_keywords)

        if is_domain_query and has_api_key:
            return "external_advisory"

        # 3. Explicit Internal Database Ownership Queries
        db_indicators = [
            "my project", "my projects", "list projects", "project status", "our projects",
            "total expenses", "my expenses", "pending expenses", "unpaid expenses", "due expenses",
            "total revenue", "my revenue", "collected revenue", "total collection", "total collections",
            "total investment", "my investment", "partner investment",
            "site status", "plot status", "inventory status", "available sites", "sold sites", "booked sites",
            "available plots", "sold plots", "booked plots", "how many sites", "how many plots",
            "outstanding balance", "customer balance", "receivable", "due amount",
            "my contacts", "list contacts", "partner list", "partners", "brokers",
            "my leads", "active leads", "lead count",
            "my deals", "land deals",
            "my followups", "pending followups", "follow-up tasks", "pending tasks",
            "audit", "bottlenecks", "project audit", "portfolio audit", "flag bottlenecks"
        ]

        is_db_metric = any(ind in q for ind in db_indicators)

        # Check for specific site/plot number lookup (e.g., "site 12", "plot 14", "site #5")
        is_site_lookup = bool(re.search(r"\b(site|plot)\s*#?\s*\d+", q))

        if is_db_metric or is_site_lookup:
            return "internal_db"

        # 4. Default: If user has API key, route to external advisory. If no API key, check internal DB.
        if has_api_key:
            return "external_advisory"
        else:
            return "internal_db"

    @classmethod
    def handle_query(
        cls,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Main dispatcher for AI Copilot queries."""
        conversation_history = conversation_history or []
        api_key = (api_key or "").strip()
        has_api_key = bool(api_key)

        intent = cls.classify_intent(query, has_api_key)
        logger.info(f"AI Copilot Query: '{query}' -> Intent: {intent} (has_api_key={has_api_key})")

        if intent == "conversational":
            q_clean = query.lower().strip()
            if "who are you" in q_clean or "what is reman" in q_clean:
                reply = (
                    "Hello! I am your AI Copilot for ReMan, an intelligent land development and real estate management "
                    "platform. I can assist with internal project financials, site inventory, and live Karnataka "
                    "regulatory/civil advisory."
                )
            else:
                reply = (
                    "Hello! I'm doing well, thank you. How can I assist you with your ReMan projects, site inventory, "
                    "or land development workflows today?"
                )
            return {"status": "success", "mode": "conversational", "reply": reply, "sources": []}

        if intent == "internal_db":
            internal_result = cls.query_internal_database(query, project_id)
            if internal_result:
                return {
                    "status": "success",
                    "mode": "internal_db",
                    "reply": internal_result,
                    "sources": []
                }
            # If not resolved internally and API key exists, fallback to Gemini
            if has_api_key:
                return cls.generate_gemini_advisory(query, conversation_history, api_key)
            else:
                return {
                    "status": "success",
                    "mode": "offline_sme",
                    "reply": cls.generate_offline_sme_fallback(query),
                    "sources": []
                }

        # intent == "external_advisory"
        if has_api_key:
            return cls.generate_gemini_advisory(query, conversation_history, api_key)
        else:
            return {
                "status": "success",
                "mode": "offline_sme",
                "reply": cls.generate_offline_sme_fallback(query),
                "sources": []
            }

    @classmethod
    def generate_gemini_advisory(
        cls,
        query: str,
        conversation_history: List[Dict[str, str]],
        api_key: str
    ) -> Dict[str, Any]:
        """
        Calls Google GenAI SDK (`google-genai`) with live Google Search Grounding.
        Uses `gemini-2.5-flash` (with fallback to `gemini-2.0-flash`).
        """
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            logger.error("google-genai package is not installed.")
            return {
                "status": "error",
                "error_type": "sdk_missing",
                "reply": "❌ **Server Configuration Error:** The Google GenAI SDK (`google-genai`) is not installed on the backend server. Please contact administrator.",
                "sources": []
            }

        client = genai.Client(api_key=api_key)
        system_instruction = get_combined_system_instruction()

        # Format multi-turn conversation history
        contents = []
        for msg in conversation_history[-8:]:
            role = "user" if msg.get("sender") == "USER" else "model"
            text = msg.get("text", "").strip()
            if text:
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=text)]
                    )
                )

        # Append current user prompt
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=query)]
            )
        )

        # Configure Google Search Grounding
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[{"google_search": {}}],
            temperature=0.4,
            max_output_tokens=1500
        )

        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        last_error = None

        for model_name in models_to_try:
            try:
                logger.info(f"Calling Gemini model '{model_name}' with Google Search Grounding...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )

                answer_text = response.text or ""
                sources = []

                # Extract grounding metadata (search chunks and queries)
                if response.candidates:
                    candidate = response.candidates[0]
                    gm = getattr(candidate, "grounding_metadata", None)
                    if gm:
                        chunks = getattr(gm, "grounding_chunks", None) or []
                        for chunk in chunks:
                            web = getattr(chunk, "web", None)
                            if web:
                                title = getattr(web, "title", "Reference Source") or "Reference Source"
                                uri = getattr(web, "uri", "")
                                if uri and uri not in [s["uri"] for s in sources]:
                                    sources.append({"title": title, "uri": uri})

                # Append formatted citation links if sources were returned
                if sources:
                    citation_block = "\n\n**Sources & Citations:**\n" + "\n".join(
                        f"• [{s['title']}]({s['uri']})" for s in sources[:6]
                    )
                    answer_text += citation_block

                return {
                    "status": "success",
                    "mode": "external_gemini",
                    "model": model_name,
                    "reply": answer_text,
                    "sources": sources
                }

            except Exception as e:
                err_msg = str(e)
                last_error = e
                logger.warning(f"Error calling {model_name}: {err_msg}")

                # Specific checks for Invalid API Key or Quota Exceeded
                if "API_KEY_INVALID" in err_msg or "400" in err_msg and "key" in err_msg.lower() or "403" in err_msg or "PERMISSION_DENIED" in err_msg:
                    return {
                        "status": "error",
                        "error_type": "api_key_invalid",
                        "reply": "❌ **Gemini API Key Error:** The configured Gemini API key is invalid or unauthorized. Please verify or update your API key in the AI Copilot settings.",
                        "sources": []
                    }

                if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg or "quota" in err_msg.lower():
                    return {
                        "status": "error",
                        "error_type": "quota_exceeded",
                        "reply": "⚠️ **Gemini API Quota Exceeded:** You have exceeded your request quota for the configured Gemini API key. Please check your usage limits at Google AI Studio or try again later.",
                        "sources": []
                    }

        # If all models failed with another error, report specific error to user
        return {
            "status": "error",
            "error_type": "api_error",
            "reply": f"⚠️ **Gemini API Service Error:** Unable to complete live search request: {str(last_error)}. Please verify your network or API key settings.",
            "sources": []
        }

    @staticmethod
    def query_internal_database(query: str, project_id: Optional[str] = None) -> Optional[str]:
        """Query internal Django database models and return exact figures/records."""
        q = query.lower().strip()

        # 1. Project Filter Scope
        projects = Project.objects.all()
        sites = Site.objects.all()
        expenses = Expense.objects.all()
        transactions = Transaction.objects.all()
        contacts = Contact.objects.all()
        leads = Lead.objects.all()
        deals = LandDeal.objects.all()
        followups = FollowUp.objects.all()
        documents = Document.objects.all()

        if project_id and project_id != "All":
            try:
                pid = int(project_id)
                projects = projects.filter(id=pid)
                sites = sites.filter(project_id=pid)
                expenses = expenses.filter(project_id=pid)
                transactions = transactions.filter(project_id=pid)
            except (ValueError, TypeError):
                pass

        # 2. Aggregated Revenue
        if any(k in q for k in ["total revenue", "revenue", "collection", "total collected", "sales revenue"]):
            rev_tx = transactions.filter(transaction_type="Received").exclude(status="Cancelled")
            total_rev = rev_tx.aggregate(s=Sum("amount"))["s"] or 0.0
            count = rev_tx.count()
            return f"The total collected revenue is {format_indian_currency(total_rev)} from {count} received customer payment transactions."

        # 3. Aggregated Expenses
        if any(k in q for k in ["total expense", "total expenses", "expenditure", "total cost", "development cost"]):
            total_exp = expenses.aggregate(s=Sum("amount"))["s"] or 0.0
            pending_exp = expenses.exclude(status="Paid").aggregate(s=Sum("amount"))["s"] or 0.0
            return f"The total recorded development expenses are {format_indian_currency(total_exp)} (with {format_indian_currency(pending_exp)} pending payment)."

        # 4. Pending Expenses
        if any(k in q for k in ["pending expense", "pending expenses", "unpaid expense", "to be paid", "due expense"]):
            pending_qs = expenses.exclude(status="Paid")
            pending_amt = pending_qs.aggregate(s=Sum("amount"))["s"] or 0.0
            count = pending_qs.count()
            return f"Total pending expenses to be paid are {format_indian_currency(pending_amt)} across {count} unpaid records."

        # 5. Total Investment
        if any(k in q for k in ["total investment", "capital investment", "investment"]):
            paid_tx = transactions.filter(transaction_type="Paid").exclude(status="Cancelled").aggregate(s=Sum("amount"))["s"] or 0.0
            paid_exp = expenses.filter(status="Paid").aggregate(s=Sum("amount"))["s"] or 0.0
            total_inv = float(paid_tx) + float(paid_exp)
            return f"The total project investment is {format_indian_currency(total_inv)} across active development operations."

        # 6. Site Inventory Status
        if any(k in q for k in ["site status", "plot status", "inventory status", "how many sites", "available sites", "sold sites", "booked sites", "available plots"]):
            total_sites = sites.count()
            avail = sites.filter(Q(status="Available") | Q(status__isnull=True) | Q(status="")).count()
            booked = sites.filter(status="Booked").count()
            sold = sites.filter(status="Sold").count()
            blocked = sites.filter(status="Blocked").count()
            return (
                f"Current site inventory status: {total_sites} total plots "
                f"({avail} available, {booked} booked, {sold} sold"
                f"{f', {blocked} blocked' if blocked > 0 else ''})."
            )

        # 7. Customer Outstanding Balance
        if any(k in q for k in ["outstanding", "customer balance", "receivable", "due from customer"]):
            booked_or_sold = sites.filter(Q(status="Booked") | Q(status="Sold"))
            gross_sales = booked_or_sold.aggregate(s=Sum("price"))["s"] or 0.0
            collected = transactions.filter(transaction_type="Received").exclude(status="Cancelled").aggregate(s=Sum("amount"))["s"] or 0.0
            outstanding = max(0.0, float(gross_sales) - float(collected))
            return f"The total customer outstanding balance is {format_indian_currency(outstanding)} from booked and sold site inventory."

        # 8. Specific Site / Plot Lookup
        site_match = re.search(r"\b(?:site|plot)\s*#?\s*([a-zA-Z0-9_-]+)", q)
        if site_match:
            site_num = site_match.group(1).strip()
            found_site = sites.filter(site_number__iexact=site_num).first()
            if found_site:
                lines = [
                    f"Site **#{found_site.site_number}** is **{found_site.status}**.",
                    f"• **Dimensions:** {found_site.dimensions or 'Standard'} ({found_site.area or 'N/A'})",
                    f"• **Price:** {format_indian_currency(found_site.price or 0.0)}"
                ]
                if found_site.facing:
                    lines.append(f"• **Facing:** {found_site.facing}")
                if found_site.road_width:
                    lines.append(f"• **Road Width:** {found_site.road_width}")
                if found_site.customer:
                    lines.append(f"• **Customer:** {found_site.customer.name}")
                if found_site.amount_received:
                    lines.append(f"• **Amount Received:** {format_indian_currency(found_site.amount_received)}")
                if found_site.balance:
                    lines.append(f"• **Remaining Balance:** {format_indian_currency(found_site.balance)}")
                return "\n".join(lines)

        # 9. Contact Lookup
        if q in ["partners", "show partners", "list partners", "partner list"]:
            partner_list = contacts.filter(contact_type="Partner")
            if partner_list.exists():
                lines = [f"Found {partner_list.count()} partner(s) in ReMan:"]
                for p in partner_list:
                    lines.append(f"• **{p.name}** ({p.ownership_percentage or 0}% share) — Mobile: {p.mobile}")
                return "\n".join(lines)

        # Match contact by name
        for c in contacts:
            if c.name and len(c.name) >= 3 and c.name.lower() in q:
                lines = [f"Found contact: **{c.name}** ({c.contact_type or 'General'})."]
                if c.mobile:
                    lines.append(f"• **Mobile:** {c.mobile}")
                if c.email:
                    lines.append(f"• **Email:** {c.email}")
                if c.ownership_percentage:
                    lines.append(f"• **Ownership Share:** {c.ownership_percentage}%")
                if c.location:
                    lines.append(f"• **Location:** {c.location}")
                return "\n".join(lines)

        # 10. Project Lookup
        for p in projects:
            if p.project_name and len(p.project_name) >= 3 and p.project_name.lower() in q:
                lines = [
                    f"Project **{p.project_name}** is in **{p.status}** status.",
                    f"• **Location:** {p.location or 'Harapanahalli'} (Survey #{p.survey_number or 'N/A'})",
                    f"• **Land Area:** {p.land_area or 'N/A'}",
                    f"• **Purchase Cost:** {format_indian_currency(p.purchase_cost or 0.0)}",
                    f"• **Development Budget:** {format_indian_currency(p.development_cost or 0.0)}"
                ]
                return "\n".join(lines)

        # 11. Lifecycle Diagnostics / Bottlenecks
        if any(k in q for k in ["bottleneck", "audit", "diagnostics", "lifecycle diagnostic"]):
            total_st = sites.count()
            avail_st = sites.filter(Q(status="Available") | Q(status__isnull=True) | Q(status="")).count()
            pending_exp_amt = expenses.exclude(status="Paid").aggregate(s=Sum("amount"))["s"] or 0.0
            overdue_fu = followups.filter(status="Pending").count()

            lines = ["🔍 **Project Lifecycle Diagnostic:**\n"]
            if total_st > 0 and avail_st > total_st * 0.5:
                lines.append(f"1. High Inventory Concentration: {int((avail_st * 100) / total_st)}% of sites remain available. Recommend buyer marketing.")
            if pending_exp_amt > 50000.0:
                lines.append(f"2. Pending Financial Outflows: {format_indian_currency(pending_exp_amt)} in unreleased expenses. Verify contractor milestones.")
            if overdue_fu > 0:
                lines.append(f"3. Client Engagement Lag: {overdue_fu} overdue follow-up reminders pending action.")
            lines.append("4. Karnataka Section 95 Workflow: Verify DC conversion order documentation and Bhoomi portal RTC mutation for active layouts.")
            return "\n\n".join(lines)

        return None

    @staticmethod
    def generate_offline_sme_fallback(query: str) -> str:
        """Offline fallback knowledge engine for Karnataka land development when no API key is available."""
        q = query.lower().strip()

        if "eka niveshana" in q or "single site" in q:
            return (
                "🏛️ **Karnataka Eka Niveshana (Single Site Approval) Guidance:**\n\n"
                "• **Statutory Basis:** Governed under Section 17 of the Karnataka Town and Country Planning (KTCP) Act, 1961.\n"
                "• **Purpose:** Regularizes and approves a single standalone residential plot formed in revenue/unauthorized layouts for building plan sanction and bank mortgages.\n"
                "• **Competent Authority:** Local Urban Development Authority (e.g. UDA / DTCP) or Gram Panchayat with town planning approval.\n"
                "• **Checklist:** Registered title deed, Section 95 DC conversion order, 11E survey sketch, nil-EC for 30 years, and proof of minimum 30 ft public road approach.\n\n"
                "💡 *Configure a Gemini API key in Copilot settings for live web search and real-time portal updates.*"
            )

        if "section 95" in q or "conversion" in q or "na conversion" in q:
            return (
                "🏛️ **Karnataka Section 95 NA Conversion Workflow (Bhoomi):**\n\n"
                "1. **Affidavit Application:** Submit online application via the Bhoomi portal with digitally signed RTC, 11E sketch, and title deed.\n"
                "2. **Field Verification:** Tahsildar and Revenue Inspector inspect site and verify tenancy claims within 30 days.\n"
                "3. **Challan Payment:** Pay statutory conversion fee via Khajane-II treasury portal.\n"
                "4. **DC Order:** Deputy Commissioner issues official NA conversion order.\n"
                "5. **Mutation & Phodi:** Survey record updated on Bhoomi with conversion endorsement and Tatkal Phodi.\n\n"
                "💡 *Configure a Gemini API key in Copilot settings for live web search and real-time portal updates.*"
            )

        if "ugd" in q or "drainage" in q or "septic" in q:
            return (
                "📐 **Civil Infrastructure & Drainage Standards:**\n\n"
                "• **Stormwater Drains:** Precast RCC rectangular box drains along both road sides with concrete covers.\n"
                "• **Underground Drainage (UGD):** Minimum 150mm - 200mm dia RCC/stoneware pipes with manholes at 30m intervals and road junctions.\n"
                "• **Septic Tank Sizing (IS 2470):** Twin-chamber tank with 2:1 length-to-width ratio, 1.2m to 1.8m liquid depth, and connected soak pit.\n\n"
                "💡 *Configure a Gemini API key in Copilot settings for live web search and real-time portal updates.*"
            )

        return (
            f"🧭 **AI Copilot (Offline Mode):**\n\n"
            f"Regarding \"{query}\", ReMan is currently operating in offline mode. "
            "To get live web-grounded legal procedures, town planning rules, and real-time Karnataka portal data, "
            "please enter your Gemini API key via the key icon in the top app bar."
        )
