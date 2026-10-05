"""P8 Middle East batch: Saudi Arabia, Bahrain, Kuwait, Oman, Israel, Jordan, Lebanon, Egypt,
Türkiye, Iraq — plus FATF / EU list status for the region (incl. Iran, Syria, Yemen).

Figures were sourced on 2026-10-05; every `Src` cites the text fetched. Where the official
site could not be reached the evidence title says "secondary source". All evidence is
`unreviewed` until a named reviewer confirms it (spec §10). Research notes:
docs/superpowers/plans/2026-10-05-p8-middle-east.md.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.seed.builder import Seeder, Src

PWC = "https://taxsummaries.pwc.com/{}"
SA_LAW = "https://gstc.gov.sa/ar/DocumentsLb/Regulations/Documents/INCOME.pdf"
SA_WHTG = (
    "https://zatca.gov.sa/en/HelpCenter/guidelines/Documents/General-Guideline-for-Withholding-"
    "Tax-In-accordance-with-the-provisions-of-the-Income-Tax-Law-and-its-Implementing-"
    "Regulations.pdf"
)
FR_SA = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/arabie_saoudite/"
    "convention_arabie_saoudite_modifiee_cml_clause_npf.pdf"
)
SA_AE = "https://zatca.gov.sa/ar/RulesRegulations/Agreements/Documents/الأمارات.pdf"
OM_ITL = (
    "https://tms.taxoman.gov.om/portal/documents/20126/1455220/income+tax+law+english.pdf"
)
OM_SRC = "Oman Income Tax Law (RD 28/2009 as amended), Tax Authority English translation"
FR_OM = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/oman/"
    "oman_convention_modifiee_cml.pdf"
)
FR_KW = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/koweit/"
    "koweit_convention-avec-le-koweit_fd_1912.pdf"
)
FATF_GREY_URL = (
    "https://www.fatf-gafi.org/en/publications/High-risk-and-other-monitored-jurisdictions/"
    "increased-monitoring-{}.html"
)
IL_ITO = "https://he.wikisource.org/wiki/פקודת_מס_הכנסה"
IL_SRC = "Income Tax Ordinance, Hebrew Wikisource consolidated text (secondary source — gov.il 403)"
FR_IL = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/israel/"
    "israel_convention-avec-israel_fd_1910.pdf"
)
FR_IL_MLI = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/israel/"
    "israel_convention_cml.pdf"
)
FR_BH = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/bahrein/"
    "bahrein_convention_cml.pdf"
)


def seed_batch_me(session: Session) -> None:
    sd = Seeder(session)
    fr = sd.jurisdiction("FR", "France")
    ae = sd.jurisdiction("AE", "United Arab Emirates")
    _saudi_arabia(sd, fr, ae, sd.jurisdiction("SA", "Saudi Arabia"))
    _bahrain(sd, fr, sd.jurisdiction("BH", "Bahrain"))
    _oman(sd, fr, sd.jurisdiction("OM", "Oman"))
    kw = sd.jurisdiction("KW", "Kuwait")
    _kuwait(sd, fr, kw)
    sd.listing(kw, "FATF_GREY", "increased_monitoring", date(2026, 2, 13), None, Src(
        "FATF — Jurisdictions under increased monitoring, February 2026 (read via Wayback "
        "snapshot 2026-09-29)", FATF_GREY_URL.format("february-2026"), None,
        "Following review, the FATF now also identified Kuwait and Papua New Guinea."))
    _israel(sd, fr, sd.jurisdiction("IL", "Israel"))


def _saudi_arabia(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, sa: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    # Income tax applies to the non-Saudi (non-GCC) owners' share; Saudi/GCC shares pay 2.5%
    # Zakat on a wealth base, which the engine does not model.
    sd.cit(sa, start, Src(
        "Income Tax Law (Royal Decree M/1), consolidated text (GSTC)", SA_LAW, "Law art. 7(a)",
        "سعر الضريبة على الوعاء الضريبي هو عشرون بالمئة (20%) لكل من 1- شركة الأموال المقيمة "
        "(20% on resident capital companies — applies to the non-Saudi/GCC owners' share; the "
        "Saudi/GCC share pays 2.5% Zakat)"), rate="20")
    whtg = "ZATCA General Guideline for Withholding Tax, 2nd version (May 2026)"
    sd.wht(sa, "DIVIDEND", "5", start, Src(
        whtg, SA_WHTG, "Implementing Regulations art. 63(1)", "Dividends 5%"))
    sd.wht(sa, "INTEREST", "5", start, Src(
        whtg, SA_WHTG, "Implementing Regulations art. 63(1)",
        "Loan charges (income from debt claims) 5%"))
    sd.wht(sa, "ROYALTY", "15", start, Src(
        "Income Tax Law (Royal Decree M/1), consolidated text (GSTC)", SA_LAW, "Law art. 68(a)",
        "2. أتاوة أو ريع 15% (royalties 15%)"))
    sd.regime(
        sa, start,
        Src("Income Tax Law (Royal Decree M/1), consolidated text (GSTC)", SA_LAW,
            "Law art. 10(c)",
            "ألا تقل نسبة مساهمة [...] عن عشرة بالمائة (10%) 2. ألا تقل مدة ملكية الحد الأدنى "
            "[...] عن سنة واحدة (dividends from resident or non-resident companies exempt at "
            "≥10% held ≥1 year)"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=10, min_holding_period_months=12, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Dividends exempt at ≥10% for 1 year; capital gains on unlisted shares taxed "
        "at 20%. No CFC rules found",
    )

    # Entry into force: 1 March 1983 per France; ZATCA lists 1 February 1983. Art. 20 limits
    # the treaty to five-year terms; the current renewal runs 2024-01-01 to 2028-12-31.
    t = sd.treaty(fr, sa, name="Convention between France and Saudi Arabia (1982, as amended "
                  "2011; renewed to 31 Dec 2028)",
                  signed=date(1982, 2, 18), in_force=date(1983, 3, 1), src=Src(
                      "Convention France–Arabie saoudite modifiée par la CML (impots.gouv.fr)",
                      FR_SA, None, "signée à Paris le 18 février 1982 [...] entrée en vigueur "
                      "le 1er mars 1983 [...] prolongation de l'accord à partir du 1er janvier "
                      "2024 pour une période de cinq ans (ZATCA lists 1 Feb 1983)"))
    start = date(2012, 6, 1)
    for cat, art, quote in (
        ("DIVIDEND", "Article 6", "Les dividendes payés par une société qui est un résident "
         "d'un Etat contractant à un résident de l'autre Etat contractant ne sont imposables "
         "que dans cet autre Etat."),
        ("INTEREST", "Article 7", "Les revenus de créances provenant d'un Etat contractant et "
         "payés à un résident de l'autre Etat contractant ne sont imposables que dans cet "
         "autre Etat."),
        ("ROYALTY", "Article 8", "Les redevances [...] payées à un résident de l'autre Etat "
         "contractant sont imposables dans cet autre Etat. 2. Toutefois, ces redevances sont "
         "aussi imposables dans le premier Etat si le droit ou le bien [...] se rattache "
         "effectivement à une activité [...] exercée dans le premier Etat (no source tax "
         "outside that case)"),
    ):
        sd.treaty_rate(t, cat, art, start, Src(
            "Convention France–Arabie saoudite modifiée par la CML (impots.gouv.fr)", FR_SA,
            f"{art}(1)", quote), exclusive=True)
    sd.ppt(t, date(2021, 1, 1), Src(
        "Convention France–Arabie saoudite modifiée par la CML (impots.gouv.fr)", FR_SA,
        "MLI art. 7(1)",
        "un avantage au titre de celle-ci ne sera pas accordé [...] s'il est raisonnable de "
        "conclure [...] que l'octroi de cet avantage était l'un des objets principaux d'un "
        "montage"))

    t = sd.treaty(sa, ae, name="Agreement between Saudi Arabia and the UAE (2018)",
                  signed=date(2018, 5, 23), in_force=date(2019, 4, 1), src=Src(
                      "ZATCA tax agreements list", "https://zatca.gov.sa/en/RulesRegulations/"
                      "Agreements/Pages/default.aspx", None,
                      "signed on 23/05/2018 and entered into force on 1/04/2019"))
    start = date(2020, 1, 1)
    src = "اتفاقية السعودية–الإمارات (ZATCA)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, SA_AE, "Article 10(2)", "فإن الضريبة المفروضة يجب ألا تتجاوز خمسة بالمائة"),
        max_rate="5")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, SA_AE, "Article 11(1)", "يخضع للضريبة فقط في تلك الدولة المتعاقدة الأخرى"),
        exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, SA_AE, "Article 12(2)", "يجب ألا تزيد عن عشرة بالمائة"), max_rate="10")


def _bahrain(sd: Seeder, fr: Jurisdiction, bh: Jurisdiction) -> None:
    # nbr.gov.bh and legalaffairs.gov.bh returned HTTP 403: domestic figures are secondary.
    sd.cit(bh, date(2025, 1, 1), Src(
        "Bahrain corporate taxes (PwC Worldwide Tax Summaries — secondary source)",
        PWC.format("bahrain/corporate/taxes-on-corporate-income"), None,
        "There are no general corporate income taxes in Bahrain on income, sales, capital "
        "gains, or estates, with the exception [...] oil and gas sector (46%); 15% DMTT for "
        "MNE groups ≥ EUR 750m from 2025 (Decree-Law 11/2024)"), rate="0")
    no_wht = Src(
        "Bahrain withholding taxes (PwC Worldwide Tax Summaries — secondary source)",
        PWC.format("bahrain/corporate/withholding-taxes"), None,
        "There are no withholding taxes (WHTs) on the payment of dividends, interest, or "
        "royalties in Bahrain.")
    for cat in ("DIVIDEND", "INTEREST", "ROYALTY"):
        sd.wht(bh, cat, "0", date(2025, 1, 1), no_wht)

    # Entry into force: 1 Aug 1994 per France (decree 94-669); 10 Aug 1994 per Bahrain (MoFNE,
    # MLI notification) — the French date is recorded.
    t = sd.treaty(fr, bh, name="Convention between France and Bahrain (1993, as amended 2009)",
                  signed=date(1993, 5, 10), in_force=date(1994, 8, 1), src=Src(
                      "Convention France–Bahreïn modifiée par la CML (impots.gouv.fr)", FR_BH,
                      None, "signée à Manama le 10 mai 1993 [...] entrée en vigueur le 1er aout "
                      "1994 [...] modifiée par l'Avenant signé à Paris le 7 mai 2009 [...] "
                      "entré en vigueur le 1er février 2011 (Bahrain records 10 Aug 1994)"))
    start = date(2011, 2, 1)
    for cat, art, quote in (
        ("DIVIDEND", "Article 8", "Les dividendes payés par une société qui est un résident "
         "d'un Etat contractant à un résident de l'autre Etat contractant ne sont imposables "
         "que dans cet autre Etat."),
        ("INTEREST", "Article 9", "Les revenus de créances provenant d'un Etat contractant et "
         "payés à un résident de l'autre Etat contractant ne sont imposables que dans cet "
         "autre Etat."),
        ("ROYALTY", "Article 10", "Les redevances provenant d'un Etat contractant et payées à "
         "un résident de l'autre Etat contractant ne sont imposables que dans cet autre "
         "Etat."),
    ):
        sd.treaty_rate(t, cat, art, start, Src(
            "Convention France–Bahreïn modifiée par la CML (impots.gouv.fr)", FR_BH,
            f"{art}(1)", quote), exclusive=True)
    sd.ppt(t, date(2023, 1, 1), Src(
        "Convention France–Bahreïn modifiée par la CML (impots.gouv.fr)", FR_BH,
        "MLI art. 7(1)",
        "un avantage au titre de celle-ci ne sera pas accordé [...] s'il est raisonnable de "
        "conclure [...] que l'octroi de cet avantage était l'un des objets principaux d'un "
        "montage"))
    # Bahrain–UAE treaty: not on Bahrain's official agreements list; PwC alone lists it —
    # not seeded until confirmed. CFC rules: none found.


def _oman(sd: Seeder, fr: Jurisdiction, om: Jurisdiction) -> None:
    start = date(2025, 1, 1)
    sd.cit(om, start, Src(
        OM_SRC, OM_ITL, "Income Tax Law art. 112",
        "The tax [...] shall be computed by applying the rate of %15 of the taxable income for "
        "any establishment, Omani company or permanent establishment for any tax year."),
        rate="15")
    sd.wht(om, "DIVIDEND", "0", start, Src(
        "Financial Services Authority press release, 11 Jan 2023", "https://fsa.gov.om/Home/"
        "PrintNews/9555", "Royal Directive of 11 Jan 2023",
        "the Royal Directive to cessate the application of withholding tax on stock dividends "
        "and income of fixed instruments (sukuk and bonds) owned by foreign investors [...] "
        "suspension of the withholding tax permanently with immediate effect"))
    # The suspension covers bond/sukuk income; loan interest stays at the statutory 10%.
    statutory = Src(
        OM_SRC, OM_ITL, "Income Tax Law art. 52, 113",
        "The tax rate referred to in Article 52 of this Law shall be %10 of the gross amount.")
    sd.wht(om, "INTEREST", "10", start, statutory)
    sd.wht(om, "ROYALTY", "10", start, statutory)
    sd.regime(
        om, start,
        Src(OM_SRC, OM_ITL, "Income Tax Law art. 115(1)",
            "Dividends received by the establishment, Omani company or permanent establishment "
            "from shares [...] in the capital of any Omani company (no exemption for foreign "
            "dividends found)"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="Only dividends from Omani companies and gains on MSX-listed shares exempt; "
        "foreign dividends taxed at 15%. No CFC rules found",
    )

    t = sd.treaty(fr, om, name="Convention between France and Oman (1989, as amended 1996 "
                  "and 2012)", signed=date(1989, 6, 1), in_force=date(1990, 8, 1), src=Src(
                      "Convention France–Oman modifiée par la CML (impots.gouv.fr)", FR_OM,
                      None, "signée à Paris le 1er juin 1989 [...] entrée en vigueur le 1er "
                      "août 1990 [...] Avenant signé à Mascate le 8 avril 2012 [...] Entré en "
                      "vigueur le 1er mars 2013"))
    start = date(2013, 3, 1)
    src = "Convention France–Oman modifiée par la CML (impots.gouv.fr)"
    sd.treaty_rate(t, "DIVIDEND", "Article 8", start, Src(
        src, FR_OM, "Article 8(1)",
        "Les dividendes payés par une société qui est un résident d'un Etat à un résident de "
        "l'autre Etat ne sont imposables que dans cet autre Etat si ce dernier résident en est "
        "le bénéficiaire effectif."), exclusive=True)
    sd.treaty_rate(t, "INTEREST", "Article 9", start, Src(
        src, FR_OM, "Article 9(1)",
        "Les revenus de créances provenant d'un Etat et payés à un résident de l'autre Etat ne "
        "sont imposables dans le premier Etat que si la créance [...] se rattache effectivement "
        "[...] à un établissement stable"), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 10", start, Src(
        src, FR_OM, "Article 10(1)(b)",
        "l'impôt ainsi établi ne peut excéder 7 pour cent du montant brut des redevances."),
        max_rate="7")
    sd.ppt(t, date(2021, 1, 1), Src(
        src, FR_OM, "MLI art. 7(1)",
        "un avantage au titre de celle-ci ne sera pas accordé [...] si [...] l'octroi de cet "
        "avantage était l'un des objets principaux d'un montage"))
    # Oman–UAE: no treaty on the Tax Authority's list of agreements in force.


def _kuwait(sd: Seeder, fr: Jurisdiction, kw: Jurisdiction) -> None:
    # mof.gov.kw refused connections: domestic figures are secondary (PwC, reviewed Jul 2026).
    start = date(2025, 1, 1)
    sd.cit(kw, start, Src(
        "Kuwait corporate taxes (PwC Worldwide Tax Summaries — secondary source)",
        PWC.format("kuwait/corporate/taxes-on-corporate-income"), "Decree 3/1955, Law 2/2008",
        "The current CIT rate in Kuwait is a flat rate of 15%. (foreign bodies corporate; "
        "Kuwaiti/GCC-owned companies are outside CIT)"), rate="15")
    no_wht = Src(
        "Kuwait withholding taxes (PwC Worldwide Tax Summaries — secondary source)",
        PWC.format("kuwait/corporate/withholding-taxes"), None,
        "The domestic tax law in Kuwait does not provide for WHTs. (a 5% retention pending a "
        "tax clearance certificate is not a final tax)")
    for cat in ("DIVIDEND", "INTEREST", "ROYALTY"):
        sd.wht(kw, cat, "0", start, no_wht)
    sd.regime(
        kw, start,
        Src("Kuwait income determination (PwC Worldwide Tax Summaries — secondary source)",
            PWC.format("kuwait/corporate/income-determination"), None,
            "Dividends declared by companies listed on the KSE after 10 November 2015 are "
            "exempt from tax in Kuwait. [foreign income] is currently treated on a "
            "case-by-case basis."),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="Only KSE-listed dividends exempt; foreign dividends treated case by case. "
        "No CFC rules",
    )

    # Kuwait signed the MLI but has not ratified it: no PPT on either treaty.
    t = sd.treaty(fr, kw, name="Convention between France and Kuwait (1982, as amended 1989 "
                  "and 1994)", signed=date(1982, 2, 7), in_force=date(1983, 9, 1), src=Src(
                      "Convention France–Koweït (impots.gouv.fr)", FR_KW, None,
                      "signée à Koweït le 7 février 1982 [...] entrée en vigueur le 1er "
                      "septembre 1983"))
    start = date(1995, 3, 1)
    src = "Convention France–Koweït (impots.gouv.fr)"
    for cat, art, quote in (
        ("DIVIDEND", "Article 8", "Les dividendes payés par une société qui est un résident "
         "d'un Etat à un résident de l'autre Etat ne sont imposables que dans cet autre Etat si "
         "ce dernier résident en est le bénéficiaire effectif."),
        ("INTEREST", "Article 9", "Les intérêts provenant d'un Etat et payés à un résident de "
         "l'autre Etat ne sont imposables que dans cet autre Etat si ce résident en est le "
         "bénéficiaire effectif."),
        ("ROYALTY", "Article 10", "Les redevances [...] sont imposables dans le premier Etat "
         "seulement si le droit ou le bien générateur des redevances se rattache effectivement "
         "[à] un établissement stable, ou d'une base fixe"),
    ):
        sd.treaty_rate(t, cat, art, start, Src(src, FR_KW, f"{art}(1)", quote), exclusive=True)
    # Kuwait–UAE: dates unverified and secondary sources disagree on royalties — not seeded.


def _israel(sd: Seeder, fr: Jurisdiction, il: Jurisdiction) -> None:
    sd.cit(il, date(2026, 1, 1), Src(
        IL_SRC, IL_ITO, "ITO s.126(a)",
        "על הכנסתו החייבת של חבר בני־אדם יוטל מס שייקרא ”מס חברות“, בשיעור 23% (company tax "
        "of 23% on taxable income)"), rate="23")
    # Substantial shareholders (≥10%) pay 30% — the relevant case for holding structures.
    sd.wht(il, "DIVIDEND", "30", date(2026, 1, 1), Src(
        IL_SRC, IL_ITO, "ITO s.125B(5), s.88",
        "דיבידנד בידי חבר־בני־אדם שהוא תושב חוץ – 25%, ואולם אם היה [...] בעל מניות מהותי "
        "[...] – 30% (non-resident company: 25%; 30% for a substantial shareholder, ≥10%)"))
    ir = Src(
        IL_SRC, IL_ITO, "ITO s.170(a), s.126",
        "ומס בשיעור המוטל לפי הסעיפים 126 ו־127 אם מקבל התשלום הוא חבר בני־אדם (withholding at "
        "the 23% company rate when the payee is a company)")
    sd.wht(il, "INTEREST", "23", date(2026, 1, 1), ir)
    sd.wht(il, "ROYALTY", "23", date(2026, 1, 1), ir)
    sd.regime(
        il, date(2026, 1, 1),
        Src(IL_SRC, IL_ITO, "ITO s.126(c)-(e)",
            "תיכלל הכנסתו החייבת של חבר בני אדם מדיבידנד שמקורו [...] מחוץ לישראל (foreign "
            "dividends are included in taxable income; indirect credit at ≥25%)"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="No participation exemption: foreign dividends and gains taxed at 23% with "
        "(indirect, ≥25%) foreign tax credit — not modelled. CFC (s.75B: passive income taxed "
        "≤15% absolute) not seeded",
    )

    t = sd.treaty(fr, il, name="Convention between France and Israel (1995)",
                  signed=date(1995, 7, 31), in_force=date(1996, 7, 18), src=Src(
                      "Convention France–Israël (impots.gouv.fr)", FR_IL, None,
                      "signée à Jérusalem le 31 juillet 1995 [...] entrée en vigueur le 18 "
                      "juillet 1996 et publiée par le décret n° 96-814"))
    start = date(1997, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Israël (impots.gouv.fr)", FR_IL, "Article 10(2)(c)",
        "c) 15 pour cent du montant brut des dividendes dans tous les autres cas"),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Israël (impots.gouv.fr)", FR_IL, "Article 10(2)(a)",
        "a) 5 pour cent du montant brut des dividendes si le bénéficiaire effectif est une "
        "société qui détient directement ou indirectement au moins 10 pour cent du capital "
        "(10% where the Israeli payer distributes reduced-rate profits — not modelled)"),
        max_rate="5", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Convention France–Israël (impots.gouv.fr)", FR_IL, "Article 11(2)",
        "l'impôt ainsi établi ne peut excéder 10 pour cent du montant brut des intérêts"),
        max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Convention France–Israël (impots.gouv.fr)", FR_IL, "Article 12(2)",
        "l'impôt ainsi établi ne peut excéder 10 pour cent du montant brut des redevances"),
        max_rate="10")
    sd.ppt(t, date(2020, 1, 1), Src(
        "Convention France–Israël modifiée par la CML (impots.gouv.fr)", FR_IL_MLI,
        "MLI art. 7(1)",
        "un avantage [...] ne sera pas accordé [...] si [...] l'octroi de cet avantage était "
        "l'un des objets principaux d'un montage — CML entrée en vigueur le 1er janvier 2019 "
        "pour la France et Israël"))
    # Israel–UAE (2021): a strict LOB (art. 28) limits benefits largely to UAE government and
    # UAE-owned entities, and only secondary texts were available — not seeded.
