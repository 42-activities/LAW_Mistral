"""P8 batch 7: Bulgaria, Romania, Greece.

Figures were sourced on 2026-10-05 from the texts cited on each `Src` and are stored as
`unreviewed` until a named reviewer confirms them (spec §10). Research notes:
docs/superpowers/plans/2026-10-05-p8-batch7.md.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import JurisdictionGroup
from app.modules.seed.builder import Seeder, Src

EU_URL = "https://european-union.europa.eu/principles-countries-history/eu-countries/{}_en"
BG_ZKPO = (
    "https://www.ciela.net/svobodna-zona-normativi/view/2135540562/"
    "zakon-za-korporativnoto-podohodno-oblagane"
)
BG_SRC = "ЗКПО, consolidated to ДВ 55/2026 (Ciela legal publisher — lex.bg blocked)"
FR_BG = (
    "https://www.impots.gouv.fr/"
    "version-consolidee-de-la-convention-avec-la-bulgarie-modifiee-par-la-convention-multilaterale"
)
RO_CF = "https://static.anaf.ro/static/10/Anaf/legislatie/Cod_fiscal_norme_2023.htm"
RO_SRC = "Codul fiscal (Legea 227/2015), ANAF consolidated edition to OUG 38/2026"
RO_L141 = "https://static.anaf.ro/static/10/Anaf/legislatie/L_141_2025.pdf"
FR_RO = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/roumanie/"
    "roumanie_convention-avec-la-roumanie_fd_2107.pdf"
)
GR_KFE = "https://www.taxheaven.gr/law/4172/2013/arthro/{}"
GR_SRC = "ΚΦΕ ν. 4172/2013, taxheaven.gr consolidation (secondary — official portals blocked)"
FR_GR = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/grece/"
    "nid_26932_grece_2022.pdf"
)
GR_AE = "https://www.taxheaven.gr/law/4234/2014/arthro/{}"
BG_AE = (
    "https://nra.bg/wps/wcm/connect/nra.bg25863/43804ebd-ccbd-488a-9844-035d8dce35bc/"
    "DTC_BG_AE_bg.pdf?MOD=AJPERES"
)


def seed_batch7(session: Session) -> None:
    sd = Seeder(session)
    fr = sd.jurisdiction("FR", "France")
    ae = sd.jurisdiction("AE", "United Arab Emirates")
    eu = sd.group("EU", "European Union member states")
    bg = sd.jurisdiction("BG", "Bulgaria")
    sd.member(eu, bg, date(2007, 1, 1), Src(
        "Bulgaria — EU member country profile (european-union.europa.eu)",
        EU_URL.format("bulgaria"), None, "EU Member State: since 1 January 2007"))
    _bulgaria(sd, fr, ae, bg, eu)
    ro = sd.jurisdiction("RO", "Romania")
    sd.member(eu, ro, date(2007, 1, 1), Src(
        "Romania — EU member country profile (european-union.europa.eu)",
        EU_URL.format("romania"), None, "EU Member State: since 1 January 2007"))
    _romania(sd, fr, ae, ro, eu)
    gr = sd.jurisdiction("GR", "Greece")
    sd.member(eu, gr, date(1981, 1, 1), Src(
        "Greece — EU member country profile (european-union.europa.eu)",
        EU_URL.format("greece"), None, "EU Member State: since 1 January 1981"))
    _greece(sd, fr, ae, gr, eu)


def _bulgaria(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, bg: Jurisdiction, eu: JurisdictionGroup
) -> None:
    sd.cit(bg, date(2024, 1, 1), Src(
        BG_SRC + "; NRA corporate tax page", BG_ZKPO, "ЗКПО чл. 20",
        "Чл. 20. Данъчната ставка на корпоративния данък е 10 на сто."), rate="10")
    sd.wht(bg, "DIVIDEND", "5", date(2024, 1, 1), Src(
        BG_SRC, BG_ZKPO, "ЗКПО чл. 200(1)",
        "Данъчната ставка на данъка върху доходите по чл. 194 е 5 на сто."))
    ir = Src(BG_SRC, BG_ZKPO, "ЗКПО чл. 200(2), чл. 195(1)",
             "Данъчната ставка на данъка върху доходите по чл. 195 е 10 на сто.")
    sd.wht(bg, "INTEREST", "10", date(2024, 1, 1), ir)
    sd.wht(bg, "ROYALTY", "10", date(2024, 1, 1), ir)
    sd.exemption(
        bg, "DIVIDEND", eu, date(2024, 1, 1),
        Src(BG_SRC, BG_ZKPO, "ЗКПО чл. 194(3) т.3",
            "чуждестранно юридическо лице, което е местно лице за данъчни цели на държава - "
            "членка на Европейския съюз [...] с изключение на случаите на скрито "
            "разпределение на печалба"),
        min_holding_pct=None, min_holding_months=None, legal_ref="ЗКПО чл. 194(3)",
        description="dividends to EU/EEA companies exempt (except hidden profit distributions)",
    )
    ird = Src(BG_SRC, BG_ZKPO, "ЗКПО чл. 195(7)-(12)",
              "притежава непрекъснато за период поне две години най-малко 25 на сто от "
              "капитала")
    for cat in ("INTEREST", "ROYALTY"):
        sd.exemption(
            bg, cat, eu, date(2024, 1, 1), ird, min_holding_pct="25", min_holding_months=24,
            legal_ref="ЗКПО чл. 195(7)",
            description="Interest and Royalties Directive: associated EU company (≥25%, 2 years)",
        )
    sd.regime(
        bg, date(2024, 1, 1),
        Src(BG_SRC, BG_ZKPO, "ЗКПО чл. 27(1) т.1",
            "Не се признават за данъчни цели [...] приходи в резултат на разпределение на "
            "дивиденти от местни юридически лица и от чуждестранни лица, които са местни лица "
            "за данъчни цели на държава - членка на ЕС"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=100, payer_group_id=eu.id,
        notes="Dividends from Bulgarian and EU/EEA companies exempt (no minimum holding); "
        "non-EU dividends taxed; no general capital-gains participation exemption",
    )
    sd.cfc(
        bg, date(2019, 1, 1),
        Src(BG_SRC, BG_ZKPO, "ЗКПО чл. 47в",
            "участие в над 50 на сто от правата на глас [...] капитала [...] печалбата (and "
            "foreign tax actually paid below the difference between Bulgarian tax and that tax, "
            "i.e. below half the Bulgarian tax)"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="ЗКПО чл. 47в",
        effect="Income of a >50%-controlled entity without substantive activity taxed below "
        "half the Bulgarian tax is included.",
    )

    # Entry into force: 1 May 1988 per France; 1 June 1988 per the Bulgarian NRA — the French
    # date is recorded.
    t = sd.treaty(fr, bg, name="Convention between France and Bulgaria (1987)",
                  signed=date(1987, 3, 14), in_force=date(1988, 5, 1), src=Src(
                      "Convention France–Bulgarie modifiée par la CML (impots.gouv.fr)", FR_BG,
                      None, "signée à Sofia le 14 mars 1987 [...] entrée en vigueur le 1er mai "
                      "1988 (NRA records 1 June 1988)"))
    start = date(1989, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 8", start, Src(
        "Convention France–Bulgarie (impots.gouv.fr)", FR_BG, "Article 8(2)(b)",
        "15 p. cent du montant brut des dividendes dans tous les autres cas"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 8", start, Src(
        "Convention France–Bulgarie (impots.gouv.fr)", FR_BG, "Article 8(2)(a)",
        "5 p. cent du montant brut des dividendes si le bénéficiaire effectif est une société "
        "(autre qu'une société de personnes) qui détient directement au moins 15 p. cent du "
        "capital"), max_rate="5", ownership_threshold="15")
    sd.treaty_rate(t, "INTEREST", "Article 9", start, Src(
        "Convention France–Bulgarie (impots.gouv.fr)", FR_BG, "Article 9(1)",
        "Les intérêts provenant d'un Etat contractant et payés à un résident de l'autre Etat "
        "contractant sont imposables dans cet autre Etat. (no source-State rate)"),
        exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 10", start, Src(
        "Convention France–Bulgarie (impots.gouv.fr)", FR_BG, "Article 10(2)",
        "l'impôt ainsi établi ne peut excéder 5 p. cent du montant brut des redevances."),
        max_rate="5")
    sd.ppt(t, date(2023, 1, 1), Src(
        "Convention France–Bulgarie modifiée par la CML (impots.gouv.fr)", FR_BG,
        "MLI art. 7(1)",
        "un avantage [...] ne sera pas accordé [...] s'il est raisonnable de conclure [...] que "
        "l'octroi de cet avantage était l'un des objets principaux d'un montage ou d'une "
        "transaction"))

    t = sd.treaty(bg, ae, name="Convention between Bulgaria and the UAE (2007)",
                  signed=date(2007, 6, 26), in_force=date(2008, 11, 16), src=Src(
                      "Спогодба България–ОАЕ (NRA)", BG_AE, None,
                      "ДВ, бр. 86 от 2008 г. в сила от 16 ноември 2008 г. и по отношение на "
                      "данъците - от първия ден на януари 2009 г."))
    start = date(2009, 1, 1)
    for cat, art, quote, rate in (
        ("DIVIDEND", "Article 10", "така начисленият данък няма да надвишава 5 процента от "
         "брутната сума на дивидентите", "5"),
        ("INTEREST", "Article 11", "няма да надвишава 2 процента от брутната сума на лихвите",
         "2"),
        ("ROYALTY", "Article 12", "няма да надвишава 5 процента от брутния размер на авторските "
         "и лицензионните възнаграждения", "5"),
    ):
        sd.treaty_rate(t, cat, art, start, Src(
            "Спогодба България–ОАЕ (NRA)", BG_AE, f"{art}(2)", quote), max_rate=rate)
    sd.ppt(t, date(2023, 1, 1), Src(
        "Bulgaria–UAE synthesised text with the MLI (NRA, 28.08.2026)", BG_AE, "MLI art. 7(1)",
        "облекчение [...] не се предоставя [...] ако [...] получаването на това облекчение е "
        "една от основните цели"))


def _directive_exemptions(
    sd: Seeder, j: Jurisdiction, eu: JurisdictionGroup, start: date, *, div_src: Src,
    div_months: int, ird_src: Src, ird_months: int, div_ref: str, ird_ref: str,
) -> None:
    sd.exemption(
        j, "DIVIDEND", eu, start, div_src, min_holding_pct="10", min_holding_months=div_months,
        legal_ref=div_ref,
        description=f"Parent-Subsidiary Directive: EU parent ≥10% for {div_months} months",
    )
    for cat in ("INTEREST", "ROYALTY"):
        sd.exemption(
            j, cat, eu, start, ird_src, min_holding_pct="25", min_holding_months=ird_months,
            legal_ref=ird_ref,
            description=f"Interest and Royalties Directive: associated EU company (≥25%, "
            f"{ird_months} months)",
        )


def _romania(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, ro: Jurisdiction, eu: JurisdictionGroup
) -> None:
    start = date(2026, 1, 1)
    sd.cit(ro, start, Src(
        RO_SRC, RO_CF, "Codul fiscal art. 17",
        "Cota de impozit pe profit care se aplică asupra profitului impozabil este de 16%."),
        rate="16")
    sd.wht(ro, "DIVIDEND", "16", start, Src(
        "Legea 141/2025 (MO 699/25.07.2025) amending the Fiscal Code (ANAF)", RO_L141,
        "Codul fiscal art. 224(4)(b); L141/2025 art. VII(1)(h)",
        "b) 16% pentru veniturile din dividende prevăzute la art. 223 alin. (1) lit. a); [...] "
        "se aplică veniturilor din dividende distribuite începând cu data de 1 ianuarie 2026"))
    ir = Src(RO_SRC, RO_CF, "Codul fiscal art. 224(4)(d)",
             "d) 16% în cazul oricăror altor venituri impozabile obținute din România, așa cum "
             "sunt enumerate la art. 223 alin. (1).")
    sd.wht(ro, "INTEREST", "16", start, ir)
    sd.wht(ro, "ROYALTY", "16", start, ir)
    _directive_exemptions(
        sd, ro, eu, start,
        div_src=Src(RO_SRC, RO_CF, "Codul fiscal art. 229(1)(c)",
                    "minimum 10% din capitalul social al rezidentului pe o perioadă "
                    "neîntreruptă de cel puțin un an, care se încheie la data plății "
                    "dividendului"),
        div_months=12,
        ird_src=Src(RO_SRC, RO_CF, "Codul fiscal art. 255, 258",
                    "sunt exceptate de la orice impozite [...] participare minimă directă de "
                    "25% [...] menținute pentru o perioadă neîntreruptă de cel puțin 2 ani"),
        ird_months=24, div_ref="Codul fiscal art. 229(1)(c)", ird_ref="Codul fiscal art. 255",
    )
    sd.regime(
        ro, start,
        Src(RO_SRC, RO_CF, "Codul fiscal art. 23(b), (i); art. 24",
            "o perioadă neîntreruptă de un an, minimum 10% din capitalul social [...] deține "
            "minimum 10% [...] pe o perioadă neîntreruptă de cel puțin un an"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=10, min_holding_period_months=12, subject_to_tax_condition=True,
        exempt_share_pct=100,
        notes="Dividends and share gains from EU and treaty-country companies (≥10%, 1 year, "
        "payer subject to profit tax) non-taxable",
    )
    sd.cfc(
        ro, date(2019, 1, 1),
        Src(RO_SRC, RO_CF, "Codul fiscal art. 40^5",
            "mai mult de 50% din drepturile de vot [...] este mai mic decât diferența dintre "
            "impozitul pe profit care ar fi fost perceput [...] și impozitul pe profit plătit "
            "efectiv"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="Codul fiscal art. 40^5",
        effect="Passive income of a >50%-controlled entity taxed below half the Romanian tax "
        "is included (EU/EEA substance carve-out).",
    )

    t = sd.treaty(fr, ro, name="Convention between France and Romania (1974)",
                  signed=date(1974, 9, 27), in_force=date(1975, 9, 27), src=Src(
                      "Convention France–Roumanie (impots.gouv.fr)", FR_RO, None,
                      "signée à Bucarest le 27 septembre 1974 [...] entrée en vigueur le 27 "
                      "septembre 1975"))
    for cat, art, word in (("DIVIDEND", "Article 10", "du montant brut des dividendes"),
                           ("INTEREST", "Article 11", "du montant des intérêts"),
                           ("ROYALTY", "Article 12", "du montant des redevances")):
        sd.treaty_rate(t, cat, art, date(1976, 1, 1), Src(
            "Convention France–Roumanie (impots.gouv.fr)", FR_RO, f"{art}(2)",
            f"ne peut excéder 10 p. cent {word}"), max_rate="10")
    sd.ppt(t, date(2024, 1, 1), Src(
        "Convention France–Roumanie modifiée par la CML (impots.gouv.fr)", FR_RO,
        "MLI art. 7(1)",
        "un avantage au titre de celle-ci ne sera pas accordé [...] s'il est raisonnable de "
        "conclure [...] — retenues à la source à compter du 1er janvier 2024"))

    t = sd.treaty(ro, ae, name="Agreement between Romania and the UAE (2015)",
                  signed=date(2015, 5, 4), in_force=date(2016, 12, 11), src=Src(
                      "MLI position of Romania — instrument of deposit (OECD)",
                      "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/"
                      "beps-mli/beps-mli-position-romania-instrument-deposit.pdf", None,
                      "United Arab Emirates Original 04-05-2015 11-12-2016"))
    for cat, art in (("DIVIDEND", "Article 10"), ("INTEREST", "Article 11"),
                     ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, date(2017, 1, 1), Src(
            "Romania withholding taxes (PwC Worldwide Tax Summaries — secondary source)",
            "https://taxsummaries.pwc.com/romania/corporate/withholding-taxes", art,
            "United Arab Emirates 0/3 (0% for governments and government-owned companies; 3% "
            "otherwise — official treaty text not retrieved)"), max_rate="3")


def _greece(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, gr: Jurisdiction, eu: JurisdictionGroup
) -> None:
    start = date(2021, 1, 1)
    sd.cit(gr, start, Src(
        GR_SRC, GR_KFE.format(58), "ΚΦΕ άρθρο 58(1)",
        "Για τα εισοδήματα του φορολογικού έτους 2021 και εφεξής ο συντελεστής του "
        "προηγούμενου εδαφίου μειώνεται σε είκοσι δύο τοις εκατό (22%)."), rate="22")
    for cat, rate, quote in (
        ("DIVIDEND", "5", "α) για μερίσματα πέντε τοις εκατό (5%)."),
        ("INTEREST", "15", "β) για τόκους δεκαπέντε τοις εκατό (15%)"),
        ("ROYALTY", "20", "γ) για δικαιώματα (royalties) και λοιπές πληρωμές είκοσι τοις εκατό "
         "(20%)"),
    ):
        sd.wht(gr, cat, rate, start, Src(GR_SRC, GR_KFE.format(64), "ΚΦΕ άρθρο 64(1)", quote))
    _directive_exemptions(
        sd, gr, eu, start,
        div_src=Src(GR_SRC, GR_KFE.format(63), "ΚΦΕ άρθρο 63(1)",
                    "δεν παρακρατείται καθόλου φόρος από μερίσματα [...] τουλάχιστον δέκα τοις "
                    "εκατό (10%) [...] για τουλάχιστον είκοσι τέσσερις (24) μήνες"),
        div_months=24,
        ird_src=Src(GR_SRC, GR_KFE.format(63), "ΚΦΕ άρθρο 63(2)",
                    "δεν παρακρατείται φόρος από τόκους και δικαιώματα [...] τουλάχιστον είκοσι "
                    "πέντε τοις εκατό (25%) [...] τουλάχιστον είκοσι τέσσερις (24) μήνες"),
        ird_months=24, div_ref="ΚΦΕ άρθρο 63(1)", ird_ref="ΚΦΕ άρθρο 63(2)",
    )
    sd.regime(
        gr, start,
        Src(GR_SRC, GR_KFE.format(48), "ΚΦΕ άρθρο 48, 48Α",
            "ελάχιστο ποσοστό συμμετοχής τουλάχιστον δέκα τοις εκατό (10%) [...] διακρατείται "
            "τουλάχιστον είκοσι τέσσερεις (24) μήνες — non-EU payers exempt if not in a "
            "non-cooperative state and subject to corporate tax (art. 48(7))"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=10, min_holding_period_months=24, subject_to_tax_condition=True,
        exempt_share_pct=100,
        notes="Dividends and share gains exempt at ≥10% for 24 months (EU and non-EU payers "
        "subject to tax, not in a non-cooperative state)",
    )
    sd.cfc(
        gr, start,
        Src(GR_SRC, GR_KFE.format(66), "ΚΦΕ άρθρο 66",
            "ποσοστό άνω του πενήντα τοις εκατό (50%) των δικαιωμάτων ψήφου [...] ο πραγματικός "
            "εταιρικός φόρος [...] είναι μικρότερος από τη διαφορά"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="ΚΦΕ άρθρο 66",
        effect="Passive income (>30%) of a >50%-controlled entity taxed below half the Greek "
        "tax is included (EU/EEA substance carve-out).",
    )

    t = sd.treaty(fr, gr, name="Convention between France and Greece (2022)",
                  signed=date(2022, 5, 11), in_force=date(2023, 12, 30), src=Src(
                      "Φ.0544/Μ.7537/ΑΣ 1130, ΦΕΚ Α' 6/17-01-2024 (taxheaven.gr reproduction)",
                      "https://www.taxheaven.gr/circulars/45915/f-0544-m-7537-as-1130-2024",
                      None, "υπογράφηκε στην Αθήνα, στις 11 Μαΐου 2022, και κυρώθηκε με τον ν. "
                      "4984/2022 (Α' 202), τέθηκε σε ισχύ την 30ή Δεκεμβρίου 2023"))
    start = date(2024, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Grèce 2022 (impots.gouv.fr)", FR_GR, "Article 10(2)(b)",
        "b) ne peut excéder 15 pour cent du montant brut des dividendes"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Grèce 2022 (impots.gouv.fr)", FR_GR, "Article 10(2)(a)",
        "société qui détient directement au moins 5 pour cent du capital [...] pendant une "
        "période de 24 mois incluant la date du paiement (taxable only in the residence "
        "State)"), exclusive=True, ownership_threshold="5", min_holding_days=730)
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            "Convention France–Grèce 2022 (impots.gouv.fr)", FR_GR, f"{art}(2)",
            "ne peut excéder 5 pour cent du montant brut"), max_rate="5")
    sd.ppt(t, start, Src(
        "Convention France–Grèce 2022 (ν. 4984/2022, taxheaven.gr)",
        "https://www.taxheaven.gr/law/4984/2022", "Article 27",
        "ένας από τους κύριους σκοπούς οποιασδήποτε διευθέτησης ή συναλλαγής"))

    # Greece–UAE (2010, protocol 2013): its 10-year term was continued by an exchange of notes
    # in force 18 Sep 2025; the original entry-into-force date is unverified, so the treaty is
    # recorded from the continuation. MLI coverage unverified (no PPT row).
    t = sd.treaty(gr, ae, name="Agreement between Greece and the UAE (2010, continued 2025)",
                  signed=date(2010, 1, 18), in_force=date(2025, 9, 18), src=Src(
                      "Φ.0544/Μ.7859/ΑΣ 54065/2025, ΦΕΚ Α' 172/07-10-2025 (taxheaven.gr "
                      "reproduction)",
                      "https://www.taxheaven.gr/circulars/51302/f-0544-m-7859-as54065-24-09-2025",
                      None, "συνήφθη δια της ανταλλαγής Ρηματικών Διακοινώσεων στην Αθήνα την 2α "
                      "Μαΐου 2025 και κυρώθηκε με τον ν. 5228/2025 (Α' 156), τέθηκε σε ισχύ την "
                      "18η Σεπτεμβρίου 2025."))
    start = date(2025, 9, 18)
    for cat, art, rate, quote in (
        ("DIVIDEND", "10", "5", "δεν υπερβαίνει το 5% του ακαθάριστου ποσού των μερισμάτων"),
        ("INTEREST", "11", "5", "δεν υπερβαίνει το 5% (πέντε τοις εκατό) του ακαθάριστου ποσού "
         "των τόκων"),
        ("ROYALTY", "12", "10", "δεν μπορεί να υπερβαίνει το 10% (δέκα τοις εκατό) του "
         "ακαθάριστου ποσού των δικαιωμάτων"),
    ):
        sd.treaty_rate(t, cat, f"Article {art}", start, Src(
            "Συμφωνία Ελλάδας–ΗΑΕ, ν. 4234/2014 (taxheaven.gr — secondary)", GR_AE.format(art),
            f"Article {art}(2)", quote), max_rate=rate)
