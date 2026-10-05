"""P8 batch 2: Germany, Belgium, Ireland, Malta.

Figures were sourced on 2026-10-05 from the official texts cited on each `Src` and are stored
as `unreviewed` until a named reviewer confirms them (spec §10). Research notes:
docs/superpowers/plans/2026-10-05-p8-batch2.md.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import JurisdictionGroup
from app.modules.seed.builder import Seeder, Src

EU_URL = "https://european-union.europa.eu/principles-countries-history/eu-countries/{}_en"
GII = "https://www.gesetze-im-internet.de/{}.html"
DE_MUC = "https://stadt.muenchen.de/service/info/gewerbesteuer/1074725/n0/"
REV = "https://www.revenue.ie/en/"
REV_TDM = REV + "tax-professionals/tdm/income-tax-capital-gains-tax-corporation-tax/"
FR_IE = REV + "tax-professionals/documents/double-taxation-treaties/f/france.pdf"
FR_IE_MLI = (
    REV + "tax-professionals/documents/double-taxation-treaties/f/"
    "synthesised-text-mli-ireland-france-dtc.pdf"
)
IE_AE = REV + "tax-professionals/documents/double-taxation-treaties/u/united-arab-emirates.pdf"
IE_AE_MLI = (
    REV + "tax-professionals/documents/double-taxation-treaties/u/"
    "synthesised-text-mli-ireland-uae-dtc.pdf"
)
MT_ITA = "https://legislation.mt/eli/cap/123/eng"
MT_ITMA = "https://legislation.mt/eli/cap/372/eng"
FR_MT = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/malte/"
    "malte_version-consolidee-de-l-accord-franco-maltais_fd_5661.pdf"
)
FR_MT_MLI = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/malte/"
    "accord_avec_malte_modifiee_par_la_cml.pdf"
)
MT_AE = "https://legislation.mt/eli/sl/123.106/eng"
MT_MLI = "https://legislation.mt/eli/sl/123.183/eng"
MB = "https://www.ejustice.just.fgov.be/eli/"
BE_2017 = MB + "loi/2017/12/25/2017014414/moniteur"
BE_2016 = MB + "loi/2016/12/25/2016021100/moniteur"
BE_IRD = MB + "arrete/2003/12/22/2003003582/moniteur"
BE_2002 = MB + "loi/2002/12/24/2002003520/moniteur"
BE_CFC = MB + "loi/2023/12/22/2023048600/moniteur"
BE_AE = MB + "loi/2002/08/02/2002015137/moniteur"
FR_BE = (
    "https://www.impots.gouv.fr/"
    "belgique-version-consolidee-de-la-convention-avec-la-belgique-modifiee-par-la-convention"
)
FR_DE = (
    "https://www.impots.gouv.fr/"
    "version-consolidee-de-la-convention-avec-lallemagne-modifiee-par-la-convention-multilaterale-impots"
)


def seed_batch_eu2(session: Session) -> None:
    sd = Seeder(session)
    fr = sd.jurisdiction("FR", "France")
    eu = sd.group("EU", "European Union member states")
    de = sd.jurisdiction("DE", "Germany")
    sd.member(eu, de, date(1958, 1, 1), Src(
        "Germany — EU member country profile (european-union.europa.eu)",
        EU_URL.format("germany"), None, "EU Member State: since 1 January 1958"))
    _germany(sd, fr, de, eu)
    ae = sd.jurisdiction("AE", "United Arab Emirates")
    ie = sd.jurisdiction("IE", "Ireland")
    mt = sd.jurisdiction("MT", "Malta")
    sd.member(eu, ie, date(1973, 1, 1), Src(
        "Ireland — EU member country profile (european-union.europa.eu)",
        EU_URL.format("ireland"), None, "EU Member State: since 1 January 1973"))
    sd.member(eu, mt, date(2004, 5, 1), Src(
        "Malta — EU member country profile (european-union.europa.eu)",
        EU_URL.format("malta"), None, "since 1 May 2004"))
    _ireland(sd, fr, ae, ie, eu)
    _malta(sd, fr, ae, mt)
    be = sd.jurisdiction("BE", "Belgium")
    sd.member(eu, be, date(1958, 1, 1), Src(
        "Belgium — EU member country profile (european-union.europa.eu)",
        EU_URL.format("belgium"), None, "EU Member State: since 1 January 1958"))
    _belgium(sd, fr, ae, be, eu)


def _germany(sd: Seeder, fr: Jurisdiction, de: Jurisdiction, eu: JurisdictionGroup) -> None:
    # Munich: KSt 15% + Soli 5.5% of KSt (0.825) + trade tax 3.5% × 490% (17.15) = 32.975%.
    # The KSt falls from 2028 (§23 KStG); later combined rates depend on the Hebesatz then in
    # force, so only 2026–2027 is seeded.
    sd.cit(de, date(2026, 1, 1), Src(
        "§23 KStG; §4 SolZG; §11 GewStG; Gewerbesteuer-Hebesatz München",
        DE_MUC, "§23 KStG, §4 SolZG, §11 GewStG",
        "Die Körperschaftsteuer beträgt für 1. Veranlagungszeiträume bis 2027 15 Prozent [...] "
        "Der Solidaritätszuschlag beträgt 5,5 Prozent [...] Die Steuermesszahl für den "
        "Gewerbeertrag beträgt 3,5 Prozent [...] multipliziert dann den Gewerbesteuermessbetrag "
        "mit dem aktuell gültigen Hebesatz von 490 Prozent (München)",
    ), rate="32.975", end=date(2028, 1, 1))
    sd.wht(de, "DIVIDEND", "15.825", date(2026, 1, 1), Src(
        "§43a / §44a(9) EStG (gesetze-im-internet.de)", GII.format("estg/__44a"),
        "§43a(1) Nr. 1, §44a(9) EStG",
        "Die Kapitalertragsteuer beträgt [...] 25 Prozent des Kapitalertrags [...] Ist der "
        "Gläubiger der Kapitalerträge [...] eine beschränkt steuerpflichtige Körperschaft [...] "
        "so werden zwei Fünftel der einbehaltenen und abgeführten Kapitalertragsteuer erstattet."
        " (25% + 5.5% Soli = 26.375% withheld; 15.825% after the refund)"))
    sd.wht(de, "INTEREST", "0", date(2026, 1, 1), Src(
        "§49 EStG (gesetze-im-internet.de)", GII.format("estg/__49"), "§49(1) Nr. 5 c) aa) EStG",
        "[Summary — no single clause to quote] Interest is German-source income of a "
        "non-resident only when secured on German real estate or registered ships "
        "(§49(1) Nr. 5 c) aa) EStG); otherwise no withholding."))
    sd.wht(de, "ROYALTY", "15.825", date(2026, 1, 1), Src(
        "§50a EStG (gesetze-im-internet.de)", GII.format("estg/__50a"), "§50a(2) EStG",
        "Der Steuerabzug beträgt 15 Prozent [...] (15% + 5.5% Soli = 15.825%)"))
    sd.exemption(
        de, "DIVIDEND", eu, date(2026, 1, 1),
        Src("§43b EStG (gesetze-im-internet.de)", GII.format("estg/__43b"), "§43b EStG",
            "nachweislich mindestens zu 10 Prozent unmittelbar am Kapital der "
            "Tochtergesellschaft beteiligt ist (Mindestbeteiligung) [...] Weitere Voraussetzung "
            "ist, dass die Beteiligung nachweislich ununterbrochen zwölf Monate besteht."),
        min_holding_pct="10", min_holding_months=12, legal_ref="§43b EStG",
        description="Parent-Subsidiary Directive: EU parent holding ≥10% for 12 months",
    )
    sd.exemption(
        de, "ROYALTY", eu, date(2026, 1, 1),
        Src("§50g EStG (gesetze-im-internet.de)", GII.format("estg/__50g"), "§50g EStG",
            "Auf Antrag werden [...] die Steuer auf Grund des § 50a für Lizenzgebühren [...] "
            "nicht erhoben [...] das erste Unternehmen unmittelbar mindestens zu 25 Prozent an "
            "dem Kapital des zweiten Unternehmens beteiligt ist"),
        min_holding_pct="25", min_holding_months=None, legal_ref="§50g EStG",
        description="Interest and Royalties Directive: associated EU company (≥25% direct)",
    )
    sd.regime(
        de, date(2026, 1, 1),
        Src("§8b KStG (gesetze-im-internet.de)", GII.format("kstg_1977/__8b"), "§8b KStG",
            "Von den Bezügen im Sinne des Absatzes 1, die bei der Ermittlung des Einkommens "
            "außer Ansatz bleiben, gelten 5 Prozent als Ausgaben, die nicht als Betriebsausgaben "
            "abgezogen werden dürfen. [...] wenn die Beteiligung zu Beginn des Kalenderjahres "
            "unmittelbar weniger als 10 Prozent [...] betragen hat"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=10, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=95,
        notes="§8b KStG: 95% exempt (10% at the start of the year for dividends; gains at any "
        "holding); trade tax adds back dividends below 15% (§8 Nr. 5 GewStG) — not modelled",
    )

    # France–Germany 1959 convention as amended and modified by the MLI (from 1 Jan 2025).
    t = sd.treaty(fr, de, name="Convention between France and Germany (1959, as amended)",
                  signed=date(1959, 7, 21), in_force=date(1961, 6, 4), src=Src(
                      "Convention France–Allemagne, version consolidée (impots.gouv.fr)", FR_DE,
                      None, "Convention entre la République française et la République fédérale "
                      "d'Allemagne [...] modifiée par la convention multilatérale"))
    start = date(2025, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 9", start, Src(
        "Convention France–Allemagne, version consolidée (impots.gouv.fr)", FR_DE, "Article 9(2)",
        "ce prélèvement ne peut excéder 15 p. 100 du montant brut des dividendes."), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 9", start, Src(
        "Convention France–Allemagne, version consolidée (impots.gouv.fr)", FR_DE, "Article 9(5)",
        "détient au moins 10 p. 100 du capital [...] tout au long d'une période de 365 jours "
        "incluant le jour du paiement [...] l'impôt prélevé à la source dans la République "
        "fédérale ne peut excéder [...] 5 p. 100 du montant brut des dividendes"),
        max_rate="5", ownership_threshold="10", min_holding_days=365, source=de)
    sd.treaty_rate(t, "DIVIDEND", "Article 9", start, Src(
        "Convention France–Allemagne, version consolidée (impots.gouv.fr)", FR_DE, "Article 9(3)",
        "qui détient au moins 10 % du capital social tout au long d'une période de 365 jours "
        "[...] ne peuvent pas être imposés en France"),
        exclusive=True, ownership_threshold="10", min_holding_days=365, source=fr)
    sd.treaty_rate(t, "INTEREST", "Article 10", start, Src(
        "Convention France–Allemagne, version consolidée (impots.gouv.fr)", FR_DE,
        "Article 10(1)",
        "Les intérêts et autres produits [...] ne sont imposables que dans l'État contractant "
        "dont le bénéficiaire est le résident."), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 15", start, Src(
        "Convention France–Allemagne, version consolidée (impots.gouv.fr)", FR_DE,
        "Article 15(1)",
        "Les redevances [...] ne sont imposables que dans l'État contractant dont le "
        "bénéficiaire est le résident."), exclusive=True)
    sd.ppt(t, start, Src(
        "Convention France–Allemagne, version consolidée (impots.gouv.fr)", FR_DE,
        "MLI art. 7(1)",
        "un avantage au titre de celle-ci ne sera pas accordé [...] s'il est raisonnable de "
        "conclure [...] que l'octroi de cet avantage était l'un des objets principaux d'un "
        "montage ou d'une transaction"), dividend_min_holding_days=365)
    # No Germany–UAE treaty: the 2010 treaty applied 2009-2021 only (BMF, Stand DBA 1.1.2026).


def _ireland(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, ie: Jurisdiction, eu: JurisdictionGroup
) -> None:
    rates = Src(
        "Corporation Tax — basis of charge (Revenue)",
        REV + "companies-and-charities/corporation-tax-for-companies/corporation-tax/"
        "basis-of-charge.aspx",
        "s.21 / s.21A TCA 1997",
        "12.5% for trading income [...] 25% for: income from an excepted trade [...] [and] non "
        "trading income, for example rental and investment income.")
    sd.cit(ie, date(2026, 1, 1), rates, rate="12.5")
    passive = Src(
        "Tax and Duty Manual 02-02-06 — trading or passive IP income (Revenue)",
        REV_TDM + "part-02/02-02-06.pdf", "s.21A TCA 1997",
        "a company whose only activity is the licensing of the rights to intellectual property, "
        "and the on-licensing of such rights, is unlikely to be regarded as trading")
    # A holding company receiving royalties/interest is treated as passive (25%); an IP company
    # with real R&D and licensing activity can be trading (12.5%) — case by case.
    sd.cit(ie, date(2026, 1, 1), passive, rate="25", category="ROYALTY")
    sd.cit(ie, date(2026, 1, 1), rates, rate="25", category="INTEREST")
    sd.wht(ie, "DIVIDEND", "25", date(2026, 1, 1), Src(
        "Dividend Withholding Tax (Revenue)",
        REV + "companies-and-charities/dividend-withholding-tax/index.aspx", "s.172A TCA",
        "They must withhold Dividend Withholding Tax (DWT) at 25% for the year in which the "
        "distribution is made."))
    sd.wht(ie, "INTEREST", "20", date(2026, 1, 1), Src(
        "Tax and Duty Manual 08-03-06 — interest (Revenue)", REV_TDM + "part-08/08-03-06.pdf",
        "s.246(2) TCA",
        "section 246 [...] requires the deduction of income tax at the standard rate from yearly "
        "interest (standard rate 20%)"))
    sd.wht(ie, "ROYALTY", "20", date(2026, 1, 1), Src(
        "Tax and Duty Manual 08-01-04 — patent royalties (Revenue)",
        REV_TDM + "part-08/08-01-04.pdf", "s.238(2) TCA",
        "the payer is obliged to deduct out of the payment a sum representing the amount of "
        "income tax on the payment at the standard rate (20%)"))
    sd.exemption(
        ie, "DIVIDEND", eu, date(2026, 1, 1),
        Src("DWT exemptions for non-residents (Revenue)",
            REV + "companies-and-charities/dividend-withholding-tax/"
            "exemptions-for-non-residents.aspx", "s.172D TCA",
            "Companies resident in a relevant territory which are neither directly nor "
            "indirectly controlled by an Irish resident person."),
        min_holding_pct=None, min_holding_months=None, legal_ref="s.172D TCA",
        description="Company resident in an EU/EEA or treaty state, not controlled by Irish "
        "residents (form V2B declaration)",
    )
    sd.exemption(
        ie, "INTEREST", eu, date(2026, 1, 1),
        Src("Tax and Duty Manual 08-03-06 — interest (Revenue)",
            REV_TDM + "part-08/08-03-06.pdf", "s.246(3)(h) TCA",
            "the interest is paid to a company that is resident for tax purposes in a relevant "
            "territory, and the tax regime in the relevant territory is one that imposes a tax "
            "that generally applies to interest receivable in that territory by companies from "
            "sources outside that territory."),
        min_holding_pct=None, min_holding_months=None, legal_ref="s.246(3)(h) TCA",
        description="Interest to a company in an EU or treaty state that taxes foreign interest",
    )
    sd.regime(
        ie, date(2025, 1, 1),
        Src("Tax and Duty Manual 35-02-11 — participation exemption (Revenue)",
            REV_TDM + "part-35/35-02-11.pdf", "s.831B TCA",
            "The participation exemption in section 831B was introduced by Finance Act 2024 and "
            "applies to a 'relevant distribution' made on or after 1 January 2025 [...] The "
            "qualifying participation must be held continuously for a minimum 12-month period"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=5, min_holding_period_months=12, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="s.831B (dividends, elective, payer in EEA/treaty state) and s.626B (gains, "
        "trading-group test): ≥5% for 12 months",
    )
    sd.cfc(
        ie, date(2019, 1, 1),
        Src("Tax and Duty Manual 35B-01-01 — CFC rules (Revenue)",
            REV_TDM + "part-35b/35b-01-01.pdf", "Part 35B TCA (s.835T)",
            "direct or indirect ownership of, or entitlement to, more than 50% of the CFC's "
            "issued share capital [...] is less than half the tax that would have been paid had "
            "the income been taxed on the basis that the CFC was resident in the State"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="Part 35B TCA",
        effect="Undistributed income from non-genuine arrangements with significant people "
        "functions in Ireland is charged.",
    )

    t = sd.treaty(fr, ie, name="Convention between France and Ireland (1968)",
                  signed=date(1968, 3, 21), in_force=date(1971, 6, 15), src=Src(
                      "Convention France–Irlande (impots.gouv.fr)",
                      "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/"
                      "irlande/irlande_convention-avec-l-irlande_fd_1806.pdf", None,
                      "signée à Paris le 21 mars 1968 [...] entrée en vigueur le 15 juin 1971"))
    start = date(1971, 6, 15)
    sd.treaty_rate(t, "DIVIDEND", "Article 9", start, Src(
        "Convention France–Ireland (Revenue)", FR_IE, "Article 9",
        "the rate shall not exceed 15 per cent (French tax on dividends to Irish residents)"),
        max_rate="15", source=fr)
    sd.treaty_rate(t, "DIVIDEND", "Article 9", start, Src(
        "Convention France–Ireland (Revenue)", FR_IE, "Article 9",
        "the rate shall not exceed 10 per cent on dividends distributed by a company being a "
        "resident of France to a company being a resident of Ireland which has held for a year "
        "[...] at least 50 per cent of the capital"),
        max_rate="10", ownership_threshold="50", min_holding_days=365, source=fr)
    sd.treaty_rate(t, "INTEREST", "Article 10", start, Src(
        "Convention France–Ireland (Revenue)", FR_IE, "Article 10",
        "Interest arising in a Contracting State and paid to a resident of the other Contracting "
        "State shall be taxable only in that other State."), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 11", start, Src(
        "Convention France–Ireland (Revenue)", FR_IE, "Article 11",
        "Royalties arising in a Contracting State and paid to a resident of the other "
        "Contracting State shall be taxable only in that other State."), exclusive=True)
    sd.ppt(t, date(2020, 1, 1), Src(
        "Ireland–France synthesised text with the MLI (Revenue)", FR_IE_MLI, "MLI art. 7(1)",
        "The following paragraph 1 of Article 7 of the MLI applies and supersedes the provisions "
        "of this Convention"))

    t = sd.treaty(ie, ae, name="Convention between Ireland and the United Arab Emirates",
                  signed=date(2010, 7, 1), in_force=date(2011, 7, 21), src=Src(
                      "Irish Treaty Series No. 16 of 2012 (gov.ie)",
                      "https://www.gov.ie/en/irish-treaty-series/treaty-series/"
                      "convention-between-ireland-and-the-united-arab-emirates-for-the-avoidance-"
                      "of-double-taxation-and-the-prevention-of-fiscal-evasion-with-respect-to-"
                      "taxes-on-income-and-capital-gains-done-at-dubai-on-1-july-2010",
                      None, "Entered into force: 21 July 2011"))
    for cat, art in (("DIVIDEND", "Article 11"), ("INTEREST", "Article 12"),
                     ("ROYALTY", "Article 13")):
        sd.treaty_rate(t, cat, art, date(2011, 7, 21), Src(
            "Convention Ireland–UAE (Revenue)", IE_AE, f"{art}(1)",
            "shall be taxable only in that other State, provided such resident is the "
            "beneficial owner"), exclusive=True)
    sd.ppt(t, date(2020, 1, 1), Src(
        "Ireland–UAE synthesised text with the MLI (Revenue)", IE_AE_MLI, "MLI art. 7(1)",
        "The following paragraph 1 of Article 7 of the MLI applies and supersedes the provisions "
        "of this Convention"))


def _malta(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, mt: Jurisdiction) -> None:
    sd.cit(mt, date(2026, 1, 1), Src(
        "Income Tax Act Cap. 123 (legislation.mt, consolidated 2026-03-10)", MT_ITA,
        "Cap. 123 art. 56(6)",
        "The tax shall be charged at the rate of thirty-five cents (0.35) on every euro of the "
        "chargeable income of every - (a) company"), rate="35")
    refund_src = Src(
        "Income Tax Management Act Cap. 372 (legislation.mt, consolidated 2026-03-10)", MT_ITMA,
        "Cap. 372 art. 48(4A)(a)",
        "may claim a refund of six-sevenths of the Advance Company Income Tax pertaining to "
        "those profits [...] consisting of passive interest or royalties [...] the rate of "
        "refund shall be of five-sevenths")
    for cat in ("ROYALTY", "INTEREST"):
        sd.refund(
            mt, cat, "71.4286", date(2026, 1, 1), refund_src, legal_ref="Cap. 372 art. 48(4A)",
            description="5/7 of the Malta tax refunded to the shareholder for passive "
            "interest/royalties (6/7 if not passive; 2/3 if double tax relief is claimed)",
        )
    sd.wht(mt, "DIVIDEND", "0", date(2026, 1, 1), Src(
        "Malta withholding taxes (PwC Worldwide Tax Summaries — secondary source)",
        "https://taxsummaries.pwc.com/malta/corporate/withholding-taxes", None,
        "No WHT is imposed on dividends distributed by Maltese companies (except for "
        "distributions of untaxed income to resident persons other than companies)"))
    nonres = Src(
        "Income Tax Act Cap. 123 (legislation.mt, consolidated 2026-03-10)", MT_ITA,
        "Cap. 123 art. 12(1)(c)(i)",
        "any interest, discount, premium or royalties accruing to or derived by any person not "
        "resident in Malta")
    sd.wht(mt, "INTEREST", "0", date(2026, 1, 1), nonres)
    sd.wht(mt, "ROYALTY", "0", date(2026, 1, 1), nonres)
    sd.regime(
        mt, date(2026, 1, 1),
        Src("Income Tax Act Cap. 123 (legislation.mt)", MT_ITA, "Cap. 123 art. 2, 12(1)(u)",
            "a company holds directly at least five percent of the equity shares of a company "
            "[...] (1) it is resident or incorporated in a country or territory which forms "
            "part of the European Union; (2) it is subject to any foreign tax of at least "
            "fifteen per cent (15%)"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=5, min_holding_period_months=None, subject_to_tax_condition=True,
        min_subject_to_tax_rate=15, exempt_share_pct=100,
        notes="Participating holding ≥5% (or alternatives); dividends need an EU payer, foreign "
        "tax ≥15% or ≤50% passive income (modelled as the 15% test)",
    )
    sd.cfc(
        mt, date(2019, 1, 1),
        Src("ATAD Implementation Regulations S.L. 123.187 (legislation.mt)",
            "https://legislation.mt/eli/sl/123.187/eng", "S.L. 123.187 reg. 7",
            "holds a direct or indirect participation of more than fifty per cent (50%) of the "
            "voting rights [...] the actual corporate tax paid on its profits by the entity [...] "
            "is lower than the difference between the tax that would have been charged [...] "
            "and the actual corporate tax paid"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="S.L. 123.187",
        effect="Undistributed income from non-genuine arrangements is included.",
    )

    # France–Malta 1977 as amended; the original entry-into-force date is not verified, so the
    # treaty is recorded from the 2008 avenant's entry into force (1 June 2010).
    t = sd.treaty(fr, mt, name="Convention between France and Malta (1977, as amended 2008)",
                  signed=date(1977, 7, 25), in_force=date(2010, 6, 1), src=Src(
                      "Accord France–Malte modifié par la CML (impots.gouv.fr)", FR_MT_MLI, None,
                      "signé à La Valette le 25 juillet 1977 [...] par l'Avenant signé à La "
                      "Valette le 29 août 2008, [...] entré en vigueur le 1er juin 2010"))
    start = date(2010, 6, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Accord franco-maltais, version consolidée (impots.gouv.fr)", FR_MT, "Article 10(2)",
        "l'impôt français ainsi établi ne peut excéder 15 % du montant brut des dividendes."),
        max_rate="15", source=fr)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Accord franco-maltais, version consolidée (impots.gouv.fr)", FR_MT, "Article 10(2)",
        "les dividendes [...] dont le bénéficiaire effectif est une société qui est un résident "
        "de Malte et qui détient directement au moins 10 % du capital [...] ne sont imposables "
        "qu'à Malte"), exclusive=True, ownership_threshold="10", source=fr)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Accord franco-maltais, version consolidée (impots.gouv.fr)", FR_MT, "Article 11(2)",
        "l'impôt ainsi établi ne peut excéder 5 p. cent du montant brut des intérêts"),
        max_rate="5")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Accord franco-maltais, version consolidée (impots.gouv.fr)", FR_MT, "Article 12(2)",
        "l'impôt ainsi établi ne peut excéder 10 p. cent du montant brut des redevances"),
        max_rate="10")
    sd.ppt(t, date(2020, 1, 1), Src(
        "Accord France–Malte modifié par la CML (impots.gouv.fr)", FR_MT_MLI, "MLI art. 7(1)",
        "un avantage au titre de celui-ci ne sera pas accordé [...] s'il est raisonnable de "
        "conclure [...] que l'octroi de cet avantage était l'un des objets principaux d'un "
        "montage"))

    t = sd.treaty(mt, ae, name="Convention between Malta and the United Arab Emirates",
                  signed=date(2006, 3, 13), in_force=date(2007, 5, 18), src=Src(
                      "Double Taxation Relief (UAE) Order, S.L. 123.106 (legislation.mt)", MT_AE,
                      None, "that the Convention has entered into force on the 18 May, 2007."))
    for cat, art in (("DIVIDEND", "Article 10"), ("INTEREST", "Article 11"),
                     ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, date(2008, 1, 1), Src(
            "Convention Malta–UAE, S.L. 123.106 (legislation.mt)", MT_AE, f"{art}(1)",
            "shall be taxable only in that other State."), exclusive=True)
    sd.ppt(t, date(2020, 1, 1), Src(
        "Multilateral Convention (BEPS) Order, S.L. 123.183 — UAE listed (legislation.mt)",
        MT_MLI, "MLI art. 7(1)",
        "Schedule 2, listed agreement no. 70: United Arab Emirates (principal purpose test)"))


def _belgium(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, be: Jurisdiction, eu: JurisdictionGroup
) -> None:
    sd.cit(be, date(2020, 1, 1), Src(
        "Loi du 25 décembre 2017 portant réforme de l'impôt des sociétés (Moniteur belge)",
        BE_2017, "CIR 92 art. 215",
        "Art. 215. Le taux de l'impôt des sociétés est fixé à 29 p.c. [...] les mots \"29 p.c.\" "
        "sont remplacés par les mots \"25 p.c.\""), rate="25")
    wht = Src(
        "Loi-programme du 25 décembre 2016, art. 94-95 (Moniteur belge)", BE_2016,
        "CIR 92 art. 269 §1, 1°",
        "A l'article 269, § 1er [...] 1° dans le 1°, les mots \"27 %\" sont remplacés par les "
        "mots \"30 %\" [...] applicables aux revenus payés ou attribués à partir du 1er janvier "
        "2017.")
    for cat in ("DIVIDEND", "INTEREST", "ROYALTY"):
        sd.wht(be, cat, "30", date(2017, 1, 1), wht)
    sd.exemption(
        be, "DIVIDEND", eu, date(2017, 1, 1),
        Src("Belgium withholding taxes (PwC Worldwide Tax Summaries — secondary source)",
            "https://taxsummaries.pwc.com/belgium/corporate/withholding-taxes",
            "AR/CIR 92 art. 106 §6",
            "WHT exemption is foreseen for the distribution of profits made by a Belgian "
            "subsidiary to an EU parent company [...] at least 10% in the capital [...] "
            "uninterrupted one-year period"),
        min_holding_pct="10", min_holding_months=12, legal_ref="AR/CIR 92 art. 106 §6",
        description="Parent-Subsidiary Directive: EU parent holding ≥10% for 1 year "
        "(official text not retrieved — secondary source)",
    )
    ird = Src(
        "Arrêté royal du 22 décembre 2003 (Moniteur belge)", BE_IRD,
        "AR/CIR 92 art. 105, 6°; 107 §6; 117 §6bis",
        "\"sociétés associées\", deux sociétés établies dans l'Union européenne [...] : - soit "
        "qu'une des deux sociétés détient une participation directe ou indirecte d'au moins 25 "
        "p.c. dans le capital de l'autre pendant une période ininterrompue d'au moins un an")
    for cat in ("INTEREST", "ROYALTY"):
        sd.exemption(
            be, cat, eu, date(2004, 1, 1), ird, min_holding_pct="25", min_holding_months=12,
            legal_ref="AR/CIR 92 art. 107 §6",
            description="Interest and Royalties Directive: associated EU company (≥25%, 1 year)",
        )
    sd.regime(
        be, date(2018, 1, 1),
        Src("Loi du 24 décembre 2002 (RDT/DBI) and loi du 25 décembre 2017 (Moniteur belge)",
            BE_2002, "CIR 92 art. 202-204",
            "une participation de 10 p.c. au moins [...] détenues en pleine propriété pendant "
            "une période ininterrompue d'au moins un an [...] taux nominal de droit commun de "
            "l'impôt sur les bénéfices de la société est inférieur à 15 p.c."),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=10, min_holding_period_months=12, subject_to_tax_condition=True,
        min_subject_to_tax_rate=15, exempt_share_pct=100,
        notes="RDT/DBI 100% (art. 204, from AY 2019): ≥10% or ≥ EUR 2.5m (financial fixed "
        "assets for non-small companies from AY 2026), 1 year; EU payers deemed not low-taxed",
    )
    sd.cfc(
        be, date(2023, 1, 1),
        Src("Loi-programme du 22 décembre 2023, art. 22 (Moniteur belge)", BE_CFC,
            "CIR 92 art. 185/2",
            "soit n'y est pas soumise à un impôt sur les revenus, soit est assujettie à un "
            "impôt sur les revenus qui s'élève à moins de la moitié de l'impôt des sociétés qui "
            "serait dû si cette société étrangère [...] était établie [...] en Belgique."),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="CIR 92 art. 185/2",
        effect="Tainted income of a controlled foreign company taxed below half the Belgian "
        "CIT is included (substance and one-third exemptions apply).",
    )

    # France–Belgium: the 1964 convention (as amended, modified by the MLI) is in force; the
    # 2021 convention has not been ratified (Sénat question of 21 May 2026).
    t = sd.treaty(fr, be, name="Convention between France and Belgium (1964, as amended)",
                  signed=date(1964, 3, 10), in_force=date(1965, 6, 17), src=Src(
                      "Convention France–Belgique, version consolidée (impots.gouv.fr)", FR_BE,
                      None, "Convention entre la France et la Belgique du 10 mars 1964 [...] "
                      "la CML est entrée en vigueur le 1er janvier 2019 pour la France et le "
                      "1er octobre 2019 pour la Belgique"))
    start = date(2020, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 15", start, Src(
        "Convention France–Belgique, version consolidée (impots.gouv.fr)", FR_BE,
        "Article 15(2)(b)", "b) 15 p. cent du montant brut des dividendes dans les autres cas."),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 15", start, Src(
        "Convention France–Belgique, version consolidée (impots.gouv.fr)", FR_BE,
        "Article 15(2)(a); MLI art. 8",
        "a) 10 p. cent du montant brut des dividendes si le bénéficiaire est une société qui a "
        "la propriété exclusive d'au moins 10 p. cent du capital [...] tout au long d'une "
        "période de 365 jours"), max_rate="10", ownership_threshold="10", min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 16", start, Src(
        "Convention France–Belgique, version consolidée (impots.gouv.fr)", FR_BE,
        "Article 16(3)",
        "L'Etat contractant où les intérêts et produits ont leur source conserve le droit de "
        "soumettre ces intérêts et produits à un impôt prélevé à la source, dont le taux ne "
        "peut excéder 15 p. cent."), max_rate="15")
    sd.treaty_rate(t, "ROYALTY", "Article 8", start, Src(
        "Convention France–Belgique, version consolidée (impots.gouv.fr)", FR_BE, "Article 8(1)",
        "Les redevances [...] ne sont imposables que dans l'Etat contractant dont le "
        "bénéficiaire est un résident."), exclusive=True)
    sd.ppt(t, start, Src(
        "Convention France–Belgique, version consolidée (impots.gouv.fr)", FR_BE,
        "MLI art. 7(1)",
        "un avantage au titre de celle-ci ne sera pas accordé [...] s'il est raisonnable de "
        "conclure [...] que l'octroi de cet avantage était l'un des objets principaux"),
        dividend_min_holding_days=365)

    t = sd.treaty(be, ae, name="Convention between Belgium and the United Arab Emirates",
                  signed=date(1996, 9, 30), in_force=date(2004, 1, 6), src=Src(
                      "Loi d'assentiment du 2 août 2002 (Moniteur belge 24.12.2003)", BE_AE,
                      "Article 28",
                      "Conformément à son article 28, cette Convention entre en vigueur le 6 "
                      "janvier 2004."))
    start = date(2004, 1, 6)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention Belgium–UAE (Moniteur belge)", BE_AE, "Article 10(2)(b)",
        "b) 10 per cent of the gross amount of the dividends in all other cases."),
        max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention Belgium–UAE (Moniteur belge)", BE_AE, "Article 10(2)(a)",
        "a) 5 per cent of the gross amount of the dividends if the beneficial owner is a "
        "company which holds directly or indirectly at least 25 per cent of the capital"),
        max_rate="5", ownership_threshold="25")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            "Convention Belgium–UAE (Moniteur belge)", BE_AE, f"{art}(2)",
            f"the tax so charged shall not exceed 5 per cent of the gross amount of the "
            f"{'interest' if cat == 'INTEREST' else 'royalties'}."), max_rate="5")
    sd.ppt(t, date(2020, 1, 1), Src(
        "MLI position of Belgium — instrument of deposit (OECD)",
        "https://www.oecd.org/tax/treaties/beps-mli-position-belgium-instrument-deposit.pdf",
        "MLI art. 7(1)", "United Arab Emirates [...] Original 30-09-1996 06-01-2004 "
        "(covered tax agreement; no reservation on article 7)"))
