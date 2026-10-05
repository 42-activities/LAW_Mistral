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
RIKSDAGEN = (
    "https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/"
)
SE_IL = RIKSDAGEN + "inkomstskattelag-19991229_sfs-1999-1229/"
SE_KUPL = RIKSDAGEN + "kupongskattelag-1970624_sfs-1970-624/"
FR_SE = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/suede/"
    "suede_convention-avec-la-suede-impot-sur-le-revenu-impot-sur-la-fortune_fd_2112.pdf"
)
SE_FR_PROT = RIKSDAGEN + "lag-1991673-om-dubbelbeskattningsavtal-mellan_sfs-1991-673/"
DK_SEL = "https://www.retsinformation.dk/eli/lta/2025/279/pdf"
DK_KSL = "https://www.retsinformation.dk/eli/lta/2024/460/pdf"
DK_ABL = "https://www.retsinformation.dk/eli/lta/2026/849/pdf"
FR_DK = "https://www.retsinformation.dk/eli/ltc/2023/6/pdf"
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
    se = sd.jurisdiction("SE", "Sweden")
    sd.member(eu, se, date(1995, 1, 1), Src(
        "Sweden — EU member country profile (european-union.europa.eu)",
        EU_URL.format("sweden"), None, "EU Member State: since 1 January 1995"))
    _sweden(sd, fr, se, eu)
    dk = sd.jurisdiction("DK", "Denmark")
    sd.member(eu, dk, date(1973, 1, 1), Src(
        "Denmark — EU member country profile (european-union.europa.eu)",
        EU_URL.format("denmark"), None, "EU Member State: since 1 January 1973"))
    _denmark(sd, fr, dk, eu)
    # Neither Sweden nor Denmark has an income tax treaty with the UAE (TIEAs only).


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


def _sweden(sd: Seeder, fr: Jurisdiction, se: Jurisdiction, eu: JurisdictionGroup) -> None:
    il = "Inkomstskattelag (1999:1229), t.o.m. SFS 2026:1393 (riksdagen.se)"
    sd.cit(se, date(2021, 1, 1), Src(
        il, SE_IL, "IL 65 kap. 10 §",
        "10 § För juridiska personer är den statliga inkomstskatten 20,6 procent av den "
        "beskattningsbara inkomsten."), rate="20.6")
    kupl = "Kupongskattelag (1970:624), t.o.m. SFS 2026:840 (riksdagen.se)"
    sd.wht(se, "DIVIDEND", "30", date(2021, 1, 1), Src(
        kupl, SE_KUPL, "KupL 5 §", "5 § Kupongskatt utgår med trettio procent av utdelningen."))
    sd.wht(se, "INTEREST", "0", date(2021, 1, 1), Src(
        il, SE_IL, "IL 6 kap. 11 §",
        "[Summary — no single clause to quote] Interest is not among the income for which "
        "foreign companies are liable to Swedish tax (IL 6 kap. 11 §)."))
    sd.wht(se, "ROYALTY", "20.6", date(2021, 1, 1), Src(
        il, SE_IL, "IL 6 kap. 11 § andra stycket",
        "Ersättning i form av royalty [...] ska anses som inkomst från ett fast driftställe i "
        "Sverige, om ersättningen kommer från en näringsverksamhet med ett fast driftställe "
        "här. (taxed by assessment at 20.6%, not withheld)"))
    sd.exemption(
        se, "DIVIDEND", eu, date(2021, 1, 1),
        Src(kupl, SE_KUPL, "KupL 4 § femte stycket",
            "Skattskyldighet gäller inte heller för en juridisk person i en främmande stat som "
            "är medlem i Europeiska unionen, om den innehar 10 procent eller mer av "
            "andelskapitalet i det utdelande bolaget"),
        min_holding_pct="10", min_holding_months=None, legal_ref="KupL 4 §",
        description="EU parent with ≥10% (Directive 2011/96/EU); comparable foreign companies "
        "holding business-related shares for 1 year also qualify — not modelled",
    )
    sd.exemption(
        se, "ROYALTY", eu, date(2021, 1, 1),
        Src(il, SE_IL, "IL 6 a kap. 2-6 §§",
            "[Summary — no single clause to quote] IL 6 a kap.: royalties to an associated "
            "company in another EU state (≥25% of capital) are exempt (Directive 2003/49/EC)."),
        min_holding_pct="25", min_holding_months=None, legal_ref="IL 6 a kap.",
        description="Interest and Royalties Directive: associated EU company (≥25%)",
    )
    sd.regime(
        se, date(2021, 1, 1),
        Src(il, SE_IL, "IL 24 kap. 33, 35 §§; 25 a kap. 5 §",
            "Andelen ska vara en kapitaltillgång och uppfylla någon av följande förutsättningar: "
            "1. Andelen är inte marknadsnoterad. [...] Utdelning på en näringsbetingad andel ska "
            "inte tas upp"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Näringsbetingade andelar: unlisted shares exempt without minimum; listed shares "
        "≥10% votes (gains after 1 year)",
    )
    sd.cfc(
        se, date(2019, 1, 1),
        Src(il, SE_IL, "IL 39 a kap. 2, 5 §§",
            "andelar med tillsammans minst 25 procent av den utländska juridiska personens "
            "kapital eller röster [...] lågbeskattad om den inte beskattats eller beskattats "
            "lindrigare än den beskattning som skulle ha skett i Sverige om 55 procent av denna "
            "inkomst utgjort överskott"),
        control_threshold_pct=25, low_tax_relative_pct=55, legal_ref="IL 39 a kap.",
        effect="Income of a ≥25%-held foreign entity taxed below Swedish tax on 55% of it "
        "(≈11.33%) is taxed currently, except white-listed or genuine EEA entities.",
    )

    t = sd.treaty(fr, se, name="Convention between France and Sweden (1990)",
                  signed=date(1990, 11, 27), in_force=date(1992, 4, 1), src=Src(
                      "Convention France–Suède (impots.gouv.fr)", FR_SE, None,
                      "signée à Stockholm le 27 novembre 1990 [...] entrée en vigueur le 1er "
                      "avril 1992"))
    start = date(1992, 4, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Suède (impots.gouv.fr)", FR_SE, "Article 10(2)",
        "l'impôt ainsi établi ne peut excéder 15 p. cent du montant brut des dividendes."),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Suède (impots.gouv.fr)", FR_SE, "Article 10(2)",
        "si le bénéficiaire effectif des dividendes est une société (autre qu'une société de "
        "personnes) qui détient directement ou indirectement au moins 10 p. cent du capital "
        "[...] ces dividendes ne sont pas imposables"),
        exclusive=True, ownership_threshold="10")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            "Convention France–Suède (impots.gouv.fr)", FR_SE, f"{art}(1)",
            "ne sont imposables que dans cet autre Etat"), exclusive=True)
    sd.ppt(t, date(2027, 1, 1), Src(
        "Lag 2023:698 om ändring i lagen (1991:673) — protokoll 22 maj 2023 (riksdagen.se)",
        SE_FR_PROT, "Article 28A (protocol of 22 May 2023)",
        "Denna lag träder i kraft den 1 oktober 2026. [...] a) källskatter, på belopp som "
        "betalas eller tillgodoförs den 1 januari det år som följer närmast efter [...] "
        "ikraftträdande (PPT inserted as article 28A)"))


def _denmark(sd: Seeder, fr: Jurisdiction, dk: Jurisdiction, eu: JurisdictionGroup) -> None:
    sel = "Selskabsskatteloven, LBK nr 279 af 13/03/2025 (retsinformation.dk)"
    sd.cit(dk, date(2016, 1, 1), Src(
        sel, DK_SEL, "SEL §17(1)",
        "(selskabsskatten) beregnes af den skattepligtige indkomst og udgør 22 pct."),
        rate="22")
    sd.wht(dk, "DIVIDEND", "22", date(2016, 1, 1), Src(
        sel, DK_SEL, "SEL §2(8); KSL §65(1)",
        "Indkomstskatten i medfør af stk. 1, litra c, udgør 22 pct. af de samlede udbytter "
        "(27% is withheld and the excess 5 points reclaimed)"))
    sd.wht(dk, "INTEREST", "22", date(2016, 1, 1), Src(
        sel, DK_SEL, "SEL §2(1)(d), §2(8); KSL §65 D",
        "Indkomstskatten i medfør af stk. 1, litra d og h, udgør 22 pct. af renterne og "
        "kursgevinsterne. (controlled debt only; exempt if the recipient's tax is at least 3/4 "
        "of Danish tax — not modelled)"))
    sd.wht(dk, "ROYALTY", "22", date(2016, 1, 1), Src(
        sel, DK_SEL, "SEL §2(1)(g), §2(8); KSL §65 C",
        "Indkomstskatten i henhold til stk. 1, litra g, udgør 22 pct. af royaltybeløbet."))
    sd.exemption(
        dk, "DIVIDEND", eu, date(2016, 1, 1),
        Src(sel, DK_SEL, "SEL §2(1)(c); ABL §4 A",
            "Skattepligten omfatter ikke udbytte af datterselskabsaktier [...] når beskatningen "
            "af udbytter fra datterselskabet skal frafaldes eller nedsættes efter [...] "
            "direktiv 2011/96/EU"),
        min_holding_pct="10", min_holding_months=None, legal_ref="SEL §2(1)(c)",
        description="Subsidiary shares (≥10%) where the Parent-Subsidiary Directive applies",
    )
    for cat in ("INTEREST", "ROYALTY"):
        sd.exemption(
            dk, cat, eu, date(2016, 1, 1),
            Src(sel, DK_SEL, "SEL §2(1)(d), (g)",
                "[Summary — no single clause to quote] Interest and royalties to an associated "
                "EU company are exempt under Directive 2003/49/EC where the companies have "
                "been associated for at least one year."),
            min_holding_pct="25", min_holding_months=12, legal_ref="SEL §2(1)(d), (g)",
            description="Interest and Royalties Directive: associated EU company (1 year)",
        )
    sd.regime(
        dk, date(2016, 1, 1),
        Src("Aktieavancebeskatningsloven, LBK nr 849 af 21/09/2026 (retsinformation.dk)",
            DK_ABL, "ABL §4 A, §8; SEL §13(1)(2)",
            "aktier, som ejes af et selskab, der ejer mindst 10 pct. af aktiekapitalen i "
            "datterselskabet [...] Gevinst og tab ved afståelse af datterselskabsaktier [...] "
            "medregnes ikke"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=10, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Subsidiary (≥10%) and group shares: dividends and gains exempt; Danish CFC "
        "rules (SEL §32) have no low-tax test — not seeded",
    )

    t = sd.treaty(fr, dk, name="Convention between France and Denmark (2022)",
                  signed=date(2022, 2, 4), in_force=date(2023, 12, 29), src=Src(
                      "Bekendtgørelse BKI nr 6 af 28/12/2023 (retsinformation.dk)", FR_DK,
                      None, "Overenskomsten træder i medfør af artikel 31 i kraft den 29. "
                      "december 2023."))
    start = date(2024, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Overenskomst Danmark–Frankrig (retsinformation.dk)", FR_DK, "Article 10(2)(b)",
        "15 pct. af udbyttets bruttobeløb i alle andre tilfælde"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Overenskomst Danmark–Frankrig (retsinformation.dk)", FR_DK, "Article 10(2)(a)",
        "0 pct. af udbyttets bruttobeløb, hvis den retmæssige ejer er et selskab, som i en "
        "uafbrudt periode på 365 dage [...] direkte ejer mindst 10 pct."),
        exclusive=True, ownership_threshold="10", min_holding_days=365)
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            "Overenskomst Danmark–Frankrig (retsinformation.dk)", FR_DK, f"{art}(1)",
            "kan kun beskattes i denne anden stat"), exclusive=True)
    sd.ppt(t, start, Src(
        "Overenskomst Danmark–Frankrig (retsinformation.dk)", FR_DK, "Article 29",
        "et af hovedformålene med noget arrangement eller nogen transaktion"))
