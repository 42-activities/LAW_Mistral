"""P8 batch 5: Poland, Hungary, Sweden, Denmark.

Figures were sourced on 2026-10-05 from the official texts cited on each `Src` and are stored
as `unreviewed` until a named reviewer confirms them (spec §10). Research notes:
docs/superpowers/plans/2026-10-05-p8-batch5.md.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import JurisdictionGroup
from app.modules.seed.builder import Seeder, Src

EU_URL = "https://european-union.europa.eu/principles-countries-history/eu-countries/{}_en"
PL_CIT = "https://api.sejm.gov.pl/eli/acts/DU/2026/554/text.pdf"
FR_PL = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/pologne/"
    "convention_avec_la_pologne_modifiee_par_la_cml.pdf"
)
PL_TREATIES = (
    "https://podatki.gov.pl/podatkowa-wspolpraca-miedzynarodowa/"
    "wykaz-umow-o-unikaniu-podwojnego-opodatkowania"
)
PL_AE = "https://podatki.gov.pl/media/0nfb2cob/dta-pl-uae-mli-synthesised-text-en.pdf"
HU_TAO = "https://net.jogtar.hu/jogszabaly?docid=99600081.tv"
HU_CONS = " (net.jogtar.hu consolidation — njt.hu unreachable)"
FR_HU = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/hongrie/"
    "hongrie_convention_modifiee_cml.pdf"
)
HU_AE = "https://net.jogtar.hu/jogszabaly?docid=a1300161.tv"
HU_AE_MLI = (
    "https://ngmszakmaiteruletek.kormany.hu/akadalymentes/download/5/b5/f2000/"
    "UAE_synthesised%20text.pdf"
)


def seed_batch5(session: Session) -> None:
    sd = Seeder(session)
    fr = sd.jurisdiction("FR", "France")
    ae = sd.jurisdiction("AE", "United Arab Emirates")
    eu = sd.group("EU", "European Union member states")
    pl = sd.jurisdiction("PL", "Poland")
    sd.member(eu, pl, date(2004, 5, 1), Src(
        "Poland — EU member country profile (european-union.europa.eu)",
        EU_URL.format("poland"), None, "EU Member State: since 1 May 2004"))
    _poland(sd, fr, ae, pl, eu)
    hu = sd.jurisdiction("HU", "Hungary")
    sd.member(eu, hu, date(2004, 5, 1), Src(
        "Hungary — EU member country profile (european-union.europa.eu)",
        EU_URL.format("hungary"), None, "EU Member State: since 1 May 2004"))
    _hungary(sd, fr, ae, hu)


def _poland(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, pl: Jurisdiction, eu: JurisdictionGroup
) -> None:
    cit_act = "Ustawa o podatku dochodowym od osób prawnych, Dz.U. 2026 poz. 554 (Sejm ELI)"
    sd.cit(pl, date(2026, 1, 1), Src(
        cit_act, PL_CIT, "CIT Act art. 19(1)(1)",
        "Podatek [...] wynosi: 1) 19 % podstawy opodatkowania"), rate="19")
    sd.wht(pl, "DIVIDEND", "19", date(2026, 1, 1), Src(
        cit_act, PL_CIT, "CIT Act art. 22(1)",
        "dywidend oraz innych przychodów [...] ustala się w wysokości 19 % uzyskanego przychodu "
        "(dochodu)"))
    ir = Src(
        cit_act, PL_CIT, "CIT Act art. 21(1)(1)",
        "z odsetek, z praw autorskich [...] (know-how) [...] – ustala się w wysokości 20 % "
        "przychodów")
    sd.wht(pl, "INTEREST", "20", date(2026, 1, 1), ir)
    sd.wht(pl, "ROYALTY", "20", date(2026, 1, 1), ir)
    sd.exemption(
        pl, "DIVIDEND", eu, date(2026, 1, 1),
        Src(cit_act, PL_CIT, "CIT Act art. 22(4)",
            "posiada bezpośrednio niemniej niż 10 % udziałów (akcji) [...] nieprzerwanie przez "
            "okres dwóch lat"),
        min_holding_pct="10", min_holding_months=24, legal_ref="CIT Act art. 22(4)",
        description="Parent-Subsidiary Directive: EU/EEA parent ≥10% for 2 years "
        "(pay-and-refund above PLN 2m to related parties — not modelled)",
    )
    ird = Src(
        cit_act, PL_CIT, "CIT Act art. 21(3)",
        "posiada bezpośrednio niemniej niż 25 % udziałów (akcji) [...] nieprzerwanie przez "
        "okres dwóch lat")
    for cat in ("INTEREST", "ROYALTY"):
        sd.exemption(
            pl, cat, eu, date(2026, 1, 1), ird, min_holding_pct="25", min_holding_months=24,
            legal_ref="CIT Act art. 21(3)",
            description="Interest and Royalties Directive: associated EU/EEA company (≥25%, "
            "2 years)",
        )
    sd.regime(
        pl, date(2026, 1, 1),
        Src(cit_act, PL_CIT, "CIT Act art. 20(3)",
            "posiada bezpośrednio niemniej niż 10 % udziałów (akcji) [...] nieprzerwanie przez "
            "okres dwóch lat"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=10, min_holding_period_months=24, subject_to_tax_condition=False,
        exempt_share_pct=100, payer_group_id=eu.id,
        notes="Dividends from EU/EEA subsidiaries (≥10%, 2 years) exempt; non-EU treaty "
        "subsidiaries: credit only (indirect credit at ≥75%); holding-company regime "
        "(art. 24m-24p) not modelled",
    )
    sd.cfc(
        pl, date(2026, 1, 1),
        Src(cit_act, PL_CIT, "CIT Act art. 24a(3)(3)",
            "faktycznie zapłacony podatek dochodowy przez tę jednostkę jest niższy o co "
            "najmniej 25 % od podatku dochodowego od osób prawnych, który byłby od niej "
            "należny"),
        control_threshold_pct=50, low_tax_relative_pct=75, threshold_inclusive=True,
        legal_ref="CIT Act art. 24a",
        effect="Income of a >50%-controlled entity with ≥33% passive revenue and tax at least "
        "25% lower than Polish CIT is taxed at 19%.",
    )

    t = sd.treaty(fr, pl, name="Convention between France and Poland (1975)",
                  signed=date(1975, 6, 20), in_force=date(1976, 9, 12), src=Src(
                      "Convention France–Pologne modifiée par la CML (impots.gouv.fr)", FR_PL,
                      None, "signée à Varsovie le 20 juin 1975 [...] entrée en vigueur le 12 "
                      "septembre 1976"))
    start = date(2020, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Pologne modifiée par la CML (impots.gouv.fr)", FR_PL,
        "Article 10(2)(b)", "15 p. cent du montant brut des dividendes, dans tous les autres "
        "cas"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Pologne modifiée par la CML (impots.gouv.fr)", FR_PL,
        "Article 10(2)(a); MLI art. 8",
        "5 p. cent du montant brut des dividendes si le bénéficiaire est une société [...] qui "
        "détient directement au moins 10 p. cent du capital [...] tout au long d'une période "
        "de 365 jours"), max_rate="5", ownership_threshold="10", min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Convention France–Pologne modifiée par la CML (impots.gouv.fr)", FR_PL,
        "Article 11(1)", "ne sont imposables que dans cet autre Etat"), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Convention France–Pologne modifiée par la CML (impots.gouv.fr)", FR_PL,
        "Article 12(2)", "l'impôt ainsi établi ne peut excéder 10 p. cent du montant brut des "
        "redevances"), max_rate="10")
    sd.ppt(t, start, Src(
        "Convention France–Pologne modifiée par la CML (impots.gouv.fr)", FR_PL,
        "MLI art. 7(1)",
        "un avantage au titre de celle-ci ne sera pas accordé [...] s'il est raisonnable de "
        "conclure [...] que l'octroi de cet avantage était l'un des objets principaux"),
        dividend_min_holding_days=365)

    t = sd.treaty(pl, ae, name="Agreement between Poland and the UAE (1993, protocol 2013)",
                  signed=date(1993, 1, 31), in_force=date(1994, 4, 21), src=Src(
                      "Wykaz umów o unikaniu podwójnego opodatkowania (podatki.gov.pl)",
                      PL_TREATIES, None,
                      "Zjednoczone Emiraty Arabskie: 31.01.1993, 21.04.1994, 01.01.1995; "
                      "protokół 11.12.2013, 01.05.2015, 01.01.2016"))
    start = date(2016, 1, 1)
    for cat, art, word in (("DIVIDEND", "Article 10", "dividend"),
                           ("INTEREST", "Article 11", "interest"),
                           ("ROYALTY", "Article 12", "royalties")):
        sd.treaty_rate(t, cat, art, start, Src(
            "Poland–UAE agreement, synthesised text with the MLI (podatki.gov.pl)", PL_AE,
            f"{art}(2)", f"the tax so charged shall not exceed 5% (five percent) of the gross "
            f"amount of the {word}"), max_rate="5")
    sd.ppt(t, date(2020, 1, 1), Src(
        "Poland–UAE agreement, synthesised text with the MLI (podatki.gov.pl)", PL_AE,
        "MLI art. 7(1)",
        "a benefit under [the Agreement] shall not be granted [...] if [...] obtaining that "
        "benefit was one of the principal purposes of any arrangement or transaction"))


def _hungary(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, hu: Jurisdiction) -> None:
    tao = "Act LXXXI of 1996 on corporate tax (Tao. tv.)" + HU_CONS
    sd.cit(hu, date(2019, 1, 1), Src(
        tao, HU_TAO, "Tao. tv. 19. §", "19. § A társasági adó mértéke 9 százalék."), rate="9")
    sd.wht(hu, "DIVIDEND", "0", date(2006, 1, 1), Src(
        tao, HU_TAO, "Tao. tv. 27. § (repealed)",
        "Hatályon kívül helyezte: 2005. évi CXIX. törvény 180. § (8). Hatálytalan: 2006. I. "
        "1-től. (dividend withholding tax repealed from 1 January 2006)"))
    no_wht = Src(
        "Hungary withholding taxes (PwC Worldwide Tax Summaries — secondary source)",
        "https://taxsummaries.pwc.com/hungary/corporate/withholding-taxes", None,
        "Under the domestic rules, there is no withholding tax (WHT) on dividends, interest, or "
        "royalties paid to non-individuals.")
    sd.wht(hu, "INTEREST", "0", date(2006, 1, 1), no_wht)
    sd.wht(hu, "ROYALTY", "0", date(2006, 1, 1), no_wht)
    sd.regime(
        hu, date(2020, 11, 27),
        Src(tao, HU_TAO, "Tao. tv. 7. § (1) g), dz); 4. § 5.",
            "az adózónál a kapott (járó) osztalék és részesedés címén 1. az adóévben nem "
            "ellenőrzött külföldi társaságtól kapott (járó) osztalék [...] (dividends from a "
            "non-CFC deducted from the pre-tax result)"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Dividends from non-CFC companies exempt; gains on announced participations "
        "(reported within 75 days, held 1 year, no % threshold) exempt; local business tax "
        "(up to 2% of the adjusted base) not modelled",
    )
    sd.cfc(
        hu, date(2019, 1, 1),
        Src(tao, HU_TAO, "Tao. tv. 4. § 11.",
            "a szavazati jogok 50 százalékát meghaladó [...] részesedéssel rendelkezik [...] "
            "ténylegesen megfizetett társasági adónak megfelelő adó kisebb, mint az a "
            "különbözet [...] (effectively below half the Hungarian tax)"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="Tao. tv. 4. § 11.",
        effect="Income of a >50%-controlled entity taxed below half the Hungarian tax from "
        "non-genuine arrangements is included.",
    )

    t = sd.treaty(fr, hu, name="Convention between France and Hungary (1980)",
                  signed=date(1980, 4, 28), in_force=date(1981, 12, 1), src=Src(
                      "Convention France–Hongrie modifiée par la CML (impots.gouv.fr)", FR_HU,
                      None, "signée à Paris le 28 avril 1980, approuvée par la loi n° 81-749 du "
                      "5 août 1981 [...], entrée en vigueur le 1er décembre 1981"))
    start = date(1981, 12, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Hongrie modifiée par la CML (impots.gouv.fr)", FR_HU,
        "Article 10(2)(b)", "b) 15 p. cent du montant brut des dividendes dans tous les autres "
        "cas."), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Hongrie modifiée par la CML (impots.gouv.fr)", FR_HU,
        "Article 10(2)(a)", "a) 5 p. cent du montant brut des dividendes si le bénéficiaire "
        "effectif est une société (autre qu'une société de personnes) qui détient directement "
        "au moins 25 p. cent du capital"), max_rate="5", ownership_threshold="25")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Convention France–Hongrie modifiée par la CML (impots.gouv.fr)", FR_HU,
        "Article 11(1)", "Les intérêts provenant d'un Etat et payés à un résident de l'autre "
        "Etat sont imposables dans cet autre Etat. (no source-State rate)"), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Convention France–Hongrie modifiée par la CML (impots.gouv.fr)", FR_HU,
        "Article 12(1)", "Les redevances [...] ne sont imposables que dans cet autre Etat, si "
        "ce résident en est le bénéficiaire effectif."), exclusive=True)
    sd.ppt(t, date(2022, 1, 1), Src(
        "Convention France–Hongrie modifiée par la CML (impots.gouv.fr)", FR_HU,
        "MLI art. 7(1)", "l'octroi de cet avantage était l'un des objets principaux d'un "
        "montage ou d'une transaction [...] à compter du 1er janvier 2022"))

    t = sd.treaty(hu, ae, name="Convention between Hungary and the UAE (2013)",
                  signed=date(2013, 4, 30), in_force=date(2014, 10, 4), src=Src(
                      "Act CLXI of 2013 promulgating the HU–UAE convention" + HU_CONS, HU_AE,
                      None, "Hatályba lép 2014. X. 4-én a 10/2014. (IX. 30.) KKM közlemény "
                      "alapján."))
    for cat, art in (("DIVIDEND", "Article 11"), ("INTEREST", "Article 12"),
                     ("ROYALTY", "Article 13")):
        sd.treaty_rate(t, cat, art, date(2015, 1, 1), Src(
            "Hungary–UAE convention" + HU_CONS, HU_AE, f"{art}(1)",
            "shall be taxable only in that other Contracting State."), exclusive=True)
    sd.ppt(t, date(2022, 1, 1), Src(
        "Hungary–UAE synthesised text with the MLI (kormany.hu)", HU_AE_MLI, "MLI art. 7(1)",
        "The following paragraph 1 of Article 7 of the MLI applies and supersedes the provisions "
        "of this Agreement [...] one of the principal purposes of any arrangement or "
        "transaction"))
