"""P8 batch 1: Luxembourg, the Netherlands, Cyprus — plus France's EU-directive exemptions.

Figures were sourced on 2026-10-05 from the official texts cited on each `Src` and are stored
as `unreviewed` until a named reviewer confirms them (spec §10). Research notes:
docs/superpowers/plans/2026-10-05-p8-batch1.md.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import JurisdictionGroup
from app.modules.risk.repository import ListDefinitionRepository
from app.modules.seed.builder import Seeder, Src

EU_URL = "https://european-union.europa.eu/principles-countries-history/eu-countries/{}_en"
LF = "https://www.legifrance.gouv.fr/codes/article_lc/"

# --- Luxembourg ------------------------------------------------------------------------------
LU_LIR = (
    "https://impotsdirects.public.lu/dam-assets/fr/legislation/LIR/"
    "texte-coordonn-en-vigueur-au-1er-janvier-2026-ver-08052026.pdf"
)
LU_CF = "https://impotsdirects.public.lu/fr/az/c/charg_fisc.html"
LU_TX = "https://impotsdirects.public.lu/fr/conventions/tx_ret.html"
LU_PROC = "https://impotsdirects.public.lu/fr/conventions/proced.html"
LU_STT = "https://impotsdirects.public.lu/fr/az/i/impot_correspondant.html"
FR_LU = "https://data.legilux.public.lu/file/eli-etat-leg-memorial-2019-495-fr-pdf.pdf"
FR_LU_BOFIP = "https://bofip.impots.gouv.fr/bofip/2451-PGP.html/identifiant=BOI-INT-CVB-LUX-20210223"
LU_AE = "https://data.legilux.public.lu/file/eli-etat-leg-memorial-2009-136-fr-pdf.pdf"
LU_AE_EIF = "https://data.legilux.public.lu/file/eli-etat-leg-memorial-2009-256-fr-pdf.pdf"
LU_AE_MLI = "https://impotsdirects.public.lu/dam-assets/fr/conventions/mli/unitedarabemirates-mli-en.pdf"

# --- Netherlands -----------------------------------------------------------------------------
NL_VPB = "https://wetten.overheid.nl/BWBR0002672/2026-01-01"
NL_VPB_RATES = (
    "https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/zakelijk/"
    "winst/vennootschapsbelasting/tarieven_vennootschapsbelasting"
)
NL_DB = "https://wetten.overheid.nl/BWBR0002515/"
NL_BRON = "https://wetten.overheid.nl/BWBR0042952/"
NL_BRON_INFO = (
    "https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/zakelijk/"
    "winst/bronbelasting-rente-en-royalty"
)
NL_LOWTAX = "https://wetten.overheid.nl/BWBR0041785/2026-01-01/0"
FR_NL = "https://wetten.overheid.nl/BWBV0004110/"
FR_NL_MLI = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/pays-bas/"
    "pays-bas_modifiee_cml_20190805.pdf"
)
NL_AE = "https://wetten.overheid.nl/BWBV0003163/"
NL_AE_MLI = "https://zoek.officielebekendmakingen.nl/trb-2023-50.pdf"

# --- Cyprus ----------------------------------------------------------------------------------
CY_ITL = "https://www.cylaw.org/nomoi/enop/non-ind/2002_1_118/full.html"
CY_SDC = "https://www.cylaw.org/nomoi/enop/non-ind/2002_1_117/full.html"
CY_L244 = "https://www.cylaw.org/nomoi/arith/2025_1_244.pdf"
CY_L245 = "https://www.cylaw.org/nomoi/arith/2025_1_245.pdf"
FR_CY = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/chypre/"
    "chypre_convention-avec-chypre_fd_1818.pdf"
)
FR_CY_MLI = (
    "https://www.impots.gouv.fr/"
    "version-consolidee-de-la-convention-avec-chypre-modifiee-par-la-convention-multilaterale"
)
CY_TREATIES = (
    "https://www.gov.cy/mof/documents/forologiki-politiki-kai-metarrythmiseis-2/"
    "symvaseis-apofygis-diplis-forologias-2/"
)
CY_AE = "https://www.gov.cy/media/sites/11/2024/03/united_arab_emirates_2011_02_27_1st_en.pdf"


def seed_batch_eu1(session: Session) -> None:
    sd = Seeder(session)
    fr = sd.jurisdiction("FR", "France")
    ae = sd.jurisdiction("AE", "United Arab Emirates")
    lu = sd.jurisdiction("LU", "Luxembourg")
    nl = sd.jurisdiction("NL", "Netherlands")
    cy = sd.jurisdiction("CY", "Cyprus")
    vu = sd.jurisdiction("VU", "Vanuatu")
    pa = sd.jurisdiction("PA", "Panama")

    # EU membership (for directive exemptions).
    eu = sd.group("EU", "European Union member states")
    for j, slug, start in (
        (fr, "france", date(1958, 1, 1)),
        (lu, "luxembourg", date(1958, 1, 1)),
        (nl, "netherlands", date(1958, 1, 1)),
        (cy, "cyprus", date(2004, 5, 1)),
    ):
        when = "1 May 2004" if start.year == 2004 else "1 January 1958"
        sd.member(eu, j, start, Src(
            f"{j.name} — EU member country profile (european-union.europa.eu)",
            EU_URL.format(slug), None, f"EU Member State: since {when}",
        ))

    _france_directives(sd, fr, eu)
    _luxembourg(sd, fr, ae, lu, eu)
    _netherlands(sd, fr, ae, nl, eu, vu, pa)
    _cyprus(sd, fr, ae, cy, eu)


def _france_directives(sd: Seeder, fr: Jurisdiction, eu: JurisdictionGroup) -> None:
    sd.exemption(
        fr, "DIVIDEND", eu, date(2016, 1, 1),
        Src("CGI art. 119 ter (Légifrance)", LF + "LEGIARTI000031815505", "CGI art. 119 ter, 2 c",
            "Détenir directement, de façon ininterrompue depuis deux ans ou plus [...] 10 % au "
            "moins du capital de la personne morale qui distribue les dividendes"),
        min_holding_pct="10", min_holding_months=24, legal_ref="CGI art. 119 ter",
        description="Parent-Subsidiary Directive: dividends to an EU parent holding ≥10% for "
        "2 years (5% where the parent cannot credit the tax — not modelled)",
    )
    sd.exemption(
        fr, "ROYALTY", eu, date(2019, 12, 15),
        Src("CGI art. 182 B bis / 119 quater (Légifrance)", LF + "LEGIARTI000039382322",
            "CGI art. 182 B bis; art. 119 quater",
            "La retenue à la source prévue à l'article 182 B n'est pas applicable aux redevances "
            "payées [...] à une personne morale qui est son associée [...] participation directe "
            "d'au moins 25 % [...] détenue de façon ininterrompue depuis deux ans au moins ou "
            "fasse l'objet d'un engagement"),
        min_holding_pct="25", min_holding_months=24, legal_ref="CGI art. 182 B bis",
        description="Interest and Royalties Directive: royalties to an associated EU company "
        "(≥25% for 2 years, or a commitment to hold)",
    )


def _luxembourg(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, lu: Jurisdiction, eu: JurisdictionGroup
) -> None:
    sd.cit(lu, date(2025, 1, 1), Src(
        "Charge fiscale des collectivités (ACD)", LU_CF, "LIR art. 174; ICC Luxembourg-Ville",
        "Charge fiscale d'une collectivité au taux d'imposition nominal (A+B+C) [...] 24,94% "
        "23,87% (de 2019 à 2024 / à partir de 2025) — IRC 16%, fonds pour l'emploi 7% (1,12), "
        "impôt commercial Luxembourg 225% x 3% (6,75)",
    ), rate="23.87")
    wht_src = Src("LIR coordonnée au 1er janvier 2026, art. 148", LU_LIR, "LIR art. 146, 148",
                  "(1) Le taux de la retenue est fixé à 15%.")
    sd.wht(lu, "DIVIDEND", "15", date(2026, 1, 1), wht_src)
    sd.wht(lu, "INTEREST", "0", date(2004, 1, 1), Src(
        "Retenue à la source — taux (ACD)", LU_TX, "LIR art. 146(1) 3°",
        "Si ce critère n'est pas rempli, la législation interne ne prévoit actuellement aucune "
        "retenue d'impôt à la source à appliquer aux intérêts.",
    ))
    sd.wht(lu, "ROYALTY", "0", date(2004, 1, 1), Src(
        "Procédures conventions (ACD)", LU_PROC, None,
        "La retenue d'impôt sur les redevances a été abrogée avec effet au 1er janvier 2004.",
    ))
    sd.exemption(
        lu, "DIVIDEND", eu, date(2026, 1, 1),
        Src("LIR coordonnée au 1er janvier 2026, art. 147", LU_LIR, "LIR art. 147 n° 2",
            "le bénéficiaire détient ou s'engage à détenir [...] pendant une période "
            "ininterrompue d'au moins douze mois, une participation d'au moins 10 pour cent ou "
            "d'un prix d'acquisition d'au moins 1.200.000 euros"),
        min_holding_pct="10", min_holding_months=12, legal_ref="LIR art. 147",
        description="EU parent (Directive 2011/96/EU) holding ≥10% (or ≥ EUR 1.2m) for 12 months, "
        "or committing to; treaty-country companies may also qualify — not modelled",
    )
    sd.regime(
        lu, date(2025, 1, 1),
        Src("LIR art. 166 / impôt correspondant (ACD)", LU_STT, "LIR art. 166",
            "à un taux d'impôt effectif qui ne peut être inférieur à la moitié du taux d'impôt "
            "sur le revenu des collectivités luxembourgeois [...] A partir de l'année "
            "d'imposition 2025 16% 8,00%"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=10, min_holding_period_months=12, subject_to_tax_condition=True,
        min_subject_to_tax_rate=8, exempt_share_pct=100,
        notes="LIR art. 166: ≥10% or ≥ EUR 1.2m (gains: ≥ EUR 6m) for 12 months; non-EU "
        "subsidiaries taxed ≥8% (ACD doctrine)",
    )
    sd.cfc(
        lu, date(2019, 1, 1),
        Src("LIR coordonnée au 1er janvier 2026, art. 164ter", LU_LIR, "LIR art. 164ter",
            "l'impôt réel [...] est inférieur à la différence entre, d'une part, l'impôt sur "
            "le revenu des collectivités qui aurait été supporté [...] et, d'autre part, "
            "l'impôt réel"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="LIR art. 164ter",
        effect="Undistributed income of non-genuine arrangements of a >50%-controlled entity "
        "taxed below half the Luxembourg CIT is included (de minimis thresholds apply).",
    )

    # France–Luxembourg, 20 March 2018 (in force 19 Aug 2019; WHT from 1 Jan 2020).
    t = sd.treaty(fr, lu, name="Convention between France and Luxembourg (2018)",
                  signed=date(2018, 3, 20), in_force=date(2019, 8, 19), src=Src(
                      "Convention France–Luxembourg (BOFiP)", FR_LU_BOFIP, "Article 30",
                      "signée à Paris le 20 mars 2018 [...] est entrée en vigueur le 19 août "
                      "2019 [...] aux sommes imposables à compter du 1er janvier 2020"))
    start = date(2020, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Luxembourg (Mémorial A 495/2019)", FR_LU, "Article 10(2)(a)",
        "ne peut excéder 15 % du montant brut des dividendes"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Luxembourg (Mémorial A 495/2019)", FR_LU, "Article 10(2)(b)",
        "détient directement au moins 5 % du capital de la société qui paie les dividendes "
        "pendant une période de 365 jours incluant le jour du paiement des dividendes"),
        exclusive=True, ownership_threshold="5", min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Convention France–Luxembourg (Mémorial A 495/2019)", FR_LU, "Article 11(1)",
        "Les intérêts provenant d'un Etat contractant et payés à un résident de l'autre Etat "
        "contractant ne sont imposables que dans cet autre Etat."), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Convention France–Luxembourg (Mémorial A 495/2019)", FR_LU, "Article 12(2)",
        "l'impôt ainsi établi ne peut excéder 5 % pour cent du montant brut des redevances"),
        max_rate="5")
    sd.ppt(t, start, Src(
        "Convention France–Luxembourg (Mémorial A 495/2019)", FR_LU, "Article 28",
        "un avantage au titre de celle-ci ne sera pas accordé [...] si l'on peut raisonnablement "
        "conclure [...] que l'octroi de cet avantage était un des objets principaux d'un montage "
        "ou d'une transaction"))

    # Luxembourg–UAE, 20 Nov 2005 (in force 19 Jun 2009; from 1 Jan 2010).
    t = sd.treaty(lu, ae, name="Convention between Luxembourg and the United Arab Emirates",
                  signed=date(2005, 11, 20), in_force=date(2009, 6, 19), src=Src(
                      "Luxembourg–UAE convention, entry into force (Mémorial A 256/2009)",
                      LU_AE_EIF, "Article 29",
                      "la Convention et le Protocole sont entrés en vigueur à l'égard des deux "
                      "Parties contractantes le 19 juin 2009"))
    start = date(2010, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Luxembourg–UAE convention (Mémorial A 136/2009)", LU_AE, "Article 10(2)(b)",
        "b) 10 pour cent du montant brut des dividendes, dans tous les autres cas."),
        max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Luxembourg–UAE convention (Mémorial A 136/2009)", LU_AE, "Article 10(2)(a)",
        "a) 5 pour cent du montant brut des dividendes, si le bénéficiaire effectif est une "
        "société (autre qu'une société de personnes) qui détient directement au moins 10 pour "
        "cent du capital"), max_rate="5", ownership_threshold="10")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            "Luxembourg–UAE convention (Mémorial A 136/2009)", LU_AE, f"{art}(1)",
            "ne sont imposables que dans cet autre Etat, si ce résident en est le bénéficiaire "
            "effectif."), exclusive=True)
    sd.ppt(t, start=date(2020, 1, 1), src=Src(
        "Luxembourg–UAE MLI synthesised text (ACD)", LU_AE_MLI, "MLI art. 7(1)",
        "The following paragraph 1 of Article 7 of the MLI applies and supersedes the provisions "
        "of this Convention [...] with respect of taxes withheld at source [...] on or after "
        "1 January 2020"))


def _netherlands(
    sd: Seeder,
    fr: Jurisdiction,
    ae: Jurisdiction,
    nl: Jurisdiction,
    eu: JurisdictionGroup,
    vu: Jurisdiction,
    pa: Jurisdiction,
) -> None:
    sd.cit(nl, date(2023, 1, 1), Src(
        "Tarieven vennootschapsbelasting (Belastingdienst)", NL_VPB_RATES, "Wet Vpb 1969 art. 22",
        "De tarieven voor de vennootschapsbelasting in 2026, 2025, 2024 en 2023 zijn: [...] tot "
        "en met € 200.000 19,0% boven € 200.000 25,8%",
    ), brackets=[("0", "200000", "19"), ("200000", None, "25.8")])
    sd.wht(nl, "DIVIDEND", "15", date(2025, 1, 1), Src(
        "Wet op de dividendbelasting 1965, art. 5", NL_DB, "Wet DB 1965 art. 5",
        "De belasting bedraagt 15% van de opbrengst."))
    no_wht = Src(
        "Bronbelasting op rente en royalty's (Belastingdienst)", NL_BRON_INFO,
        "Wet bronbelasting 2021",
        "De Wet bronbelasting 2021 regelt een bronbelasting op bepaalde rente-, royalty- en "
        "dividendbetalingen. Het gaat dan om een betaling door een in Nederland gevestigd lichaam "
        "aan een gelieerd lichaam in een laagbelastend land, en om bepaalde misbruiksituaties.")
    sd.wht(nl, "INTEREST", "0", date(2021, 1, 1), no_wht)
    sd.wht(nl, "ROYALTY", "0", date(2021, 1, 1), no_wht)
    sd.exemption(
        nl, "DIVIDEND", eu, date(2025, 1, 1),
        Src("Wet op de dividendbelasting 1965, art. 4", NL_DB, "Wet DB 1965 art. 4(2)",
            "de opbrengstgerechtigde [...] een belang in de inhoudingsplichtige heeft waarop de "
            "deelnemingsvrijstelling, bedoeld in artikel 13 van de Wet op de "
            "vennootschapsbelasting 1969 [...] van toepassing zou zijn indien hij in Nederland "
            "zou zijn gevestigd."),
        min_holding_pct="5", min_holding_months=None, legal_ref="Wet DB 1965 art. 4",
        description="EU/EEA parent with a ≥5% (participation-exemption) interest; no holding "
        "period; anti-abuse and beneficial-ownership conditions",
    )
    # Art. 4(2)(a) extends the exemption to companies in treaty states with a dividend article.
    nl_treaty = sd.group("NL_DIV_TREATY", "States with a Dutch tax treaty containing a dividend "
                                          "article (Wet DB art. 4(2)(a))")
    sd.member(nl_treaty, ae, date(2025, 1, 1), Src(
        "Netherlands–UAE convention (wetten.overheid.nl)", NL_AE, "Article 10",
        "02-06-2010 Nieuwe-regeling, inwerkingtreding Trb. 2007, 107 Trb. 2010, 178 08-05-2007 "
        "Totstandkoming"))
    sd.exemption(
        nl, "DIVIDEND", nl_treaty, date(2025, 1, 1),
        Src("Wet op de dividendbelasting 1965, art. 4", NL_DB, "Wet DB 1965 art. 4(2)(a)",
            "de opbrengstgerechtigde [...] een belang in de inhoudingsplichtige heeft waarop de "
            "deelnemingsvrijstelling [...] van toepassing zou zijn indien hij in Nederland zou "
            "zijn gevestigd."),
        min_holding_pct="5", min_holding_months=None, legal_ref="Wet DB 1965 art. 4",
        description="Parent resident in a treaty state with a dividend article, ≥5% interest; "
        "anti-abuse and beneficial-ownership conditions",
    )
    sd.regime(
        nl, date(2026, 1, 1),
        Src("Wet Vpb 1969, art. 13 (deelnemingsvrijstelling)", NL_VPB, "Wet Vpb art. 13",
            "Bij het bepalen van de winst blijven buiten aanmerking de voordelen uit hoofde van "
            "een deelneming [...] voor ten minste 5% van het nominaal gestorte kapitaal "
            "aandeelhouder is"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=5, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Wet Vpb art. 13: ≥5%, no holding period, 100%; portfolio participations need a "
        "realistic levy (~10%, Belastingdienst guidance) — not modelled",
    )

    # Conditional withholding tax on payments to low-tax / EU-listed jurisdictions.
    ListDefinitionRepository(sd.s).get_or_create(
        "NL_LOW_TAX", name="Netherlands low-tax and non-cooperative jurisdictions "
        "(Regeling laagbelastende staten)", family="tax_governance", publisher="Netherlands",
        update_cadence="yearly (1 January)", source_evidence_id=sd.ev(Src(
            "Wet bronbelasting 2021, art. 1.2", NL_BRON, "Wet bronbelasting 2021 art. 1.2(1)(e)",
            "laagbelastende jurisdictie: een bij ministeriële regeling aangewezen staat die: "
            "1°. [...] lichamen niet of naar een tarief van minder dan 9% onderwerpt aan een "
            "belasting naar de winst; of 2°. is opgenomen in een [...] EU-lijst van "
            "niet-coöperatieve rechtsgebieden")))
    sd.s.flush()
    lowtax_2026 = Src(
        "Regeling laagbelastende staten 2026", NL_LOWTAX, "art. 2a",
        "Anguilla, Bahama's, [...] Turks- en Caicoseilanden, Vanuatu; en b. [...] Amerikaanse "
        "Maagdeneilanden, [...] Panama, Russische Federatie, Samoa, Trinidad en Tobago en Vanuatu")
    sd.listing(vu, "NL_LOW_TAX", "low_tax_and_eu_list", date(2026, 1, 1), date(2027, 1, 1),
               lowtax_2026)
    sd.listing(pa, "NL_LOW_TAX", "eu_list", date(2026, 1, 1), date(2027, 1, 1), lowtax_2026)
    rate_src = Src(
        "Wet bronbelasting 2021, art. 4.1", NL_BRON, "Wet bronbelasting 2021 art. 4.1",
        "De belasting bedraagt het hoogste percentage, bedoeld in artikel 22 van de Wet op de "
        "vennootschapsbelasting 1969 [...] (in 2024, 2025 en 2026 is dat 25,8%)")
    for cat in ("DIVIDEND", "INTEREST", "ROYALTY"):
        sd.consequence(
            nl, "NL_LOW_TAX", cat, "25.8", date(2024, 1, 1), rate_src,
            legal_ref="Wet bronbelasting 2021",
            description=f"Conditional withholding tax on {cat.lower()} to an affiliated entity "
            "(>50%) in a designated low-tax / EU-listed jurisdiction",
        )

    # France–Netherlands, 16 March 1973 (in force 29 Mar 1974; avenant in force 24 Jul 2005).
    t = sd.treaty(fr, nl, name="Convention between France and the Netherlands (1973)",
                  signed=date(1973, 3, 16), in_force=date(1974, 3, 29), src=Src(
                      "France–Netherlands convention (wetten.overheid.nl)",
                      "https://wetten.overheid.nl/BWBV0004110/2005-07-24/0/informatie", None,
                      "29-03-1974 Nieuwe-regeling, inwerkingtreding Trb. 1973, 83 Trb. 1974, 41 "
                      "16-03-1973 Totstandkoming"))
    start = date(2005, 7, 24)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "France–Netherlands convention (wetten.overheid.nl)", FR_NL, "Article 10(2)(b)",
        "b) 15 percent van het brutobedrag van de dividenden in alle andere gevallen."),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "France–Netherlands convention as modified by the MLI (impots.gouv.fr)", FR_NL_MLI,
        "Article 10(2)(a); MLI art. 8",
        "qui dispose directement d'au moins 25 p. cent du capital [...] tout au long d'une "
        "période de 365 jours incluant le jour du paiement des dividendes"),
        max_rate="5", ownership_threshold="25", min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "France–Netherlands convention (wetten.overheid.nl)", FR_NL, "Article 11(2)",
        "de aldus geheven belasting mag 10 percent van hef [sic] bedrag van de interest niet "
        "overschrijden."), max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "France–Netherlands convention (wetten.overheid.nl)", FR_NL, "Article 12(1)",
        "Royalty's afkomstig uit een van de Staten en betaald aan een inwoner van de andere "
        "Staat, zijn slechts in die andere Staat belastbaar."), exclusive=True)
    sd.ppt(t, date(2020, 1, 1), Src(
        "France–Netherlands convention as modified by the MLI (impots.gouv.fr)", FR_NL_MLI,
        "MLI art. 7(1)",
        "un avantage au titre de celle-ci ne sera pas accordé [...] si [...] l'octroi de cet "
        "avantage était l'un des objets principaux d'un montage ou d'une transaction"),
        dividend_min_holding_days=365)

    # Netherlands–UAE, 8 May 2007 (in force 2 Jun 2010; from 1 Jan 2011).
    t = sd.treaty(nl, ae, name="Convention between the Netherlands and the United Arab Emirates",
                  signed=date(2007, 5, 8), in_force=date(2010, 6, 2), src=Src(
                      "Netherlands–UAE convention (wetten.overheid.nl)",
                      "https://wetten.overheid.nl/BWBV0003163/2010-06-02/0/informatie", None,
                      "02-06-2010 Nieuwe-regeling, inwerkingtreding Trb. 2007, 107 Trb. 2010, "
                      "178 08-05-2007 Totstandkoming"))
    start = date(2011, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Netherlands–UAE convention (wetten.overheid.nl)", NL_AE, "Article 10(2)(b)",
        "b) 10 per cent of the gross amount of the dividends in all other cases."), max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Netherlands–UAE convention (wetten.overheid.nl)", NL_AE, "Article 10(2)(a)",
        "a) 5 per cent of the gross amount of the dividends if the beneficial owner is a company "
        "[...] which holds directly at least 10 per cent of the capital"),
        max_rate="5", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Netherlands–UAE convention (wetten.overheid.nl)", NL_AE, "Article 11(1)",
        "Interest arising in a Contracting State and beneficially owned by a resident of the "
        "other Contracting State shall be taxable only in that other State."), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Netherlands–UAE convention (wetten.overheid.nl)", NL_AE, "Article 12(1)",
        "Royalties arising in a Contracting State and beneficially owned by a resident of the "
        "other Contracting State shall be taxable only in that other State."), exclusive=True)
    sd.ppt(t, date(2020, 1, 1), Src(
        "Netherlands–UAE MLI synthesised text (Trb. 2023, 50)", NL_AE_MLI, "MLI art. 7(1)",
        "a benefit under the Convention shall not be granted [...] if [...] obtaining that "
        "benefit was one of the principal purposes of any arrangement or transaction"))


def _cyprus(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, cy: Jurisdiction, eu: JurisdictionGroup
) -> None:
    sd.cit(cy, date(2026, 1, 1), Src(
        "Law 244(I)/2025 amending the Income Tax Law (Official Gazette 5070, 31.12.2025)",
        CY_L244, "ITL art. 25, Second Annex para. 2; L.244 art. 24-25",
        "με την αντικατάσταση στην παράγραφο (2), της φράσης «δώδεκα και μισό» και του ποσοστού "
        "«12,5%» με τη λέξη «δεκαπέντε» και το ποσοστό «15%» [...] Ο παρών Νόμος τίθεται σε ισχύ "
        "από την 1η Ιανουαρίου 2026",
    ), rate="15")
    sd.wht(cy, "DIVIDEND", "0", date(2026, 1, 1), Src(
        "Special Defence Contribution Law 117(I)/2002 (consolidated, cylaw)", CY_SDC,
        "SDC art. 3(1)",
        "[Summary — no single clause to quote] SDC art. 3(1) charges dividends of Cyprus "
        "residents and, defensively, of companies in "
        "non-cooperative or low-tax jurisdictions; no general charge on other non-residents."))
    sd.wht(cy, "INTEREST", "0", date(2026, 1, 1), Src(
        "Special Defence Contribution Law 117(I)/2002 (consolidated, cylaw)", CY_SDC,
        "SDC art. 3B",
        "[Summary — no single clause to quote] SDC art. 3B charges interest of Cyprus "
        "residents and, defensively, of affiliated "
        "companies in non-cooperative jurisdictions; no general charge on other non-residents."))
    sd.wht(cy, "ROYALTY", "10", date(2002, 1, 1), Src(
        "Income Tax Law 118(I)/2002 (consolidated, cylaw)", CY_ITL, "ITL art. 21",
        "από οποιοδήποτε πρόσωπο το οποίο δεν είναι κάτοικος στη Δημοκρατία [...] υπόκειται σε "
        "φορολογία με συντελεστή δέκα σεντ κατά λίρα [...] σε περίπτωση κατά την οποία το "
        "δικαίωμα εκχωρείται για χρήση εκτός της Δημοκρατίας, το ποσό αυτό δε λογίζεται ως "
        "εισόδημα το οποίο αποκτάται από πηγές στη Δημοκρατία"))
    sd.exemption(
        cy, "ROYALTY", eu, date(2026, 1, 1),
        Src("Income Tax Law 118(I)/2002 (consolidated, cylaw)", CY_ITL, "ITL art. 21 proviso",
            "[Summary — no single clause to quote] Interest and Royalties Directive proviso to "
            "ITL art. 21: royalties to an associated "
            "company resident in another EU member state (minimum 25% direct holding)"),
        min_holding_pct="25", min_holding_months=None, legal_ref="ITL art. 21",
        description="Interest and Royalties Directive: royalties to an associated EU company "
        "(≥25% direct holding)",
    )
    for cat, rate, start, ref, quote in (
        ("DIVIDEND", "17", date(2022, 12, 31), "SDC art. 3(1)(δ)(i)(ββ)",
         "είναι κάτοικος σε μη συνεργάσιμη δικαιοδοσία [...] αναφορικά με οποιαδήποτε μερίσματα "
         "λαμβάνει από εταιρεία κάτοικο της Δημοκρατίας σε ποσοστό δεκαεπτά τοις εκατό (17%)"),
        ("INTEREST", "17", date(2026, 1, 1), "SDC art. 3B(γ)",
         "εταιρεία μη κάτοικος της Δημοκρατίας, η οποία είναι κάτοικος σε μη συνεργάσιμη "
         "δικαιοδοσία [...] αναφορικά με τόκους [...] σε ποσοστό δεκαεπτά τοις εκατό (17%)"),
        ("ROYALTY", "10", date(2022, 12, 31), "ITL art. 21A",
         "εταιρεία μη κάτοικος της Δημοκρατίας, η οποία είναι κάτοικος σε μη συνεργάσιμη "
         "δικαιοδοσία [...] υπόκειται σε φορολογία με συντελεστή ποσοστού ύψους δέκα τοις "
         "εκατό (10%)"),
    ):
        url = CY_ITL if ref.startswith("ITL") else CY_SDC
        sd.consequence(
            cy, "EU_TAX_ANNEX_I", cat, rate, start,
            Src("Cyprus defensive measures (consolidated law, cylaw)", url, ref, quote),
            legal_ref=ref,
            description=f"Withholding on {cat.lower()} to an affiliated (>50%) company in an EU "
            "non-cooperative jurisdiction",
        )
    sd.regime(
        cy, date(2026, 1, 1),
        Src("Income Tax Law 118(I)/2002 (consolidated, cylaw)", CY_ITL, "ITL art. 8(20), 8(22)",
            "(20) εισόδημα από μερίσματα [...] (22) κέρδος από τη διάθεση τίτλων."),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="ITL art. 8(20)/(22): dividends and gains on titles exempt, no minimum holding; "
        "5% SDC if the payer is >50% passive and taxed <50% of the Cyprus burden — not modelled",
    )
    sd.cfc(
        cy, date(2026, 1, 1),
        Src("Income Tax Law 118(I)/2002 (consolidated, cylaw)", CY_ITL, "ITL art. 36A",
            "συμμετοχή σε ποσοστό άνω του πενήντα τοις εκατό (50%) [...] και (β) ο πραγματικός "
            "εταιρικός φόρος [...] είναι χαμηλότερος του πενήντα τοις εκατό (50%) του φόρου που "
            "θα επιβαλλόταν [...] στη Δημοκρατία"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="ITL art. 36A",
        effect="Undistributed income of non-genuine arrangements of a >50%-controlled entity "
        "taxed below half the Cyprus tax is included.",
    )

    # France–Cyprus, 18 Dec 1981 (in force 1 Apr 1983). A 2023 convention is not yet in force.
    t = sd.treaty(fr, cy, name="Convention between France and Cyprus (1981)",
                  signed=date(1981, 12, 18), in_force=date(1983, 4, 1), src=Src(
                      "Convention France–Chypre (impots.gouv.fr)", FR_CY, None,
                      "signée à Nicosie le 18 décembre 1981 [...] entrée en vigueur le 1er "
                      "avril 1983"))
    start = date(1983, 4, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Chypre (impots.gouv.fr)", FR_CY, "Article 10(2)(b)",
        "b) 15 p. cent du montant brut des dividendes, dans tous les autres cas."), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Chypre (impots.gouv.fr)", FR_CY, "Article 10(2)(a)",
        "a) 10 p. cent du montant brut de ces dividendes si le bénéficiaire effectif est une "
        "société [...] qui détient directement au moins 10 p. cent du capital"),
        max_rate="10", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Convention France–Chypre (impots.gouv.fr)", FR_CY, "Article 11(2)",
        "l'impôt ainsi établi ne peut excéder 10 p. cent du montant brut des intérêts."),
        max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Convention France–Chypre (impots.gouv.fr)", FR_CY, "Article 12(1)",
        "1. Les redevances provenant d'un Etat et payées à un résident de l'autre Etat sont "
        "imposables dans cet autre Etat. (film royalties: source tax up to 5%, art. 12(2))"),
        exclusive=True)
    sd.ppt(t, date(2021, 1, 1), Src(
        "Convention France–Chypre modifiée par la CML (impots.gouv.fr)", FR_CY_MLI,
        "MLI art. 7(1)",
        "un avantage au titre de celle-ci ne sera pas accordé [...] s'il est raisonnable de "
        "conclure [...] que l'octroi de cet avantage était l'un des objets principaux d'un "
        "montage"))

    # Cyprus–UAE, 27 Feb 2011 (effective 1 Jan 2014 per the Cyprus MoF table).
    t = sd.treaty(cy, ae, name="Agreement between Cyprus and the United Arab Emirates",
                  signed=date(2011, 2, 27), in_force=date(2014, 1, 1), src=Src(
                      "Cyprus MoF double tax treaties table", CY_TREATIES, None,
                      "Ηνωμένα Αραβικά Εμιράτα | 27/02/2011 | 1/1/2014 | 4145 – 05/09/2011"))
    start = date(2014, 1, 1)
    for cat, art, quote in (
        ("DIVIDEND", "Article 11", "Dividends paid by a company which is a resident of a "
         "Contracting State to a resident of the other Contracting State shall be taxable only "
         "in that other State."),
        ("INTEREST", "Article 12", "Interest arising in a Contracting State and paid to a "
         "resident of the other Contracting State shall be taxable only in that other State."),
        ("ROYALTY", "Article 13", "Royalties arising in a Contracting State and paid to a "
         "resident of the other Contracting State shall be taxable only in that other State."),
    ):
        sd.treaty_rate(t, cat, art, start, Src(
            "Cyprus–UAE agreement (official English text, gov.cy)", CY_AE, f"{art}(1)", quote),
            exclusive=True)
