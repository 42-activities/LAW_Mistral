"""P8 Middle East wave 2: Egypt, Türkiye, Jordan, Lebanon, Iraq — plus list status only for
Iran, Syria and Yemen (sanctioned / no reliable tax sources: they rank as incomplete, with
their FATF and EU AML guardrails visible).

Figures were sourced on 2026-10-05; every `Src` cites the text fetched. All evidence is
`unreviewed` until a named reviewer confirms it (spec §10). Research notes:
docs/superpowers/plans/2026-10-05-p8-batch7.md.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.seed.builder import Seeder, Src

ETA = "https://eta.gov.eg/sites/default/files/{}"
EG_151 = ETA.format("2026-08/law.no_.151.of_.2026.pdf")
EG_30 = ETA.format("2024-03/law_no.30-2023.pdf")
FR_EG = "https://www.impots.gouv.fr/10conventionsegypteversion-consolidee-egyptepdf"
EG_AE = ETA.format("2024-09/alamarat.pdf")
PWC = "https://taxsummaries.pwc.com/{}"
FR_JO = (
    "https://www.impots.gouv.fr/"
    "version-consolidee-de-la-convention-avec-la-jordanie-modifiee-par-la-convention-multilaterale"
)
TR_KVK = "https://www.mevzuat.gov.tr/mevzuatmetin/1.5.5520.pdf"
TR_SRC = "Kurumlar Vergisi Kanunu 5520, consolidated (mevzuat.gov.tr, to Law 7590)"
FR_TR = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/turquie/"
    "turquie_convention-avec-la-turquie_fd_1780.pdf"
)
TR_AE = (
    "https://cdn.gib.gov.tr/api/gibportal-file/file/getFileResources?objectKey=arsiv/mevzuat/"
    "uluslararasi_mevzuat/TURKCE_METIN/BAE.pdf"
)
FR_LB = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/liban/"
    "liban_convention-avec-le-liban_fd_1916.pdf"
)
IQ_ITL = "https://tax.mof.gov.iq/قانون-ضريبة-الدخل-رقم-113-لسنة-1982-وتعديلاته/"
FATF = (
    "https://www.fatf-gafi.org/en/publications/High-risk-and-other-monitored-jurisdictions/{}.html"
)
EU_AML = "http://publications.europa.eu/resource/celex/{}"
EU_ANNEX = "http://publications.europa.eu/resource/celex/{}"
OECD_EOIR = "https://datawrapper.dwcdn.net/LGXCI/73/dataset.csv"


def seed_batch_me2(session: Session) -> None:
    sd = Seeder(session)
    fr = sd.jurisdiction("FR", "France")
    ae = sd.jurisdiction("AE", "United Arab Emirates")
    _qatar_treaties(sd)
    eg = sd.jurisdiction("EG", "Egypt")
    _egypt(sd, fr, ae, eg)
    sd.listing(eg, "GLOBAL_FORUM_RATING", "partially_compliant", date(2024, 1, 1), None, Src(
        "OECD Global Forum EOIR ratings table (embedded on oecd.org)", OECD_EOIR, None,
        "Egypt (Round 2),2024,Partially Compliant"))
    tr = sd.jurisdiction("TR", "Türkiye")
    _turkiye(sd, fr, ae, tr)
    sd.listing(tr, "EU_TAX_ANNEX_II", "state_of_play", date(2025, 2, 18), None, Src(
        "Council conclusions on the EU list of non-cooperative jurisdictions, 17 Feb 2026 "
        "(OJ C/2026/1465)", EU_ANNEX.format("52026XG01465"), "Annex II §1.1",
        "The following jurisdiction is expected to effectively exchange information with all "
        "27 Member States [...] : Türkiye"))
    _lists(sd)
    _lebanon(sd, fr, ae, sd.jurisdiction("LB", "Lebanon"))
    _iraq(sd, sd.jurisdiction("IQ", "Iraq"))
    jo = sd.jurisdiction("JO", "Jordan")
    _jordan(sd, fr, ae, jo)
    sd.listing(jo, "EU_TAX_ANNEX_II", "state_of_play", date(2025, 10, 10), None, Src(
        "Council conclusions on the EU list of non-cooperative jurisdictions, 17 Feb 2026 "
        "(OJ C/2026/1465)", EU_ANNEX.format("52026XG01465"), "Annex II §1.1",
        "in time to be reflected in the Global Forum AEOI peer review report in 2026: Jordan "
        "and Montenegro (first listed in the October 2025 conclusions)"))


def _qatar_treaties(sd: Seeder) -> None:
    qa = sd.jurisdiction("QA", "Qatar")
    cy = sd.jurisdiction("CY", "Cyprus")
    at = sd.jurisdiction("AT", "Austria")
    cy_qa = "https://www.gov.cy/media/sites/11/2024/03/quatar_en-66069ca6cbbe9.pdf"
    src = "Agreement between Cyprus and Qatar (Cyprus Ministry of Finance, Official Gazette)"
    t = sd.treaty(cy, qa, name="Agreement between Cyprus and Qatar (2008)",
                  signed=date(2008, 11, 11), in_force=date(2009, 3, 20), src=Src(
                      "Cyprus Ministry of Finance — double tax treaties list",
                      "https://www.gov.cy/mof/en/documents/double-tax-treaties/", None,
                      "50 Qatar 11/11/2008 20/03/2009 4099 – 14/11/2008"))
    start = date(2010, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, cy_qa, "Article 10(1)",
        "Dividends paid by a company which is a resident of a Contracting State to a resident "
        "of the other Contracting State shall be taxable only in that other State."),
        exclusive=True)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, cy_qa, "Article 11(1)",
        "Interest arising in a Contracting State and paid to a resident of the other "
        "Contracting State shall be taxable only in that other State."), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, cy_qa, "Article 12(2)",
        "if the beneficial owner of the royalties is a resident of the other Contracting "
        "State, the tax so charged shall not exceed 5 per cent of the gross amount of the "
        "royalties"), max_rate="5")
    sd.ppt(t, date(2021, 1, 1), Src(
        "MLI position of Qatar — consolidated (OECD)",
        "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/"
        "beps-mli-position-qatar-consolidated.pdf", "MLI art. 7(1)",
        "Cyprus Original 11/11/2008 20/03/2009 (covered by both; MLI in force for Cyprus 1 May "
        "2020 — WHT effect from 1 Jan 2021 under MLI art. 35(1)(a))"))

    # Not an MLI covered agreement (Austria never listed Qatar; Qatar dropped Austria at
    # deposit): no PPT.
    at_qa = (
        "https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&"
        "Gesetzesnummer=20007728"
    )
    src = "DBA Österreich–Katar, BGBl. III Nr. 52/2012 (RIS)"
    t = sd.treaty(at, qa, name="Convention between Austria and Qatar (2010)",
                  signed=date(2010, 12, 30), in_force=date(2012, 3, 7), src=Src(
                      src, at_qa, "Article 29(1)",
                      "Die Mitteilungen gemäß Art. 29 Abs. 1 des Abkommens wurden am 26. "
                      "September 2011 bzw. 6. Februar 2012 abgegeben; das Abkommen tritt gemäß "
                      "derselben Bestimmung mit 7. März 2012 in Kraft."))
    start = date(2013, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, at_qa, "Article 10(1)",
        "Dividenden, die eine in einem Vertragsstaat ansässige Gesellschaft an eine im anderen "
        "Vertragsstaat ansässige Person zahlt, dürfen nur im anderen Staat besteuert werden."),
        exclusive=True)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, at_qa, "Article 11(1)",
        "Zinsen [...] dürfen, wenn diese Person der Nutzungsberechtigte ist, nur im anderen "
        "Staat besteuert werden."), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, at_qa, "Article 12(2)",
        "die Steuer darf aber [...] 5 vom Hundert des Bruttobetrags der Lizenzgebühren nicht "
        "übersteigen"), max_rate="5")


def _lists(sd: Seeder) -> None:
    grey_jun = Src(
        "FATF — Jurisdictions under increased monitoring, 19 June 2026 (read via Wayback "
        "snapshot 2026-10-01)", FATF.format("increased-monitoring-june-2026"), None,
        "Haiti, Iraq, Kenya, Kuwait, Lao PDR, Lebanon, Monaco, Nepal, Papua New Guinea, South "
        "Sudan, Syria, Venezuela, Vietnam, Virgin Islands (UK), Yemen")
    aml = Src(
        "Delegated Regulation (EU) 2016/1675, consolidated 29 Jan 2026 (Publications Office)",
        EU_AML.format("02016R1675-20260129"), "Annex points I-II",
        "I: [...] 12 Lebanon [...] 18 Syria [...] 23 Yemen; II: 1 Iran")
    lb = sd.jurisdiction("LB", "Lebanon")
    iq = sd.jurisdiction("IQ", "Iraq")
    ir = sd.jurisdiction("IR", "Iran")
    sy = sd.jurisdiction("SY", "Syria")
    ye = sd.jurisdiction("YE", "Yemen")
    sd.listing(lb, "FATF_GREY", "increased_monitoring", date(2024, 10, 25), None, grey_jun)
    sd.listing(iq, "FATF_GREY", "increased_monitoring", date(2026, 6, 19), None, grey_jun)
    sd.listing(sy, "FATF_GREY", "increased_monitoring", date(2010, 2, 18), None, grey_jun)
    sd.listing(ye, "FATF_GREY", "increased_monitoring", date(2010, 2, 18), None, grey_jun)
    sd.listing(ir, "FATF_BLACK", "call_for_action", date(2020, 2, 21), None, Src(
        "FATF — High-risk jurisdictions subject to a call for action, 19 June 2026 (read via "
        "Wayback snapshot 2026-09-22)", FATF.format("call-for-action-june-2026"), None,
        "the FATF reiterates its call on its members and urges all jurisdictions to apply "
        "effective countermeasures on Iran"))
    sd.listing(lb, "EU_AML_HIGH_RISK", "high_risk", date(2025, 8, 5), None, Src(
        "Delegated Regulation (EU) 2025/1184 (Publications Office)",
        EU_AML.format("32025R1184"), None,
        "to add Algeria, Angola, Côte d'Ivoire, Kenya, Laos, Lebanon, [...] and to remove [...] "
        "Uganda and the United Arab Emirates from that list"))
    for j in (ir, sy, ye):
        sd.listing(j, "EU_AML_HIGH_RISK", "high_risk", date(2016, 9, 23), None, aml)


def _egypt(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, eg: Jurisdiction) -> None:
    start = date(2023, 5, 1)
    sd.cit(eg, start, Src(
        "Law 96/2015 amending Income Tax Law 91/2005 (ETA)",
        ETA.format("2024-03/law_no.96-2015.pdf"), "ITL art. 49",
        "ويخضع للضريبة بسعر (22.5٪) من صافى الأرباح السنوية (22.5% of annual net profits)"),
        rate="22.5")
    sd.wht(eg, "DIVIDEND", "10", start, Src(
        "Law 151/2026 amending Income Tax Law 91/2005 (ETA)", EG_151, "ITL art. 56 bis",
        "تخضع للضريبة بسعر (10٪) دون خصم أية تكاليف توزيعات الأرباح [...] للشخص الطبيعى غير "
        "المقيم والشخص الاعتبارى المقيم أو غير المقيم (10%; 5% on EGX-listed securities)"))
    ir = Src(
        "Income Tax Law 91/2005 (ETA)", ETA.format("2024-03/law_no.91-2005.pdf"),
        "ITL art. 56",
        "تخضع للضريبة بسعر 20٪ المبالغ التى يدفعها [...] لغير المقيمين فى مصر [...] 1- "
        "العوائد. 2- الإتاوات (20% on interest and royalties paid to non-residents)")
    sd.wht(eg, "INTEREST", "20", start, ir)
    sd.wht(eg, "ROYALTY", "20", start, ir)
    sd.regime(
        eg, start,
        Src("Law 30/2023 amending Income Tax Law 91/2005 (ETA)", EG_30, "ITL art. 50(10)",
            "بعد إضافة نسبة (10٪) من قيمة التوزيعات إلى الوعاء [...] مقابل تكاليف غير واجبة "
            "الخصم (exempt at ≥25% for 2 years, 10% added back)"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=25, min_holding_period_months=24, subject_to_tax_condition=False,
        end=date(2026, 7, 29), exempt_share_pct=90,
        notes="Dividends from resident and non-resident subsidiaries exempt at ≥25% for 2 "
        "years with a 10% add-back; gains on foreign shares taxed",
    )
    sd.regime(
        eg, date(2026, 7, 29),
        Src("Law 151/2026 amending Income Tax Law 91/2005 (ETA)", EG_151, "ITL art. 50(10)",
            "توزيعات الأرباح التى تحصل عليها الشركة الأم أو الشركة القابضة من الشركات التابعة "
            "المقيمة وغير المقيمة [...] (أ) ألا تقل مساهمة [...] عن (25٪) [...] (ب) ألا تقل "
            "مدة الحيازة [...] عن سنتين"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=25, min_holding_period_months=24, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Law 151/2026 removed the 10% add-back; gains on foreign shares taxed. No CFC "
        "rules",
    )

    t = sd.treaty(fr, eg, name="Convention between France and Egypt (1980, as amended 1999)",
                  signed=date(1980, 6, 19), in_force=date(1982, 10, 1), src=Src(
                      "Convention France–Égypte, version consolidée (impots.gouv.fr)", FR_EG,
                      None, "entrée en vigueur le 1er octobre 1982 [...] Avenant signé au Caire "
                      "le 1er mai 1999 [...] entré en vigueur le 1er juin 2004"))
    start = date(2005, 1, 1)
    src = "Convention France–Égypte, version consolidée (impots.gouv.fr)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_EG, "Article 10(1)",
        "Les dividendes payés par une société qui est un résident d'un Etat à un bénéficiaire "
        "effectif qui est un résident de l'autre Etat ne sont imposables que dans cet autre "
        "Etat"), exclusive=True)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, FR_EG, "Article 11(2)",
        "l'impôt ainsi établi ne peut excéder 15 p. cent du montant brut des intérêts"),
        max_rate="15")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, FR_EG, "Article 12(2)", "ne peut excéder 15 p. cent du montant brut des redevances"),
        max_rate="15")
    sd.ppt(t, date(2021, 1, 1), Src(
        src, FR_EG, "MLI art. 7(1)",
        "un avantage [...] ne sera pas accordé [...] s'il est raisonnable de conclure [...] que "
        "l'octroi de cet avantage était l'un des objets principaux d'un montage — si le fait "
        "générateur de ces impôts intervient à compter du 1er janvier 2021"))

    # 2019 agreement replaced the 1994 one; entry-into-force date not in the official text —
    # WHT effect from 1 Jan 2022 per PwC (secondary).
    t = sd.treaty(eg, ae, name="Agreement between Egypt and the UAE (2019)",
                  signed=date(2019, 11, 14), in_force=None, src=Src(
                      "اتفاقية مصر–الإمارات 2019 (ETA, Official Gazette No. 22, 3 June 2021)",
                      EG_AE, "Article 31",
                      "ينتهي العمل بالاتفاقية الموقعة [...] في القاهرة بتاريخ [...] 12 أبريل "
                      "1994م (WHT effect from 1 Jan 2022 per PwC — secondary)"))
    start = date(2022, 1, 1)
    src = "اتفاقية مصر–الإمارات 2019 (ETA)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, EG_AE, "Article 10(2)(b)", "10% in all other cases"), max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, EG_AE, "Article 10(2)(a)",
        "(5٪) [...] شركة [...] تمتلك بصورة مباشرة على الأقل (10٪) من رأس مال الشركة الدافعة "
        "[...] خلال مدة 365 يوماً"), max_rate="5", ownership_threshold="10",
        min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, EG_AE, "Article 11(2)", "ألا تزيد [...] عن (10٪) من إجمالي مبلغ الفوائد"),
        max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, EG_AE, "Article 12(2)", "(10٪) بالمائة من إجمالي مبلغ الإتاوات"), max_rate="10")
    sd.ppt(t, start, Src(
        src, EG_AE, "Article 30",
        "أن الحصول على هذه المزايا هو الهدف أو أحد الأهداف الرئيسية (treaty's own PPT)"))


def _jordan(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, jo: Jurisdiction) -> None:
    # istd.gov.jo and lob.gov.jo unreachable: domestic figures are secondary (PwC, Jul 2026).
    start = date(2025, 1, 1)
    sd.cit(jo, start, Src(
        "Jordan corporate taxes (PwC Worldwide Tax Summaries — secondary source)",
        PWC.format("jordan/corporate/taxes-on-corporate-income"), "Income Tax Law 34/2014",
        "20% for all other companies. [national contribution tax:] Other companies not listed "
        "above 1 (%) — 20% + 1% stored"), rate="21")
    sd.wht(jo, "DIVIDEND", "0", start, Src(
        "Jordan withholding taxes (PwC Worldwide Tax Summaries — secondary source)",
        PWC.format("jordan/corporate/withholding-taxes"), None,
        "Dividends payable by a Jordan-incorporated and resident company to both resident and "
        "non-resident companies are exempt from WHT in Jordan"))
    other = Src(
        "Jordan withholding taxes (PwC Worldwide Tax Summaries — secondary source)",
        PWC.format("jordan/corporate/withholding-taxes"), None,
        "WHT at a rate of 10% and national contribution tax [...] apply to any imported "
        "services provided by a non-resident legal entity (10% assumed for interest and "
        "royalties; bank interest 7%)")
    sd.wht(jo, "INTEREST", "10", start, other)
    sd.wht(jo, "ROYALTY", "10", start, other)
    sd.regime(
        jo, start,
        Src("Jordan income determination (PwC Worldwide Tax Summaries — secondary source)",
            PWC.format("jordan/corporate/income-determination"), None,
            "dividend income received by Jordanian taxpayers from a non-resident legal entity "
            "[...] is also subject to both income tax and national contribution tax"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="Foreign dividends treated as taxable (secondary sources conflict with the "
        "territoriality rule). No CFC rules",
    )

    t = sd.treaty(fr, jo, name="Convention between France and Jordan (1984)",
                  signed=date(1984, 5, 28), in_force=date(1985, 4, 1), src=Src(
                      "Convention France–Jordanie modifiée par la CML (impots.gouv.fr)", FR_JO,
                      None, "signée à Amman le 28 mai 1984 [...] entrée en vigueur le 1er "
                      "avril 1985"))
    start = date(2021, 1, 1)
    src = "Convention France–Jordanie modifiée par la CML (impots.gouv.fr)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_JO, "Article 10(2)(b)", "b) 15 p. cent [...] dans tous les autres cas"),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_JO, "Article 10(2)(a); MLI art. 8",
        "a) 5 p. cent du montant brut des dividendes si le bénéficiaire effectif est une "
        "société [...] qui détient directement au moins 10 p. cent du capital [...] tout au "
        "long d'une période de 365 jours incluant le jour du paiement des dividendes"),
        max_rate="5", ownership_threshold="10", min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, FR_JO, "Article 11(2)", "ne peut excéder 15 p. cent du montant brut des intérêts "
        "(0% on bank loans, art. 11(3))"), max_rate="15")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, FR_JO, "Article 12(2)", "15 p. cent [...] dans tous les autres cas (25% for "
        "trademarks, 5% for copyright)"), max_rate="15")
    sd.ppt(t, start, Src(
        src, FR_JO, "MLI art. 7(1)",
        "un avantage au titre de celle-ci ne sera pas accordé [...] s'il est raisonnable de "
        "conclure [...] que l'octroi de cet avantage était l'un des objets principaux d'un "
        "montage"))

    t = sd.treaty(jo, ae, name="Agreement between Jordan and the UAE (2016)",
                  signed=date(2016, 4, 5), in_force=date(2017, 1, 10), src=Src(
                      "MLI position of Jordan — instrument of deposit (OECD)",
                      "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/"
                      "beps-mli/beps-mli-position-jordan-instrument-deposit.pdf", None,
                      "United Arab Emirates Original 05-04-2016 10-01-2017"))
    for cat, art, rate in (("DIVIDEND", "Article 10", "7"), ("INTEREST", "Article 11", "7"),
                           ("ROYALTY", "Article 12", "10")):
        sd.treaty_rate(t, cat, art, date(2018, 1, 1), Src(
            "Jordan withholding taxes (PwC Worldwide Tax Summaries — secondary source)",
            PWC.format("jordan/corporate/withholding-taxes"), art,
            "United Arab Emirates 1/1/2018 7 7 10 (official treaty text not retrieved)"),
            max_rate=rate)
    sd.ppt(t, date(2021, 1, 1), Src(
        "MLI position of the UAE — instrument of deposit (OECD)",
        "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/"
        "beps-mli-position-united-arab-emirates-instrument-deposit.pdf", "MLI art. 7(1)",
        "Jordan Original 05-04-2016 10-01-2017 (covered by both; no PPT reservation; MLI in "
        "force for Jordan 1 Jan 2021)"))


def _turkiye(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, tr: Jurisdiction) -> None:
    start = date(2025, 1, 1)
    sd.cit(tr, start, Src(
        TR_SRC, TR_KVK, "KVK md. 32(1)",
        "Kurumlar vergisi, kurum kazancı üzerinden %25 oranında alınır (10% domestic minimum "
        "tax under md. 32/C not modelled)"), rate="25")
    sd.wht(tr, "DIVIDEND", "15", start, Src(
        "Cumhurbaşkanı Kararı 9286 (RG 22/12/2024) amending BKK 2009/14593",
        "https://www.resmigazete.gov.tr/eskiler/2024/12/20241222-9.pdf", "KVK md. 30(3)",
        "(12) ve (14) numaralı bentlerinde yer alan '% 10' ibareleri '% 15' şeklinde "
        "değiştirilmiştir"))
    bkk = "BKK 2009/14593 (RG 3/2/2009, no. 27130)"
    bkk_url = "https://www.resmigazete.gov.tr/eskiler/2009/02/20090203-9.htm"
    sd.wht(tr, "INTEREST", "10", start, Src(
        bkk, bkk_url, "KVK md. 30(1)(ç); BKK item 5",
        "Diğerlerinden % 10 (loans from non-bank lenders; 0% from foreign banks and states)"))
    sd.wht(tr, "ROYALTY", "20", start, Src(
        bkk, bkk_url, "KVK md. 30(1)(c), 30(2); BKK items 3(b), 11",
        "telif, imtiyaz, ihtira, işletme, ticaret unvanı, marka ve benzeri gayrimaddi "
        "hakların [...] % 20"))
    sd.regime(
        tr, start,
        Src(TR_SRC, TR_KVK, "KVK md. 5(1)(b)",
            "ödenmiş sermayesinin en az % 10'una sahip olması [...] kesintisiz olarak en az bir "
            "yıl [...] en az % 15 oranında gelir ve kurumlar vergisi benzeri toplam vergi yükü"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=10, min_holding_period_months=12, subject_to_tax_condition=True,
        min_subject_to_tax_rate=15, exempt_share_pct=100,
        notes="Foreign dividends exempt at ≥10%, 1 year, ≥15% tax burden; share gains only "
        "50% exempt after 2 years (PD 9160) — treated as taxable",
    )
    sd.cfc(
        tr, start,
        Src(TR_SRC, TR_KVK, "KVK md. 7",
            "en az % 50'sine sahip olmak suretiyle kontrol [...] gayrisafî hasılatının % 25 "
            "veya fazlası [...] pasif nitelikli gelirlerden [...] % 10'dan az oranda [...] "
            "toplam vergi yükü"),
        control_threshold_pct=50, low_tax_relative_pct=40, threshold_inclusive=True,
        legal_ref="KVK md. 7",
        effect="Passive (≥25%) income of a ≥50%-controlled entity taxed below 10% (40% of the "
        "25% Turkish rate) is included.",
    )

    # Türkiye has signed but not ratified the MLI: no PPT on either treaty.
    t = sd.treaty(fr, tr, name="Convention between France and Türkiye (1987)",
                  signed=date(1987, 2, 18), in_force=date(1989, 7, 1), src=Src(
                      "Convention France–Turquie (impots.gouv.fr)", FR_TR, None,
                      "signée à Paris le 18 février 1987 [...] entrée en vigueur le 1er juillet "
                      "1989"))
    start = date(1990, 1, 1)
    src = "Convention France–Turquie (impots.gouv.fr)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_TR, "Article 10(2)(b)", "20 p. cent du montant brut des dividendes dans tous "
        "les autres cas"), max_rate="20")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_TR, "Article 10(2)(a)",
        "15 p. cent [...] société [...] qui détient directement au moins 10 p. cent du "
        "capital"), max_rate="15", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, FR_TR, "Article 11(2)", "ne peut excéder 15 p. cent du montant brut des "
        "intérêts"), max_rate="15")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, FR_TR, "Article 12(2)", "ne peut excéder 10 p. cent du montant brut des "
        "redevances"), max_rate="10")

    t = sd.treaty(tr, ae, name="Agreement between Türkiye and the UAE (1993)",
                  signed=date(1993, 1, 29), in_force=date(1994, 12, 26), src=Src(
                      "GİB list of double tax treaties (23.04.2025)", TR_AE, None,
                      "B.A.E. 29.01.1993 | RG 27.12.1994 – 22154 | yürürlük 26.12.1994 | "
                      "uygulama 01.01.1995"))
    start = date(1995, 1, 1)
    src = "Türkiye–BAE Anlaşması (GİB Turkish text)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, TR_AE, "Article 10(2)(c)", "Tüm diğer durumlarda 12 (GİB table)"), max_rate="12")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, TR_AE, "Article 10(2)(b)",
        "en az yüzde 25'ini elinde tutan bir şirket ise [...] yüzde 10"), max_rate="10",
        ownership_threshold="25")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, TR_AE, "Article 11(2)", "yüzde 10'unu aşmayacaktır"), max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, TR_AE, "Article 12(2)", "yüzde 10 (GİB table: 10)"), max_rate="10")


def _lebanon(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, lb: Jurisdiction) -> None:
    start = date(2025, 1, 1)
    sd.cit(lb, start, Src(
        "Ministry of Finance notice 4859/ص1 (14-11-2017)",
        "https://www.finance.gov.lb/en-us/Taxation/LRT/TP/Documents/4859.pdf",
        "Decree-Law 144/1959 art. 32; Law 64/2017",
        "بحيث أصبح معدل الضريبة على أرباح شركات الأموال ١٧% بدلاً من ١٥% (capital companies: "
        "17% instead of 15%)"), rate="17")
    sd.wht(lb, "DIVIDEND", "10", start, Src(
        "Ministry of Finance notice 4676/ص1 (2-11-2017)",
        "https://www.finance.gov.lb/en-us/Taxation/LRT/TP/Documents/4676.pdf",
        "Income Tax Law art. 72 bis; Law 64/2017",
        "بات يتوجب عليها اعتماد معدل ضريبة ١٠% على الأرباح التي تتخذ قراراً بتوزيعها اعتباراً "
        "من تاريخ ٢٠١٧/١٠/٢٧ (10% on profits distributed from 27-10-2017)"))
    pwc = "Lebanon withholding taxes (PwC Worldwide Tax Summaries — secondary source)"
    sd.wht(lb, "INTEREST", "10", start, Src(
        pwc, PWC.format("lebanon/corporate/withholding-taxes"), "Income Tax Law Chapter III",
        "A 10% WHT is levied on income derived from movable capital [...] Interest from loans "
        "to corporations."))
    sd.wht(lb, "ROYALTY", "8.5", date(2024, 4, 1), Src(
        pwc, PWC.format("lebanon/corporate/withholding-taxes"), "Income Tax Law arts. 41-43",
        "the 2024 Budget Law increased the WHT rates to 3.4% on payments for goods and 8.5% on "
        "payments for services, applicable starting [...] 1 April 2024"))
    sd.regime(
        lb, start,
        Src("Lebanon income determination (PwC Worldwide Tax Summaries — secondary source)",
            PWC.format("lebanon/corporate/income-determination"), None,
            "Dividends received as a result of a taxable person's activity are deemed trading "
            "income and are subject to 17% CIT. Dividends received as passive income are "
            "subject to 10% tax."),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="No participation exemption; share gains taxed at 15%. No CFC rules",
    )

    # Lebanon has not signed the MLI: no PPT. Royalties have no source-State cap.
    t = sd.treaty(fr, lb, name="Convention between France and Lebanon (1962)",
                  signed=date(1962, 7, 24), in_force=date(1963, 12, 28), src=Src(
                      "Convention France–Liban (impots.gouv.fr)", FR_LB, "Article 42",
                      "signée à Paris le 24 juillet 1962 [...] ratifiée à Beyrouth le 28 "
                      "novembre 1963 [...] Elle entrera en vigueur un mois après l'échange des "
                      "instruments de ratification"))
    for cat, art in (("DIVIDEND", "Article 15"), ("INTEREST", "Article 16")):
        sd.treaty_rate(t, cat, art, date(1964, 1, 1), Src(
            "Convention France–Liban (impots.gouv.fr)", FR_LB, f"{art}(1)",
            "ne sont imposables que dans cet autre Etat"), exclusive=True)

    t = sd.treaty(lb, ae, name="Convention between Lebanon and the UAE (1998)",
                  signed=date(1998, 5, 17), in_force=date(1999, 5, 21), src=Src(
                      "MLI position of the UAE — instrument of deposit (OECD)",
                      "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/"
                      "beps-mli/beps-mli-position-united-arab-emirates-instrument-deposit.pdf",
                      None, "Lebanon Original 17-05-1998 21-05-1999"))
    lb_ae = Src(
        "Lebanon withholding taxes (PwC Worldwide Tax Summaries — secondary source)",
        PWC.format("lebanon/corporate/withholding-taxes"), None,
        "United Arab Emirates | 0 (2) | 0 (2) | 5 — (2) taxable only in the residence State")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(2000, 1, 1), lb_ae, exclusive=True)
    sd.treaty_rate(t, "INTEREST", "Article 11", date(2000, 1, 1), lb_ae, exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", date(2000, 1, 1), lb_ae, max_rate="5")


def _iraq(sd: Seeder, iq: Jurisdiction) -> None:
    start = date(2025, 1, 1)
    src = "Income Tax Law 113/1982 as amended (General Commission for Taxes web text)"
    sd.cit(iq, start, Src(
        src, IQ_ITL, "ITL art. 13(1)",
        "ج- دخل الشركات المحدودة المسؤولية بنسبة ثابتة مقدارها 15%. د- دخل الشركات المساهمة "
        "الخاصة بنسبة ثابتة مقدارها 15%"), rate="15")
    sd.wht(iq, "DIVIDEND", "0", start, Src(
        src, IQ_ITL, "ITL art. 2(2), 15",
        "profit shares paid out of taxed profits are not taxable income (PwC: Dividends are not "
        "subject to WHT)"))
    sd.wht(iq, "INTEREST", "15", start, Src(
        src, IQ_ITL, "ITL art. 19(1)",
        "فوائد السندات والرهنيات والقروض والودائع والسلفات [...] وتكون نسبة الضريبة الواجبة "
        "التأدية عن مثل هذه المبالغ (15%)"))
    sd.wht(iq, "ROYALTY", "15", start, Src(
        "Iraq withholding taxes (PwC Worldwide Tax Summaries — secondary source)",
        PWC.format("iraq/corporate/withholding-taxes"), None,
        "royalties are taxed at the normal CIT rate when deemed to arise in Iraq (no specific "
        "statutory withholding rate — 15% stored)"))
    sd.regime(
        iq, start,
        Src(src, IQ_ITL, "ITL art. 5(1)",
            "تفرض الضريبة على دخل الشخص المقيم العراقي الذي يحصل عليه في العراق أو خارجه "
            "(worldwide taxation; foreign tax credit under art. 5(4))"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0, notes="Worldwide taxation, no participation exemption, no CFC rules",
    )
    # No France–Iraq treaty. Iraq–UAE in force 28-07-2021 but its text was not obtained —
    # not seeded.
