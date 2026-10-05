"""P8 batch 3: United Kingdom, Spain, Singapore, Switzerland.

Figures were sourced on 2026-10-05 from the official texts cited on each `Src` and are stored
as `unreviewed` until a named reviewer confirms them (spec §10). Research notes:
docs/superpowers/plans/2026-10-05-p8-batch3.md.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import JurisdictionGroup
from app.modules.seed.builder import Seeder, Src

GOV = "https://www.gov.uk/government/publications/"
LEG = "https://www.legislation.gov.uk/ukpga/"
FR_GB = GOV + "france-tax-treaties/2008-uk-and-france-double-taxation-convention-in-force"
GB_AE = GOV + "united-arab-emirates-tax-treaties/2016-uk-uae-double-taxation-convention"
ES_LIS = "https://www.boe.es/buscar/act.php?id=BOE-A-2014-12328"
ES_IRNR = "https://www.boe.es/buscar/act.php?id=BOE-A-2004-4527"
FR_ES = (
    "https://www.hacienda.gob.es/sgt/normativadoctrina/tributaria/cdi/textos-sinteticos/"
    "cdi-ts-francia-sp.pdf"
)
ES_AE = (
    "https://www.hacienda.gob.es/SGT/NormativaDoctrina/Tributaria/CDI/Textos-Sinteticos/"
    "CDI-TS-EAU-SP.pdf"
)
IRAS = "https://www.iras.gov.sg/"
SSO = "https://sso.agc.gov.sg/Act/ITA1947?ProvIds="
FR_SG = (
    IRAS + "media/docs/default-source/dtas/singapore-france-dta-(ratified)(mli)(19-jul-2021).pdf"
)
SG_AE = (
    IRAS + "media/docs/default-source/dtas/"
    "singapore-united-arab-emirates-dta-(ratified)(mli)(2-sep-2019).pdf"
)
FEDLEX = "https://www.fedlex.admin.ch/eli/cc/"
CH_DBG = FEDLEX + "1991/1184_1184_1184/de"
CH_VSTG = FEDLEX + "1966/371_385_384/de"
CH_ZG = (
    "https://cdn.zg.ch/dam/jcr:1992b85c-2c8c-4427-b2b7-0d41ba460da6/"
    "Steuerbelastungen%202023%20-%202026.pdf"
)
FR_CH = FEDLEX + "1967/1079_1119_1113/fr"
CH_EU = FEDLEX + "2005/444/de"
CH_AE = FEDLEX + "2012/736/de"


def seed_batch3(session: Session) -> None:
    sd = Seeder(session)
    fr = sd.jurisdiction("FR", "France")
    ae = sd.jurisdiction("AE", "United Arab Emirates")
    eu = sd.group("EU", "European Union member states")
    _united_kingdom(sd, fr, ae, sd.jurisdiction("GB", "United Kingdom"))
    es = sd.jurisdiction("ES", "Spain")
    sd.member(eu, es, date(1986, 1, 1), Src(
        "Spain — EU member country profile (european-union.europa.eu)",
        "https://european-union.europa.eu/principles-countries-history/eu-countries/spain_en",
        None, "since 1 January 1986"))
    _spain(sd, fr, ae, es, eu)
    _singapore(sd, fr, ae, sd.jurisdiction("SG", "Singapore"))
    _switzerland(sd, fr, ae, sd.jurisdiction("CH", "Switzerland"), eu)


def _united_kingdom(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, gb: Jurisdiction) -> None:
    # Small profits rate 19% to £50k, main rate 25% above £250k, marginal relief (3/200) in
    # between — equivalent to a 26.5% marginal band from £50k to £250k.
    sd.cit(gb, date(2023, 4, 1), Src(
        "Rates and allowances: Corporation Tax (gov.uk)",
        GOV + "rates-and-allowances-corporation-tax/rates-and-allowances-corporation-tax",
        "CTA 2010",
        "Small profits rate (companies with profits under £50,000) 19% [...] Main rate "
        "(companies with profits over £250,000) 25% [...] marginal relief fraction 3/200 "
        "(band £50,000-£250,000 modelled as 26.5% marginal)",
    ), brackets=[("0", "50000", "19"), ("50000", "250000", "26.5"), ("250000", None, "25")])
    sd.wht(gb, "DIVIDEND", "0", date(2026, 4, 6), Src(
        "United Kingdom withholding taxes (PwC Worldwide Tax Summaries — secondary source)",
        "https://taxsummaries.pwc.com/united-kingdom/corporate/withholding-taxes", None,
        "There is generally no requirement to deduct WHT from dividends."))
    sd.wht(gb, "INTEREST", "20", date(2026, 4, 6), Src(
        "Income Tax Act 2007 s.874 (legislation.gov.uk); Income Tax rates (gov.uk)",
        LEG + "2007/3/section/874", "ITA 2007 s.874",
        "must, on making the payment, deduct from it a sum representing income tax on it at the "
        "savings basic rate in force for the tax year in which it is made. (2026-27: 20%)"))
    sd.wht(gb, "ROYALTY", "20", date(2026, 4, 6), Src(
        "Income Tax Act 2007 s.903/906 (legislation.gov.uk)", LEG + "2007/3/section/906",
        "ITA 2007 s.903, s.906",
        "deduct from it a sum representing income tax on it at the basic rate in force for the "
        "tax year."))
    sd.regime(
        gb, date(2009, 7, 1),
        Src("Corporation Tax Act 2009 Part 9A (legislation.gov.uk)",
            LEG + "2009/4/part/9A/chapter/3", "CTA 2009 s.931D-931I; TCGA 1992 Sch 7AC",
            "exempt classes: controlled companies (s.931E), non-redeemable ordinary shares "
            "(s.931F), portfolio holdings (s.931G) [...] substantial shareholding [...] "
            "throughout a twelve-month period"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Dividend exemption (CTA 2009 Part 9A) for most distributions; gains via SSE "
        "(≥10% for 12 months within 6 years)",
    )
    sd.cfc(
        gb, date(2013, 1, 1),
        Src("TIOPA 2010 s.371NB (legislation.gov.uk)", LEG + "2010/8/section/371NB",
            "TIOPA 2010 Part 9A",
            "The tax exemption applies if the local tax amount is at least 75% of the "
            "corresponding UK tax."),
        control_threshold_pct=50, low_tax_relative_pct=75, legal_ref="TIOPA 2010 Part 9A",
        effect="Chargeable profits of a UK-controlled foreign company paying less than 75% of "
        "the corresponding UK tax are apportioned (gateway and exemptions apply).",
    )

    t = sd.treaty(fr, gb, name="Convention between France and the United Kingdom (2008)",
                  signed=date(2008, 6, 19), in_force=date(2009, 12, 18), src=Src(
                      "France: tax treaties (gov.uk)", GOV + "france-tax-treaties", None,
                      "Signed 19 June 2008 [...] entered into force 18 December 2009"))
    start = date(2010, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 11", start, Src(
        "2008 UK and France double taxation convention (gov.uk)", FR_GB, "Article 11(1)(b)",
        "the tax so charged shall not exceed 15 per cent of the gross amount of the dividends."),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 11", start, Src(
        "2008 UK and France double taxation convention (gov.uk)", FR_GB, "Article 11(1)(c)",
        "shall not be taxable in that State if the beneficial owner is a company liable to "
        "Corporation Tax which holds, directly or indirectly, at least 10 per cent of the "
        "capital in the company paying the dividends"), exclusive=True, ownership_threshold="10")
    for cat, art in (("INTEREST", "Article 12"), ("ROYALTY", "Article 13")):
        sd.treaty_rate(t, cat, art, start, Src(
            "2008 UK and France double taxation convention (gov.uk)", FR_GB, f"{art}(1)",
            "beneficially owned by a resident of the other Contracting State shall be taxable "
            "only in that other State."), exclusive=True)
    sd.ppt(t, date(2019, 1, 1), Src(
        "Synthesised text of the MLI and the 2008 UK-France convention (gov.uk)",
        GOV + "france-tax-treaties", "MLI art. 7(1)",
        "a benefit under [this Convention] shall not be granted [...] if it is reasonable to "
        "conclude [...] that obtaining that benefit was one of the principal purposes"))

    t = sd.treaty(gb, ae, name="Convention between the United Kingdom and the UAE (2016)",
                  signed=date(2016, 4, 12), in_force=date(2016, 12, 25), src=Src(
                      "United Arab Emirates: tax treaties (gov.uk)",
                      GOV + "united-arab-emirates-tax-treaties", None,
                      "signed 12 April 2016 [...] entered into force 25 December 2016"))
    start = date(2017, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "2016 UK-UAE double taxation convention (gov.uk)", GB_AE, "Article 10(2)(a)",
        "such dividends shall be exempt from tax in the Contracting State of which the company "
        "paying the dividends is a resident"), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "2016 UK-UAE double taxation convention (gov.uk)", GB_AE, "Article 12(1)",
        "Royalties arising in a Contracting State and beneficially owned by a resident of the "
        "other Contracting State shall be taxable only in that other State."), exclusive=True)
    # Interest (art. 11) is exempt only for listed recipients (state bodies, listed companies,
    # pension schemes, unrelated banks, cleared companies) — no general cap is recorded.
    sd.ppt(t, date(2020, 1, 1), Src(
        "United Arab Emirates: tax treaties — MLI dates (gov.uk)",
        GOV + "united-arab-emirates-tax-treaties", "MLI art. 7(1)",
        "The convention is modified by the MLI: withholding taxes from 1 January 2020"))


def _spain(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, es: Jurisdiction, eu: JurisdictionGroup
) -> None:
    sd.cit(es, date(2025, 1, 1), Src(
        "Ley 27/2014 del Impuesto sobre Sociedades, art. 29 (BOE)", ES_LIS, "LIS art. 29.1",
        "El tipo general de gravamen para los contribuyentes de este Impuesto será el 25 por "
        "ciento"), rate="25")
    divint = Src(
        "TRLIRNR (RDLeg 5/2004), art. 25 (BOE)", ES_IRNR, "TRLIRNR art. 25.1.f)",
        "f) El 19 por ciento cuando se trate de: 1.º Dividendos y otros rendimientos derivados "
        "de la participación en los fondos propios de una entidad. 2.º Intereses")
    sd.wht(es, "DIVIDEND", "19", date(2015, 1, 1), divint)
    sd.wht(es, "INTEREST", "19", date(2015, 1, 1), divint)
    roy = Src(
        "TRLIRNR (RDLeg 5/2004), art. 25 (BOE)", ES_IRNR, "TRLIRNR art. 25.1.a)",
        "a) Con carácter general el 24 por 100. No obstante, el tipo de gravamen será el 19 por "
        "ciento cuando se trate de contribuyentes residentes en otro Estado miembro de la Unión "
        "Europea")
    sd.wht(es, "ROYALTY", "24", date(2015, 1, 1), roy)
    sd.exemption(es, "ROYALTY", eu, date(2015, 1, 1), roy, min_holding_pct=None,
                 min_holding_months=None, legal_ref="TRLIRNR art. 25.1.a)",
                 description="royalties to EU residents taxed at 19%", reduced_rate="19")
    sd.exemption(
        es, "ROYALTY", eu, date(2015, 1, 1),
        Src("TRLIRNR (RDLeg 5/2004), art. 14.1.m) (BOE)", ES_IRNR, "TRLIRNR art. 14.1.m)",
            "dos sociedades se considerarán asociadas cuando una posea en el capital de la otra "
            "una participación directa de, al menos, el 25 por ciento [...] durante el año "
            "anterior al día en que se haya satisfecho el pago"),
        min_holding_pct="25", min_holding_months=12, legal_ref="TRLIRNR art. 14.1.m)",
        description="Interest and Royalties Directive: associated EU company (≥25%, 1 year)",
    )
    sd.exemption(
        es, "DIVIDEND", eu, date(2015, 1, 1),
        Src("TRLIRNR (RDLeg 5/2004), art. 14.1.h) (BOE)", ES_IRNR, "TRLIRNR art. 14.1.h)",
            "Tendrá la consideración de sociedad matriz aquella entidad que posea en el capital "
            "de otra sociedad una participación directa o indirecta de, al menos, el 5 por "
            "ciento [...] de forma ininterrumpida durante el año anterior"),
        min_holding_pct="5", min_holding_months=12, legal_ref="TRLIRNR art. 14.1.h)",
        description="Parent-Subsidiary Directive: EU parent ≥5% for 1 year (not majority "
        "controlled from outside the EU/EEA without valid reasons)",
    )
    sd.exemption(
        es, "INTEREST", eu, date(2015, 1, 1),
        Src("TRLIRNR (RDLeg 5/2004), art. 14.1.c) (BOE)", ES_IRNR, "TRLIRNR art. 14.1.c)",
            "c) Los intereses y demás rendimientos obtenidos por la cesión a terceros de "
            "capitales propios [...] por residentes en otro Estado miembro de la Unión Europea"),
        min_holding_pct=None, min_holding_months=None, legal_ref="TRLIRNR art. 14.1.c)",
        description="interest to EU residents exempt",
    )
    sd.regime(
        es, date(2021, 1, 1),
        Src("Ley 27/2014, art. 21 (BOE)", ES_LIS, "LIS art. 21",
            "a) Que el porcentaje de participación [...] sea, al menos, del 5 por ciento [...] "
            "sujeta y no exenta por un impuesto extranjero [...] a un tipo nominal de, al menos, "
            "el 10 por ciento [...] se reducirá [...] en un 5 por ciento en concepto de gastos "
            "de gestión"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=5, min_holding_period_months=12, subject_to_tax_condition=True,
        min_subject_to_tax_rate=10, exempt_share_pct=95,
        notes="LIS art. 21: ≥5% for 1 year, foreign nominal tax ≥10% (deemed met under a treaty "
        "with exchange of information), 95% exempt",
    )
    sd.cfc(
        es, date(2021, 1, 1),
        Src("Ley 27/2014, art. 100 (BOE)", ES_LIS, "LIS art. 100",
            "tengan una participación igual o superior al 50 por ciento [...] Que el importe "
            "satisfecho por la entidad no residente [...] sea inferior al 75 por ciento del que "
            "hubiera correspondido de acuerdo con las normas de aquel."),
        control_threshold_pct=50, low_tax_relative_pct=75, legal_ref="LIS art. 100",
        effect="Income of a ≥50%-controlled entity taxed below 75% of the Spanish tax is "
        "included (substance and passive-income rules apply).",
    )

    t = sd.treaty(fr, es, name="Convention between France and Spain (1995)",
                  signed=date(1995, 10, 10), in_force=date(1997, 7, 1), src=Src(
                      "Convenio entre España y Francia (BOE)",
                      "https://www.boe.es/eli/es/ai/1995/10/10/(1)/con", None,
                      "firmado en Madrid el 10 de octubre de 1995. Publicado en: «BOE» núm. "
                      "140, de 12/06/1997. Entrada en vigor: 01/07/1997"))
    start = date(2023, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convenio España–Francia, texto sintético con el MLI (Hacienda)", FR_ES,
        "Article 10(2)(a)",
        "el impuesto así exigido no podrá exceder del 15 por 100 del importe bruto de los "
        "dividendos"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convenio España–Francia, texto sintético con el MLI (Hacienda)", FR_ES,
        "Article 10(2)(b); MLI art. 8",
        "estos dividendos solo pueden someterse a imposición en el Estado contratante del que "
        "el beneficiario efectivo es residente, si este es una sociedad [...] que detente "
        "directamente al menos el 10 por 100 del capital [...] durante un período de 365 días"),
        exclusive=True, ownership_threshold="10", min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Convenio España–Francia, texto sintético con el MLI (Hacienda)", FR_ES,
        "Article 11(2)",
        "el impuesto así exigido no puede exceder del 10 por 100 del importe bruto de los "
        "intereses."), max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Convenio España–Francia, texto sintético con el MLI (Hacienda)", FR_ES,
        "Article 12(2)(a)",
        "el impuesto así establecido no puede exceder del 5 por 100 del importe bruto de los "
        "cánones."), max_rate="5")
    sd.ppt(t, start, Src(
        "Convenio España–Francia, texto sintético con el MLI (Hacienda)", FR_ES,
        "MLI art. 7(1)",
        "El siguiente apartado 1 del artículo 7 del MLI se aplica a este Convenio: ARTÍCULO 7 – "
        "IMPEDIR LA UTILIZACIÓN ABUSIVA DE LOS CONVENIOS"), dividend_min_holding_days=365)

    t = sd.treaty(es, ae, name="Convention between Spain and the United Arab Emirates (2006)",
                  signed=date(2006, 3, 5), in_force=date(2007, 4, 2), src=Src(
                      "Convenio España–EAU (BOE 23.01.2007)",
                      "https://www.boe.es/boe/dias/2007/01/23/pdfs/A03019-03028.pdf", None,
                      "El presente Convenio y su Protocolo anejo entrarán en vigor el 2 de abril "
                      "de 2007"))
    start = date(2007, 4, 2)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convenio España–EAU, texto sintético (Hacienda)", ES_AE, "Article 10(2)(b)",
        "b) 15 por ciento del importe bruto de los dividendos en todos los demás casos."),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convenio España–EAU, texto sintético (Hacienda)", ES_AE, "Article 10(2)(a)",
        "a) 5 por ciento del importe bruto de los dividendos si el beneficiario efectivo es una "
        "sociedad que controle directamente al menos el 10 por ciento del capital"),
        max_rate="5", ownership_threshold="10")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            "Convenio España–EAU, texto sintético (Hacienda)", ES_AE, f"{art}(1)",
            "cuyo beneficiario efectivo sea un residente del otro Estado contratante solo "
            "pueden someterse a imposición en ese otro Estado"), exclusive=True)
    sd.ppt(t, date(2023, 1, 1), Src(
        "Convenio España–EAU, texto sintético (Hacienda)", ES_AE, "MLI art. 7(1)",
        "El siguiente apartado 1 del artículo 7 del MLI reemplaza al apartado 7 del artículo 10, "
        "al apartado 5 del artículo 11 y al apartado 5 del artículo 12 de este Convenio"))


def _singapore(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, sg: Jurisdiction) -> None:
    sd.cit(sg, date(2010, 1, 1), Src(
        "Income Tax Act 1947 s.43 (Singapore Statutes Online)", SSO + "pr43-", "ITA s.43(1)(a)",
        "every company or body of persons, tax at the rate of 17% on every dollar of the "
        "chargeable income thereof"), rate="17")
    sd.wht(sg, "DIVIDEND", "0", date(2010, 1, 1), Src(
        "Payments not subject to withholding tax (IRAS)",
        IRAS + "taxes/withholding-tax/payments-to-non-resident-company/"
        "payments-that-are-not-subject-to-withholding-tax", None,
        "Singapore currently does not impose withholding tax on dividends."))
    sd.wht(sg, "INTEREST", "15", date(2010, 1, 1), Src(
        "Income Tax Act 1947 s.43 (Singapore Statutes Online)", SSO + "pr43-", "ITA s.43(3)(a)",
        "(3) [...] tax at the rate of 15% is to be levied and paid on the gross amount of — (a) "
        "any income referred to in section 12(6)"))
    sd.wht(sg, "ROYALTY", "10", date(2010, 1, 1), Src(
        "Income Tax Act 1947 s.43 (Singapore Statutes Online)", SSO + "pr43-", "ITA s.43(3A)",
        "(3A) Despite anything in this Act, tax at the rate of 10% is to be levied and paid on "
        "the gross amount of any income referred to in section 12(7)(a) and (b)"))
    sd.regime(
        sg, date(2025, 3, 20),
        Src("Income Tax Act 1947 s.13(8)-(9) (Singapore Statutes Online)", SSO + "pr13-",
            "ITA s.13(8), (9)",
            "the highest rate of tax of a similar character to income tax [...] levied under "
            "the law of the territory from which the income is received on any gains or "
            "profits from any trade or business [...] is not less than 15%"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=True,
        min_subject_to_tax_rate=15, exempt_share_pct=100,
        notes="Foreign-sourced dividends exempt when subject to tax and the source headline "
        "rate is ≥15% (no shareholding requirement); share gains via s.13W (≥20%, 24 months)",
    )

    t = sd.treaty(fr, sg, name="Convention between France and Singapore (2015)",
                  signed=date(2015, 1, 15), in_force=date(2016, 6, 1), src=Src(
                      "Singapore–France DTA with MLI (IRAS)", FR_SG, None,
                      "Date of Conclusion: 15 January 2015 Entry into Force: 1 June 2016 "
                      "Effective Date: 1 January 2017"))
    start = date(2017, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Singapore–France DTA (IRAS)", FR_SG, "Article 10(2)(b)",
        "(b) in all other cases, 15 per cent"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Singapore–France DTA (IRAS)", FR_SG, "Article 10(2)(a)",
        "(a) 5 per cent [...] if the beneficial owner is a company which owns directly or "
        "indirectly at least 10 per cent of the share capital"),
        max_rate="5", ownership_threshold="10")
    # Art. 11(3)(c): interest paid by an enterprise of one State to an enterprise of the other
    # is taxable only in the residence State — the case for company-to-company flows.
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Singapore–France DTA (IRAS)", FR_SG, "Article 11(3)(c)",
        "interest [...] paid by an enterprise of one of the Contracting States to an enterprise "
        "of the other Contracting State (taxable only in the State of residence; 10% cap "
        "otherwise)"), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Singapore–France DTA (IRAS)", FR_SG, "Article 12(1)",
        "Royalties arising in a Contracting State and beneficially owned by a resident of the "
        "other Contracting State shall be taxable only in that other State."), exclusive=True)
    sd.ppt(t, date(2020, 1, 1), Src(
        "Singapore–France DTA with MLI, Annex A (IRAS)", FR_SG, "MLI art. 7(1)",
        "a benefit under this Convention shall not be granted [...] if it is reasonable to "
        "conclude [...] that obtaining that benefit was one of the principal purposes of any "
        "arrangement or transaction"))

    t = sd.treaty(sg, ae, name="Agreement between Singapore and the UAE (1995, protocol 2014)",
                  signed=date(1995, 12, 1), in_force=date(1996, 8, 30), src=Src(
                      "Singapore–UAE DTA with MLI and Second Protocol (IRAS)", SG_AE, None,
                      "Date of Conclusion: 1 December 1995. Entry into Force: 30 August 1996 "
                      "[...] A Protocol signed on 31 October 2014 entered into force on 16 March "
                      "2016 and its provisions shall take effect from 1 January 2017."))
    start = date(2017, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Singapore–UAE DTA, Second Protocol (IRAS)", SG_AE, "Article 10(1)",
        "Dividends paid by a company which is a resident of a Contracting State to a resident of "
        "the other Contracting State shall be taxable only in that other State."),
        exclusive=True)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Singapore–UAE DTA, Second Protocol (IRAS)", SG_AE, "Article 11(1)",
        "Interest arising in a Contracting State and paid to a resident of the other "
        "Contracting State shall be taxable only in that other State."), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Singapore–UAE DTA (IRAS)", SG_AE, "Article 12(2)",
        "if the recipient is the beneficial owner of the royalties then the tax so charged shall "
        "not exceed 5 percent of the gross amount of such royalties"), max_rate="5")
    sd.ppt(t, date(2020, 1, 1), Src(
        "Singapore–UAE DTA with MLI, Annex A (IRAS)", SG_AE, "MLI art. 7(1)",
        "a benefit under this Agreement shall not be granted [...] if it is reasonable to "
        "conclude [...] that obtaining that benefit was one of the principal purposes"))


def _switzerland(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, ch: Jurisdiction, eu: JurisdictionGroup
) -> None:
    # City of Zug 2026: federal 8.5% + cantonal/communal 4.759% of profit after tax;
    # taxes are deductible, so (8.5 + 4.759) / 1.13259 = 11.71% of profit before tax.
    sd.cit(ch, date(2026, 1, 1), Src(
        "Steuerbelastungen 2023-2026 (Kanton Zug); DBG art. 68 (fedlex)", CH_ZG,
        "DBG art. 68; StG ZG",
        "Zug 2026 [...] Kanton: 78.000 % EG: 52.000 % [...] Total Steuerfuss 135.962 % RG: bis "
        "3.50 % 4.759 % — Die Gewinnsteuer [...] beträgt 8,5 Prozent des Reingewinns "
        "(combined 11.71% of profit before tax, derived)"), rate="11.71", end=date(2027, 1, 1))
    sd.wht(ch, "DIVIDEND", "35", date(2025, 1, 1), Src(
        "Verrechnungssteuergesetz art. 13 (fedlex)", CH_VSTG, "VStG art. 13(1)(a)",
        "Die Steuer beträgt: a. auf Kapitalerträgen [...] 35 Prozent der steuerbaren Leistung"))
    sd.wht(ch, "INTEREST", "0", date(2025, 1, 1), Src(
        "Verrechnungssteuerverordnung art. 14a (fedlex)",
        FEDLEX + "1966/1585_1641_1624/de", "VStV art. 14a(1)",
        "Zwischen Konzerngesellschaften bestehende Guthaben gelten weder als Obligationen [...] "
        "noch als Kundenguthaben"))
    sd.wht(ch, "ROYALTY", "0", date(2025, 1, 1), Src(
        "Verrechnungssteuergesetz art. 4 (fedlex)", CH_VSTG, "VStG art. 4(1)",
        "[Summary — no single clause to quote] VStG art. 4(1) lists the taxable income "
        "exhaustively (interest on bonds and bank deposits, capital income, lottery gains, "
        "insurance); royalties are not on the list."))
    sd.exemption(
        ch, "DIVIDEND", eu, date(2017, 1, 1),
        Src("Abkommen Schweiz–EU über den automatischen Informationsaustausch, art. 9 (fedlex)",
            CH_EU, "AEOI agreement art. 9(1)",
            "werden Dividendenzahlungen von Tochtergesellschaften an Muttergesellschaften im "
            "Quellenstaat nicht besteuert, wenn: – die Muttergesellschaft mindestens zwei Jahre "
            "lang eine direkte Beteiligung von mindestens 25 Prozent [...] hält"),
        min_holding_pct="25", min_holding_months=24, legal_ref="CH-EU agreement art. 9",
        description="dividends to an EU parent holding ≥25% directly for 2 years",
    )
    sd.regime(
        ch, date(2011, 1, 1),
        Src("DBG art. 69-70 (fedlex)", CH_DBG, "DBG art. 69, 70",
            "a. zu mindestens 10 Prozent am Grund- oder Stammkapital [...] c. Beteiligungsrechte "
            "im Verkehrswert von mindestens einer Million Franken hält [...] abzüglich des "
            "darauf entfallenden Finanzierungsaufwandes und eines Beitrages von 5 Prozent zur "
            "Deckung des Verwaltungsaufwandes"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=10, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=95,
        notes="Beteiligungsabzug: tax reduced in proportion to net participation income "
        "(less financing costs and a 5% administration charge); ≥10% or CHF 1m; gains ≥10% "
        "held 1 year. Switzerland has no CFC rules (EFD, 2023).",
    )

    # France–Switzerland 1966, as amended; recorded from the 2009 avenant (in force 2010-11-04).
    t = sd.treaty(fr, ch, name="Convention between France and Switzerland (1966, as amended)",
                  signed=date(1966, 9, 9), in_force=date(2010, 11, 4), src=Src(
                      "Convention franco-suisse, état consolidé 24.07.2025 (fedlex)", FR_CH,
                      None, "Avenant du 27 août 2009 [...] entré en vigueur le 4 novembre 2010 "
                      "(dividend article 11 as amended)"))
    start = date(2010, 11, 4)
    sd.treaty_rate(t, "DIVIDEND", "Article 11", start, Src(
        "Convention franco-suisse (fedlex)", FR_CH, "Article 11(2)(a)",
        "l'impôt ainsi établi ne peut excéder 15 % du montant brut des dividendes."),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 11", start, Src(
        "Convention franco-suisse (fedlex)", FR_CH, "Article 11(2)(b)(i)",
        "qui détient directement ou indirectement au moins 10 % du capital de la première "
        "société, ne sont imposables que dans cet autre État."),
        exclusive=True, ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 12", start, Src(
        "Convention franco-suisse (fedlex)", FR_CH, "Article 12(1)",
        "Les intérêts [...] ne sont imposables que dans cet autre État, si ce résident en est "
        "le bénéficiaire effectif."), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 13", start, Src(
        "Convention franco-suisse (fedlex)", FR_CH, "Article 13(2)",
        "l'impôt ainsi établi ne peut excéder 5 % du montant brut des redevances."),
        max_rate="5")
    sd.ppt(t, date(2026, 1, 1), Src(
        "Avenant du 27 juin 2023 à la convention franco-suisse (RO 2025 486, fedlex)",
        "https://www.fedlex.admin.ch/eli/oc/2025/486/fr", "Article 29",
        "un avantage au titre de celle-ci ne sera pas accordé [...] s'il est raisonnable de "
        "conclure [...] que l'octroi de cet avantage était l'un des objets principaux d'un "
        "montage ou d'une transaction"))

    t = sd.treaty(ch, ae, name="Agreement between Switzerland and the UAE (2011)",
                  signed=date(2011, 10, 6), in_force=date(2012, 10, 21), src=Src(
                      "Abkommen Schweiz–VAE (fedlex)", CH_AE, None,
                      "Abgeschlossen am 6. Oktober 2011 [...] In Kraft getreten durch "
                      "Notenaustausch am 21. Oktober 2012"))
    start = date(2012, 10, 21)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Abkommen Schweiz–VAE (fedlex)", CH_AE, "Article 10(2)(b)",
        "b) 15 Prozent des Bruttobetrags der Dividenden in allen anderen Fällen."),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Abkommen Schweiz–VAE (fedlex)", CH_AE, "Article 10(2)(a)",
        "a) 5 Prozent des Bruttobetrags der Dividenden, wenn die nutzungsberechtigte Person eine "
        "Gesellschaft ist, die unmittelbar über mindestens 10 Prozent des Kapitals [...] "
        "verfügt"), max_rate="5", ownership_threshold="10")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            "Abkommen Schweiz–VAE (fedlex)", CH_AE, f"{art}(1)",
            "können nur im anderen Staat besteuert werden."), exclusive=True)
    sd.ppt(t, date(2026, 1, 1), Src(
        "Abkommen Schweiz–VAE, Protokoll 2022, art. 26A (fedlex)", CH_AE, "Article 26A",
        "wird ein Vorteil nach diesem Abkommen nicht [...] gewährt, wenn [...] der Erhalt dieses "
        "Vorteils einer der Hauptzwecke einer Gestaltung oder Transaktion war"))
