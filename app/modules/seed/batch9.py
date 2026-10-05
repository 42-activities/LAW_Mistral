"""P8 batch 9: Middle East completion (IR, SY, YE, PS), North Africa (MA, DZ, TN, LY, SD),
Kenya and Australia.

Figures were sourced on 2026-10-05 from the texts cited on each `Src` and are stored as
`unreviewed` until a named reviewer confirms them (spec §10). Iran, Syria and Yemen keep their
FATF / EU AML guardrails (seeded in the Middle East wave 2). Research notes:
docs/superpowers/plans/2026-10-05-p8-batch9.md.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.seed.builder import Seeder, Src

IR_DTA = "https://qavanin.ir/Law/TreeText/?IDS=892583840653829785"
IR_SRC = "قانون مالیاتهای مستقیم (Direct Taxation Act), consolidated to 1404/04/08 (qavanin.ir)"
FR_IR = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/iran/"
    "iran_convention-avec-l-iran_fd_1881.pdf"
)

AU_RATES = "https://www.legislation.gov.au/C2004A00086/latest/text"
AU_ITAA36 = "https://www.legislation.gov.au/C1936A00027/latest/text"
AU_ITAA97 = "https://www.legislation.gov.au/C2004A05138/latest/text"
FR_AU = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/australie/"
    "version-consolidee-australie.pdf"
)

DZ_CIDTA = (
    "https://www.mfdgi.gov.dz/files/803/2026/3726/"
    "CodedesImpotsDirectsetTaxesAssimilees2026fr"
)
DZ_SRC = "Code des impôts directs et taxes assimilées 2026 (DGI, mfdgi.gov.dz)"
FR_DZ = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/algerie/"
    "algerie_convention-avec-l-algerie_fd_1720.pdf"
)
DZ_AE = "https://www.mfdgi.gov.dz/files/526/Pays-Arabes/102/Emirats-arabes--unis"
LY_LAW = "https://tax.gov.ly/assets/m2016.pdf"
LY_SRC = "Income Tax Law No. 7 of 2010, Libyan Tax Authority compilation 2016"
FR_LY = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/libye/"
    "libye_convention-avec-la-libye-signee-le-22.12.05-texte-entre-en-vigueur-le-01.07.2008_"
    "fd_3713.pdf"
)
MA_CGI = (
    "https://www.tax.gov.ma/wps/wcm/connect/08712531-1e81-4e28-a38b-2bd9edf8e09e/CGI+2026+FR.pdf"
)
MA_SRC = "Code Général des Impôts 2026 (DGI Maroc, read via Wayback snapshot)"
FR_MA = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/maroc/"
    "maroc_convention-avec-le-maroc_fd_2177.pdf"
)
MA_AE = "https://mof.gov.ae/wp-content/uploads/2025/06/UAE-Morocco-DTA.pdf"
TN_CODE = "https://jibaya.tn/wp-content/uploads/2026/03/Code_IRPP_IS_2026_fr.pdf"
TN_SRC = "Code de l'IRPP et de l'IS, édition 2026 (DGI Tunisie, jibaya.tn)"
FR_TN = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/tunisie/"
    "nid_27638_tunisie_version_consolidee_cml.pdf"
)
TN_AE = "https://jibaya.tn/wp-content/uploads/2024/01/emirate-des-etats-unis.pdf"
KE_ITA = "https://www.kra.go.ke/images/publications/Income-Tax-Act-2026.pdf"
KE_SRC = "Income Tax Act Cap. 470, Kenya Law revision as at 1 July 2026 (KRA-hosted)"
FR_KE = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/kenya/"
    "nid_26934_kenya_modifiee_cml_clause_npf.pdf"
)
KE_AE = "https://mof.gov.ae/wp-content/uploads/2025/06/UAE-Kenya-DTA.pdf"
SD_ITA = "https://moj.gov.sd/sudanlaws/epub/EPUB/xhtml/s2yuyr.html"
SD_SRC = "Income Tax Act 1986 as amended (Ministry of Justice e-library; Taxation Chamber acts)"
SD_AE = "https://tax.gov.sd/wp-content/uploads/2025/02/emaraties1.pdf"
FATF = (
    "https://www.fatf-gafi.org/en/publications/High-risk-and-other-monitored-jurisdictions/{}.html"
)


def seed_batch9(session: Session) -> None:
    sd = Seeder(session)
    fr = sd.jurisdiction("FR", "France")
    _iran(sd, fr, sd.jurisdiction("IR", "Iran"))
    _australia(sd, fr, sd.jurisdiction("AU", "Australia"))
    ae = sd.jurisdiction("AE", "United Arab Emirates")
    dz = sd.jurisdiction("DZ", "Algeria")
    _algeria(sd, fr, ae, dz)
    sd.listing(dz, "FATF_GREY", "increased_monitoring", date(2024, 10, 25), date(2026, 6, 19),
               Src("FATF — Jurisdictions under increased monitoring, 19 June 2026 (Wayback "
                   "snapshot)", FATF.format("increased-monitoring-june-2026"), None,
                   "The FATF welcomes Algeria's significant progress [...] the strategic "
                   "deficiencies that the FATF identified in October 2024 (removed June 2026)"))
    sd.listing(dz, "EU_AML_HIGH_RISK", "high_risk", date(2025, 8, 5), None, Src(
        "Delegated Regulation (EU) 2025/1184 (Publications Office)",
        "http://publications.europa.eu/resource/celex/32025R1184", None,
        "to add Algeria, Angola, Côte d'Ivoire, Kenya, Laos, Lebanon [...] (still listed in the "
        "29 Jan 2026 consolidation)"))
    _libya(sd, fr, sd.jurisdiction("LY", "Libya"))
    ma = sd.jurisdiction("MA", "Morocco")
    _morocco(sd, fr, ae, ma)
    sd.listing(ma, "EU_TAX_ANNEX_II", "state_of_play", date(2026, 2, 17), None, Src(
        "Council conclusions on the EU list of non-cooperative jurisdictions, 17 Feb 2026 "
        "(OJ C/2026/1465)", "http://publications.europa.eu/resource/celex/52026XG01465",
        "Annex II 3.2", "committed to addressing the identified deficiencies [...] as regards "
        "country-by-country reporting [...] Greenland, Jordan and Morocco"))
    _tunisia(sd, fr, ae, sd.jurisdiction("TN", "Tunisia"))
    ke = sd.jurisdiction("KE", "Kenya")
    _kenya(sd, fr, ae, ke)
    sd.listing(ke, "FATF_GREY", "increased_monitoring", date(2024, 2, 23), None, Src(
        "FATF — Jurisdictions under increased monitoring, 19 June 2026 (Wayback snapshot)",
        FATF.format("increased-monitoring-june-2026"), None,
        "Since February 2024, when Kenya made a high-level political commitment to work with "
        "the FATF and ESAAMLG"))
    sd.listing(ke, "EU_AML_HIGH_RISK", "high_risk", date(2025, 8, 5), None, Src(
        "Delegated Regulation (EU) 2016/1675, consolidated 29 Jan 2026 (EUR-Lex)",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R1675-20260129",
        "Annex point I", "10 Kenya (added by Delegated Regulation (EU) 2025/1184)"))
    _sudan(sd, ae, sd.jurisdiction("SD", "Sudan"))


def _iran(sd: Seeder, fr: Jurisdiction, ir: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(ir, start, Src(
        IR_SRC, IR_DTA, "DTA art. 105",
        "مشمول ماليات به نرخ بيست و پنج درصد (25٪) خواهند بود (companies taxed at 25% on "
        "income from Iran or abroad)"), rate="25")
    sd.wht(ir, "DIVIDEND", "0", start, Src(
        IR_SRC, IR_DTA, "DTA art. 105 tabs. 4",
        "اشخاص اعم از حقيقي يا حقوقي نسبت به سود سهام [...] مشمول ماليات ديگري نخواهند بود "
        "(no further tax on dividends)"))
    # Royalties: deemed profit of 10-40% of gross taxed at 25%; the general 30% coefficient
    # (Art. 107 Regulation art. 3) gives 7.5% of gross.
    sd.wht(ir, "ROYALTY", "7.5", start, Src(
        IR_SRC, IR_DTA, "DTA art. 107; Art. 107 Regulation (1395/03/12) art. 3",
        "به مأخذ ده درصد (10 %) تا چهل درصد (40 %) مجموع وجوهي [...] (deemed taxable income "
        "10-40% of gross, 30% for general royalties, taxed at 25% — 7.5% of gross)"))
    # No dedicated interest WHT article: non-residents' tax may be collected at source at the
    # 25% rate (art. 159) — stored conservatively.
    sd.wht(ir, "INTEREST", "25", start, Src(
        IR_SRC, IR_DTA, "DTA art. 105 tabs. 2; art. 159",
        "در مورد مؤديان غير ايراني و اشخاص مقيم خارج از كشور كل ماليات‌هاي متعلق را به نرخ "
        "مربوط مقرر در منبع وصول نمايد (tax of non-residents collected at source at the "
        "applicable rate)"))
    sd.regime(
        ir, start,
        Src(IR_SRC, IR_DTA, "DTA art. 1(4), 105 tabs. 4",
            "هر شخص حقوقي ايراني نسبت به كليه درآمدهائي كه در ايران يا خارج از ايران تحصيل "
            "مي‌نمايد (worldwide taxation; dividend exemption read as domestic only)"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="Foreign dividends treated as taxable (scope of art. 105 tabs. 4 unclear); share "
        "sales bear final flat taxes (0.5% listed, 4% of nominal value unlisted). No CFC rules",
    )

    # Iran is not an MLI signatory; no Iran–UAE treaty (only a 2003 authorisation to initial).
    t = sd.treaty(fr, ir, name="Convention between France and Iran (1973)",
                  signed=date(1973, 11, 7), in_force=date(1975, 4, 10), src=Src(
                      "Convention France–Iran (impots.gouv.fr)", FR_IR, None,
                      "signée à Téhéran le 7 novembre 1973 [...] entrée en vigueur le 10 avril "
                      "1975"))
    src = "Convention France–Iran (impots.gouv.fr)"
    start = date(1976, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_IR, "Article 10(2)(b)", "20 p. cent [...] dans tous les autres cas"),
        max_rate="20")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_IR, "Article 10(2)(a)", "15 p. cent [...] au moins 25 p. cent du capital"),
        max_rate="15", ownership_threshold="25")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, FR_IR, "Article 11(2)", "ne peut excéder 15 p. cent du montant brut des intérêts"),
        max_rate="15")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, FR_IR, "Article 12(2)", "ne peut excéder 10 p. cent du montant brut des "
        "redevances"), max_rate="10")


def _australia(sd: Seeder, fr: Jurisdiction, au: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(au, start, Src(
        "Income Tax Rates Act 1986, compilation No. 66 (legislation.gov.au)",
        "https://www.legislation.gov.au/C2004A03397/latest/text", "s 23(2)",
        "The rate of tax in respect of the taxable income of a company is: (a) if the company "
        "is a base rate entity for a year of income—25%; or (b) otherwise—30%"), rate="30")
    wht = ("Income Tax (Dividends, Interest and Royalties Withholding Tax) Act 1974 "
           "(legislation.gov.au)")
    # Franked dividends and conduit foreign income are exempt; the unfranked 30% is stored.
    sd.wht(au, "DIVIDEND", "30", start, Src(
        wht, AU_RATES, "s 7(a); ITAA 1936 s 128B(3)(ga)",
        "subsection 128B(4) [dividends]—30% (the franked part of a dividend is exempt)"))
    sd.wht(au, "INTEREST", "10", start, Src(wht, AU_RATES, "s 7(b)", "subsection (5) "
                                            "[interest]—10%"))
    sd.wht(au, "ROYALTY", "30", start, Src(wht, AU_RATES, "s 7(c)", "subsection (5A) "
                                           "[royalties]—30%"))
    sd.regime(
        au, start,
        Src("Income Tax Assessment Act 1997 (legislation.gov.au)", AU_ITAA97, "s 768-5, 768-15",
            "is not assessable income, and is not exempt income [...] at least 10% (combined "
            "direct and indirect participation interest)"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=10, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Foreign dividends exempt at ≥10% participation (no period); share gains reduced "
        "only by the active foreign business asset percentage (Subdiv. 768-G) — treated as "
        "taxable",
    )
    # Part X attributes by country lists (listed: CA, FR, DE, JP, NZ, GB, US), not a rate test;
    # half the Australian rate is stored as an approximation.
    sd.cfc(
        au, start,
        Src("Income Tax Assessment Act 1936, Part X (legislation.gov.au)", AU_ITAA36, "s 340",
            "a group of 5 or fewer Australian 1% entities [...] not less than 50% [...] a single "
            "Australian entity holds not less than 40%"),
        control_threshold_pct=50, low_tax_relative_pct=50, threshold_inclusive=True,
        legal_ref="ITAA 1936 Part X",
        effect="Passive/tainted income of controlled companies in unlisted countries is "
        "attributed (country-list system; rate test approximated).",
    )

    t = sd.treaty(fr, au, name="Convention between France and Australia (2006)",
                  signed=date(2006, 6, 20), in_force=date(2009, 6, 1), src=Src(
                      "Convention France–Australie modifiée par la CML (impots.gouv.fr)", FR_AU,
                      None, "signée à Paris le 20 juin 2006 [...] entrée en vigueur le 1er juin "
                      "2009"))
    src = "Convention France–Australie modifiée par la CML (impots.gouv.fr)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(2010, 1, 1), Src(
        src, FR_AU, "Article 10(2)(b)", "15 pour cent du montant brut des dividendes dans tous "
        "les autres cas"), max_rate="15")
    # The 0% tier needs profits taxed at the normal corporate rate — not modelled.
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(2019, 1, 1), Src(
        src, FR_AU, "Article 10(2)(a); MLI art. 8",
        "5 pour cent [...] une société qui détient directement au moins 10 pour cent [...] tout "
        "au long d'une période de 365 jours incluant le jour du paiement"),
        max_rate="5", ownership_threshold="10", min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 11", date(2010, 1, 1), Src(
        src, FR_AU, "Article 11(2)", "ne peut excéder 10 pour cent du montant brut"),
        max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", date(2010, 1, 1), Src(
        src, FR_AU, "Article 12(2)", "ne peut excéder 5 pour cent du montant brut"),
        max_rate="5")
    sd.ppt(t, date(2019, 1, 1), Src(
        src, FR_AU, "MLI art. 7(1)", "l'un des objets principaux d'un montage — MLI in force for "
        "both 1 Jan 2019"))
    # No Australia–UAE treaty (Treasury list, 24 Mar 2026).


def _algeria(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, dz: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(dz, start, Src(
        DZ_SRC, DZ_CIDTA, "CIDTA art. 150-1)",
        "26%, pour les autres activités (19% production of goods; 23% construction, public "
        "works, tourism)"), rate="26")
    sd.wht(dz, "DIVIDEND", "15", start, Src(
        DZ_SRC, DZ_CIDTA, "CIDTA art. 150-2)",
        "15%, libératoires d'impôt, pour les produits des actions ou parts sociales [...] "
        "réalisés par les personnes morales n'ayant pas d'installation professionnelle "
        "permanente en Algérie"))
    sd.wht(dz, "INTEREST", "10", start, Src(
        DZ_SRC, DZ_CIDTA, "CIDTA art. 150-2)",
        "10%, pour les revenus des créances, dépôts, et cautionnements"))
    sd.wht(dz, "ROYALTY", "30", start, Src(
        DZ_SRC, DZ_CIDTA, "CIDTA art. 150-2)",
        "30%, pour [...] les produits versés à des inventeurs situés à l'étranger au titre [...] "
        "de licence [...] brevets [...] marque"))
    sd.regime(
        dz, start,
        Src(DZ_SRC, DZ_CIDTA, "CIDTA art. 137, 150-2)",
            "L'impôt est dû à raison des bénéfices réalisés en Algérie (territoriality; 5% final "
            "tax on distributed profits already subject to IBS — scope unclear)"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="No explicit participation exemption (territorial system; treatment of foreign "
        "dividends unverified); share gains taxed on 35-70% of the gain. No CFC rules",
    )

    # Algeria signed the MLI (2024) but has not ratified it — no PPT.
    t = sd.treaty(fr, dz, name="Convention between France and Algeria (1999)",
                  signed=date(1999, 10, 17), in_force=date(2002, 12, 1), src=Src(
                      "Décret n° 2002-1501 (JO n° 300 du 26-12-2002)", FR_DZ, None,
                      "La présente convention est entrée en vigueur le 1er décembre 2002"))
    src = "Convention France–Algérie (impots.gouv.fr)"
    start = date(2002, 12, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_DZ, "Article 10(2)(b)", "15 pour cent du montant brut des dividendes dans tous "
        "les autres cas"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_DZ, "Article 10(2)(a)",
        "si le bénéficiaire effectif est une société qui détient directement ou indirectement "
        "au moins 10 pour cent du capital"), max_rate="5", ownership_threshold="10")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        for state, rate in ((dz, "12"), (fr, "10")):
            sd.treaty_rate(t, cat, art, start, Src(
                src, FR_DZ, f"{art}(2)", "10 pour cent [...] lorsque ceux-ci proviennent de "
                "France et 12 pour cent [...] lorsque ceux-ci proviennent d'Algérie"),
                max_rate=rate, source=state)

    # Ratified by Algeria (D.P. 03-164, 2003); the exchange of instruments — and so the entry
    # into force — was not found: the engine does not apply a treaty without that date.
    t = sd.treaty(dz, ae, name="Convention between Algeria and the UAE (2001)",
                  signed=date(2001, 4, 24), in_force=None, src=Src(
                      "Convention Algérie–EAU (DGI, mfdgi.gov.dz)", DZ_AE, None,
                      "ratified by Algeria by D.P. 03-164 of 7-04-2003 (JORA n°26 of "
                      "13-04-2003); entry into force not published"))
    src = "Convention Algérie–EAU (DGI, mfdgi.gov.dz)"
    start = date(2004, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, DZ_AE, "Article 10(1)", "imposables dans cet autre Etat (no source-State rate)"),
        exclusive=True)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, DZ_AE, "Article 11(1)", "imposables uniquement dans cet autre Etat contractant"),
        exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, DZ_AE, "Article 12(2)", "ne peut excèder dix pour cent (10%)"), max_rate="10")


def _libya(sd: Seeder, fr: Jurisdiction, ly: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(ly, start, Src(
        LY_SRC, LY_LAW, "Law 7/2010 art. 70; Law 44/1970 art. 2",
        "يكون سعر الضريبة سنوياً (20%) — plus Jihad tax 4% من الربح أو الدخل الخاضع للضريبة "
        "(20% + 4% stored)"), rate="24")
    sd.wht(ly, "DIVIDEND", "0", start, Src(
        LY_SRC, LY_LAW, "Law 7/2010 art. 34",
        "على ما يوزع من هذه الدخول على المساهمين في الشركة (no further tax on distributions of "
        "company-taxed income)"))
    # No general withholding on interest or royalties paid to non-residents found in Law
    # 7/2010 (the Executive Regulation was not read) — not seeded.
    sd.regime(
        ly, start,
        Src(LY_SRC, LY_LAW, "Law 7/2010 art. 45, 63",
            "gains on business assets taxed as ordinary income; national companies taxed on "
            "Libyan and foreign income"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0, notes="No participation exemption or CFC rules found",
    )

    # Libya is not an MLI signatory; no Libya–UAE treaty (neither side's list).
    t = sd.treaty(fr, ly, name="Convention between France and Libya (2005)",
                  signed=date(2005, 12, 22), in_force=date(2008, 7, 1), src=Src(
                      "Convention France–Libye (impots.gouv.fr)", FR_LY, None,
                      "signée le 22.12.05 — texte entré en vigueur le 01.07.2008"))
    src = "Convention France–Libye (impots.gouv.fr)"
    start = date(2009, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 11", start, Src(
        src, FR_LY, "Article 11(2)(b)", "10 pour cent du montant brut des dividendes dans tous "
        "les autres cas"), max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 11", start, Src(
        src, FR_LY, "Article 11(2)(a)",
        "société qui détient directement ou indirectement au moins 10 pour cent du capital"),
        max_rate="5", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 12", start, Src(
        src, FR_LY, "Article 12(1)", "ne sont imposables que dans cet autre Etat [...] soumis "
        "à l'impôt à raison de ces intérêts dans cet autre Etat"), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 13", start, Src(
        src, FR_LY, "Article 13(2)", "ne peut excéder 10 pour cent du montant brut des "
        "redevances"), max_rate="10")


def _morocco(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, ma: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(ma, start, Src(
        MA_SRC, MA_CGI, "CGI art. 19-I; art. 247-XXXVII-A",
        "le taux de l'impôt sur les sociétés est fixé à : A.- 20% (35% where net profit is MAD "
        "100m or more; 40% for banks and insurers)"), rate="20")
    # 11.25% for distributions from 1 Jan 2026, 10% from 1 Jan 2027 (art. 247-XXXVII-C).
    sd.wht(ma, "DIVIDEND", "11.25", start, Src(
        MA_SRC, MA_CGI, "CGI art. 19-IV-B; art. 247-XXXVII-C",
        "11,25% [...] à compter du 1er janvier 2026 ; 10% [...] à compter du 1er janvier 2027"))
    ir = Src(MA_SRC, MA_CGI, "CGI art. 19-IV-B; art. 15",
             "montant des produits bruts [...] perçus par les personnes physiques ou morales non "
             "résidentes, énumérés à l'article 15 — 10% (royalties, interest on loans)")
    sd.wht(ma, "INTEREST", "10", start, ir)
    sd.wht(ma, "ROYALTY", "10", start, ir)
    sd.regime(
        ma, start,
        Src(MA_SRC, MA_CGI, "CGI art. 6-I-C-1°",
            "Ces produits [...] ainsi que ceux de source étrangère sont compris dans les "
            "produits financiers de la société bénéficiaire avec un abattement de 100%"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Domestic and foreign dividends 100% deducted with no holding test; share gains "
        "taxed. No CFC rules. Casablanca Finance City regime not modelled",
    )

    # Morocco has signed but not ratified the MLI — no PPT on either treaty.
    t = sd.treaty(fr, ma, name="Convention between France and Morocco (1970, as amended 1989)",
                  signed=date(1970, 5, 29), in_force=date(1971, 12, 1), src=Src(
                      "Convention France–Maroc (impots.gouv.fr)", FR_MA, None,
                      "signée à Paris le 29 mai 1970 — entrée en vigueur le 1er décembre 1971; "
                      "avenant du 18 août 1989 en vigueur le 1er décembre 1990"))
    src = "Convention France–Maroc (impots.gouv.fr)"
    start = date(1991, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 13", start, Src(
        src, FR_MA, "Article 13(3)", "l'impôt ainsi établi ne peut excéder 15 p. cent du "
        "montant brut des dividendes"), max_rate="15")
    sd.treaty_rate(t, "INTEREST", "Article 14", start, Src(
        src, FR_MA, "Article 14(2)", "10 p. cent du montant brut des autres intérêts (15% on "
        "term deposits and cash bonds)"), max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 16", start, Src(
        src, FR_MA, "Article 16(2)", "ne peut excéder 10 p. cent (patents, trademarks, "
        "know-how; 5% for copyright)"), max_rate="10")

    t = sd.treaty(ma, ae, name="Agreement between Morocco and the UAE (1999)",
                  signed=date(1999, 2, 9), in_force=date(2000, 7, 2), src=Src(
                      "MLI position of the UAE — instrument of deposit (OECD)",
                      "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/"
                      "beps-mli/beps-mli-position-united-arab-emirates-instrument-deposit.pdf",
                      None, "Morocco Original 09-02-1999 02-07-2000"))
    src = "اتفاقية المغرب–الإمارات (UAE Ministry of Finance, scanned Arabic text)"
    start = date(2001, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, MA_AE, "Article 10(2)(b)", "10% [...] في جميع الحالات الأخرى"), max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, MA_AE, "Article 10(2)(a)",
        "5% [...] إذا كان المستفيد الفعلي شركة التي في حوزتها مباشرة ما لا يقل عن 10% من رأس "
        "مال الشركة"), max_rate="5", ownership_threshold="10")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, MA_AE, f"{art}(2)", "لا يمكن أن تتجاوز 10% (may not exceed 10%)"),
            max_rate="10")


def _tunisia(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, tn: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(tn, start, Src(
        TN_SRC, TN_CODE, "Code IRPP/IS art. 49-I",
        "Le taux de l'impôt sur les sociétés [...] est fixé à 20% (35% and 40% for listed "
        "sectors; profits from 1 Jan 2024)"), rate="20")
    sd.wht(tn, "DIVIDEND", "10", start, Src(
        TN_SRC, TN_CODE, "art. 52-I c bis)", "10% au titre des revenus distribués"))
    sd.wht(tn, "INTEREST", "20", start, Src(
        TN_SRC, TN_CODE, "art. 52-I c)", "20% au titre des revenus de capitaux mobiliers (10% "
        "on loans from non-resident banks, art. 52-I e))"))
    sd.wht(tn, "ROYALTY", "15", start, Src(
        TN_SRC, TN_CODE, "art. 52-I b)", "15% au titre [...] des rémunérations et revenus "
        "servis aux non domiciliés ni établis (25% to privileged-tax regimes)"))
    sd.regime(
        tn, start,
        Src(TN_SRC, TN_CODE, "art. 48-III; art. 29-I",
            "sont déductibles pour la détermination du bénéfice imposable, les revenus "
            "distribués (Tunisian payers only)"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="Only dividends from Tunisian companies are deductible; foreign dividends and "
        "share gains taxed at 20%. No CFC rules",
    )

    t = sd.treaty(fr, tn, name="Convention between France and Tunisia (1973)",
                  signed=date(1973, 5, 28), in_force=date(1975, 4, 1), src=Src(
                      "Convention France–Tunisie modifiée par la CML (impots.gouv.fr)", FR_TN,
                      None, "signée à Tunis le 28 mai 1973 — entrée en vigueur le 1er avril "
                      "1975"))
    src = "Convention France–Tunisie modifiée par la CML (impots.gouv.fr)"
    start = date(1976, 1, 1)
    # Dividends: art. 14(2) leaves the source State its own law (no cap) — not seeded.
    sd.treaty_rate(t, "INTEREST", "Article 18", start, Src(
        src, FR_TN, "Article 18(2)", "un taux qui ne peut excéder 12 p. cent du montant "
        "versé"), max_rate="12")
    sd.treaty_rate(t, "ROYALTY", "Article 19", start, Src(
        src, FR_TN, "Article 19(2)", "15 p. cent (patents, designs, know-how; 5% copyright; "
        "20% trademarks, films and equipment)"), max_rate="15")
    sd.ppt(t, date(2024, 1, 1), Src(
        src, FR_TN, "MLI art. 7(1)",
        "s'agissant des impôts prélevés à la source [...] si le fait générateur de ces impôts "
        "intervient à compter du 1er janvier 2024"))

    t = sd.treaty(tn, ae, name="Convention between Tunisia and the UAE (1996)",
                  signed=date(1996, 4, 10), in_force=date(1997, 5, 27), src=Src(
                      "Convention Tunisie–EAU (DGI Tunisie, jibaya.tn)", TN_AE, None,
                      "Date de signature : le 10/04/1996 [...] impôts retenus à la source : le "
                      "27/06/1997 (UAE MLI position: in force 27-05-1997)"))
    src = "Convention Tunisie–EAU (DGI Tunisie, jibaya.tn)"
    start = date(1997, 6, 27)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, TN_AE, "Article 10(1)", "ne sont imposables dans aucun des Etats contractants"),
        exclusive=True)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, TN_AE, "Article 11(2)", "10% dans les autres cas (2.5%-5% for banks)"),
        max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, TN_AE, "Article 12(2)", "7,5% du montant brut des redevances"), max_rate="7.5")
    sd.ppt(t, date(2024, 1, 1), Src(
        "MLI position of Tunisia — instrument of deposit (OECD)",
        "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/"
        "beps-mli-position-tunisia-instrument-deposit.pdf", "MLI art. 7(1)",
        "34 Émirats Arabes Unis (covered by both; MLI in force for Tunisia 1 Nov 2023)"))


def _kenya(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, ke: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(ke, start, Src(
        KE_SRC, KE_ITA, "ITA Third Schedule, Head B, para 2(a)(ix)",
        "for the year of income 2021 and each subsequent year of income. 6.00 (shillings per "
        "twenty — 30%)"), rate="30")
    head_b = "ITA Third Schedule, Head B, para 3"
    sd.wht(ke, "DIVIDEND", "15", start, Src(
        KE_SRC, KE_ITA, f"{head_b}(d)", "in respect of a dividend, fifteen per cent of the "
        "amount payable"))
    sd.wht(ke, "INTEREST", "15", start, Src(
        KE_SRC, KE_ITA, f"{head_b}(e)(i)", "interest and deemed interest, discount or original "
        "issue discount, fifteen per cent of the gross sum payable"))
    sd.wht(ke, "ROYALTY", "20", start, Src(
        KE_SRC, KE_ITA, f"{head_b}(b)", "twenty per cent of the gross amount payable"))
    sd.regime(
        ke, start,
        Src(KE_SRC, KE_ITA, "ITA s.7(2)",
            "a dividend received by a resident company, other than a dividend received by a "
            "company which controls directly or indirectly less than twelve and one-half per "
            "cent of the voting power [...] shall be deemed not to be income chargeable to tax"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=12.5, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Dividends exempt at ≥12.5% of voting power; share gains bear 15% CGT; treaty "
        "benefits denied to ≥50% foreign-owned recipients (s.41(2)). No CFC rules",
    )

    t = sd.treaty(fr, ke, name="Convention between France and Kenya (2007)",
                  signed=date(2007, 12, 4), in_force=date(2010, 11, 1), src=Src(
                      "Convention France–Kenya modifiée par la CML et la clause NPF "
                      "(impots.gouv.fr)", FR_KE, None,
                      "Convention avec le Kenya signée le 04/12/2007 - en vigueur au "
                      "01/11/2010"))
    src = "Convention France–Kenya modifiée par la CML et la clause NPF (impots.gouv.fr)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(2011, 1, 1), Src(
        src, FR_KE, "Article 10(2)(b)", "10 % [...] dans tous les autres cas"), max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(2017, 4, 3), Src(
        src, FR_KE, "Article 10(2)(a) (MFN, Kenya–Korea treaty)",
        "8 % [...] si le bénéficiaire effectif est une société (autre qu'une société de "
        "personnes) qui détient directement au moins 25 pour cent du capital"),
        max_rate="8", ownership_threshold="25")
    sd.treaty_rate(t, "INTEREST", "Article 11", date(2011, 1, 1), Src(
        src, FR_KE, "Article 11(2)", "ne peut excéder 12 % du montant brut des intérêts"),
        max_rate="12")
    sd.treaty_rate(t, "ROYALTY", "Article 12", date(2011, 1, 1), Src(
        src, FR_KE, "Article 12(2)", "ne peut excéder 10 % du montant brut des redevances"),
        max_rate="10")
    sd.ppt(t, date(2026, 1, 1), Src(
        src, FR_KE, "MLI art. 7(1)",
        "si le fait générateur de ces impôts intervient à compter du 1er janvier 2026"))

    t = sd.treaty(ke, ae, name="Agreement between Kenya and the UAE (2011)",
                  signed=date(2011, 11, 21), in_force=date(2017, 2, 22), src=Src(
                      "MLI position of Kenya (OECD)",
                      "https://www.oecd.org/tax/treaties/beps-mli-position-kenya.pdf", None,
                      "United Arab Emirates Original 21/11/2011 22/02/2017"))
    src = "Agreement UAE–Kenya (UAE Ministry of Finance)"
    start = date(2018, 1, 1)
    for cat, art, rate in (("DIVIDEND", "Article 11", "5"), ("INTEREST", "Article 12", "10"),
                           ("ROYALTY", "Article 13", "10")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, KE_AE, f"{art}(2)", f"shall not exceed {rate} percent of the gross amount"),
            max_rate=rate)
    sd.ppt(t, date(2026, 1, 1), Src(
        "MLI position of Kenya (OECD)",
        "https://www.oecd.org/tax/treaties/beps-mli-position-kenya.pdf", "MLI art. 7(1)",
        "covered by both (KE No. 15, UAE No. 54); MLI in force for Kenya 1 May 2025"))


def _sudan(sd: Seeder, ae: Jurisdiction, sd_: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(sd_, start, Src(
        SD_SRC, SD_ITA, "ITA 1986 Third Schedule (A)(c)(2), as amended 2019",
        "يحذف الرقم \"15%\" ويستعاض عنه بالرقم \"30%\" [...] ويعمل به من فترة الأساس لسنة "
        "2019 (companies: 30% from basis period 2019)"), rate="30")
    sd.wht(sd_, "DIVIDEND", "0", start, Src(
        SD_SRC, SD_ITA, "ITA 1986 s.10(a)(iii)",
        "بخلاف حصة أرباح الأسهم المقبوضة من أرباح خاضعة للضريبة (dividends out of taxed "
        "profits are not taxed again; no dividend withholding in the Act)"))
    # s.65(1)(k): withholding on non-resident companies at a rate set by ministerial order —
    # the orders were not found, so interest and royalty withholding is not seeded.
    sd.regime(
        sd_, start,
        Src(SD_SRC, SD_ITA, "ITA 1986 s.10(a)(iii)",
            "بخلاف حصة أرباح الأسهم المقبوضة من أرباح خاضعة للضريبة بموجب أحكام هذا القانون "
            "(only dividends out of Sudanese-taxed profits excluded)"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="Foreign dividends treated as taxable; share gains bear 2% capital gains tax. No "
        "CFC rules. No France treaty; not in the MLI",
    )

    t = sd.treaty(sd_, ae, name="Agreement between Sudan and the UAE (2001)",
                  signed=date(2001, 3, 18), in_force=date(2004, 6, 6), src=Src(
                      "UAE Ministry of Finance — list of double taxation agreements",
                      "https://mof.gov.ae/wp-content/uploads/2023/08/Avoidance-of-Double-"
                      "Taxation-Agreements1.pdf", None, "Sudan [...] 6/6/2004"))
    src = "اتفاقية السودان–الإمارات (Taxation Chamber, scanned Arabic text)"
    start = date(2005, 1, 1)
    for cat, art in (("DIVIDEND", "Article 10"), ("INTEREST", "Article 11")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, SD_AE, f"{art}(1)", "تخضع [...] للضريبة فقط في تلك الدولة الأخرى (taxable "
            "only in the other State)"), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, SD_AE, "Article 12(2)", "لا يمكن أن تتجاوز 5% (خمسة بالمائة) من المبلغ الإجمالي "
        "للإتاوات"), max_rate="5")
