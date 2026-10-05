"""P8 batch 6: United States, Mauritius, Qatar, Czech Republic.

Figures were sourced on 2026-10-05 from the official texts cited on each `Src` and are stored
as `unreviewed` until a named reviewer confirms them (spec §10). Research notes:
docs/superpowers/plans/2026-10-05-p8-batch6.md.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import JurisdictionGroup
from app.modules.seed.builder import Seeder, Src

CORNELL = "https://www.law.cornell.edu/uscode/text/26/{}"
FR_US = "https://www.irs.gov/pub/irs-trty/france.pdf"
FR_US_2009 = "https://home.treasury.gov/system/files/131/Treaty-France-Pr2-1-13-2009.pdf"
EU_URL = "https://european-union.europa.eu/principles-countries-history/eu-countries/{}_en"
MRA = "https://www.mra.mu/download/"
MU_ITA = MRA + "ITAConsolidated.pdf"
FR_MU = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/ile_maurice/"
    "convention_avec_l_ile_maurice_modifiee_par_la_cml_v2.pdf"
)
QA_ITL = "https://gta.gov.qa/assets/pdf/Income%20Tax%20Law%20EN%202024.pdf"
FR_QA = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/qatar/"
    "qatar_convention-avec-le-qatar_fd_2100.pdf"
)
FR_QA_MLI = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/qatar/"
    "qatar_convention_modifiee_par_cml_2021-12-29.pdf"
)
CZ_ZDP = "https://www.zakonyprolidi.cz/cs/1992-586"
FR_CZ = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/republique_tcheque/"
    "version_consolidee_de_la_convention_avec_la_republique_tcheque_modifiee_par_la_"
    "convention_multilaterale.pdf"
)
CZ_AE = "https://www.zakonyprolidi.cz/cs/2024-206"


def seed_batch6(session: Session) -> None:
    sd = Seeder(session)
    fr = sd.jurisdiction("FR", "France")
    _united_states(sd, fr, sd.jurisdiction("US", "United States"))
    ae = sd.jurisdiction("AE", "United Arab Emirates")
    eu = sd.group("EU", "European Union member states")
    cz = sd.jurisdiction("CZ", "Czech Republic")
    sd.member(eu, cz, date(2004, 5, 1), Src(
        "Czechia — EU member country profile (european-union.europa.eu)",
        EU_URL.format("czechia"), None, "EU member country: since 1 May 2004"))
    _czech_republic(sd, fr, ae, cz, eu)
    _mauritius(sd, fr, ae, sd.jurisdiction("MU", "Mauritius"))
    _qatar(sd, fr, sd.jurisdiction("QA", "Qatar"))


def _united_states(sd: Seeder, fr: Jurisdiction, us: Jurisdiction) -> None:
    # Federal rate only: state income tax applies to income apportioned to the state (Delaware
    # 8.7%; holding companies often outside it) and is not modelled.
    sd.cit(us, date(2018, 1, 1), Src(
        "26 U.S.C. §11 (LII, Cornell)", CORNELL.format(11), "IRC §11(b)",
        "The amount of the tax imposed by subsection (a) shall be 21 percent of taxable "
        "income."), rate="21")
    fdap = Src(
        "26 U.S.C. §881 / §1442 (LII, Cornell)", CORNELL.format(1442), "IRC §881(a), §1442(a)",
        "there shall be deducted and withheld at the source in the same manner and on the same "
        "items of income as is provided in section 1441 a tax equal to 30 percent thereof.")
    for cat in ("DIVIDEND", "INTEREST", "ROYALTY"):
        sd.wht(us, cat, "30", date(2018, 1, 1), fdap)
    sd.regime(
        us, date(2018, 1, 1),
        Src("26 U.S.C. §245A / §246 (LII, Cornell)", CORNELL.format("245A"),
            "IRC §245A, §246(c)(5)",
            "There shall be allowed as a deduction an amount equal to the foreign-source portion "
            "of such dividend [...] by substituting '365 days' for '45 days'"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=10, min_holding_period_months=12, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="§245A: 100% DRD for the foreign-source portion of dividends from specified "
        "10%-owned foreign corporations (365 days); gains taxable; NCTI/Subpart F apply",
    )
    sd.cfc(
        us, date(2018, 1, 1),
        Src("26 U.S.C. §954 (LII, Cornell)", CORNELL.format(954), "IRC §954(b)(4)",
            "subject to an effective rate of income tax imposed by a foreign country greater "
            "than 90 percent of the maximum rate of tax specified in section 11."),
        control_threshold_pct=50, low_tax_relative_pct=90, threshold_inclusive=True,
        legal_ref="IRC §951-§954 (Subpart F); §951A (NCTI)",
        effect="Subpart F income of a CFC taxed at no more than 90% of the US rate (18.9%) is "
        "included; NCTI (former GILTI) applies to other tested income.",
    )

    t = sd.treaty(fr, us, name="Convention between France and the United States (1994)",
                  signed=date(1994, 8, 31), in_force=date(1996, 1, 1), src=Src(
                      "BOI-INT-CVB-USA-10 (BOFiP)",
                      "https://bofip.impots.gouv.fr/bofip/3063-PGP.html/"
                      "identifiant=BOI-INT-CVB-USA-10-20200219", None,
                      "Convention signée le 31 août 1994 (general effective date 1 January "
                      "1996); avenant [...] entrée en vigueur le 23 décembre 2009"))
    start = date(2009, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "France–US protocol of 13 January 2009 (US Treasury)", FR_US_2009, "Article 10(2)(b)",
        "15 percent of the gross amount of the dividends in all other cases."), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "France–US protocol of 13 January 2009 (US Treasury)", FR_US_2009, "Article 10(2)(a)",
        "5 percent of the gross amount of the dividends if the beneficial owner is a company "
        "that owns: (i) directly at least 10 percent of the voting stock of the company paying "
        "the dividends"), max_rate="5", ownership_threshold="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "France–US protocol of 13 January 2009 (US Treasury)", FR_US_2009, "Article 10(3)",
        "shall not be taxed in the Contracting State of which the company paying the dividends "
        "is a resident if the beneficial owner is a company [...] that has owned [...] shares "
        "representing 80 percent or more of the voting power [...] for a 12-month period [...] "
        "(subject to the Article 30 limitation-on-benefits tests)"),
        exclusive=True, ownership_threshold="80", min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 11", date(1996, 1, 1), Src(
        "France–US convention (IRS)", FR_US, "Article 11(1)",
        "Interest arising in a Contracting State and beneficially owned by a resident of the "
        "other Contracting State shall be taxable only in that other State."), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "France–US protocol of 13 January 2009 (US Treasury)", FR_US_2009, "Article 12(1)",
        "Royalties arising in a Contracting State and beneficially owned by a resident of the "
        "other Contracting State shall be taxable only in that other State."), exclusive=True)
    # The US is not an MLI party; access to treaty benefits is governed by the article 30
    # limitation-on-benefits clause (not modelled). There is no US–UAE income tax treaty.


def _czech_republic(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, cz: Jurisdiction, eu: JurisdictionGroup
) -> None:
    zdp = "Zákon o daních z příjmů 586/1992 Sb., znění 01.08.2026 (zakonyprolidi.cz)"
    sd.cit(cz, date(2024, 1, 1), Src(
        zdp, CZ_ZDP, "ZDP §21(1)",
        "(1) Sazba daně činí 21 %, pokud v odstavcích 2 a 3 není stanoveno jinak."), rate="21")
    roy = Src(zdp, CZ_ZDP, "ZDP §36(1)(a)",
              "a) 15 %, a to 1. z příjmů uvedených v § 22 odst. 1 písm. c), f) a g) bodech 1, 2")
    divint = Src(zdp, CZ_ZDP, "ZDP §36(1)(b)",
                 "b) 15 %, a to 1. z příjmů uvedených v § 22 odst. 1 písm. g) bodech 3 a 4")
    sd.wht(cz, "DIVIDEND", "15", date(2024, 1, 1), divint)
    sd.wht(cz, "INTEREST", "15", date(2024, 1, 1), divint)
    sd.wht(cz, "ROYALTY", "15", date(2024, 1, 1), roy)
    sd.exemption(
        cz, "DIVIDEND", eu, date(2024, 1, 1),
        Src(zdp, CZ_ZDP, "ZDP §19(1)(ze), §19(3)(b)",
            "příjmy z 1. podílu na zisku, vyplácené dceřinou společností [...] mateřské "
            "společnosti [...] nejméně po dobu 12 měsíců nepřetržitě alespoň 10% podíl na "
            "základním kapitálu"),
        min_holding_pct="10", min_holding_months=12, legal_ref="ZDP §19(1)(ze)",
        description="Parent-Subsidiary Directive: EU parent ≥10% for 12 months",
    )
    ird = Src(zdp, CZ_ZDP, "ZDP §19(1)(zj), (zk); §23(7)",
              "osobami přímo kapitálově spojenými po dobu alespoň 24 měsíců nepřetržitě [...] "
              "podíl představuje alespoň 25 % základního kapitálu nebo 25 % hlasovacích práv")
    for cat in ("INTEREST", "ROYALTY"):
        sd.exemption(
            cz, cat, eu, date(2024, 1, 1), ird, min_holding_pct="25", min_holding_months=24,
            legal_ref="ZDP §19(1)(zj)-(zk)",
            description="Interest and Royalties Directive: associated EU company (≥25%, 24 "
            "months; tax authority decision required)",
        )
    sd.regime(
        cz, date(2024, 1, 1),
        Src(zdp, CZ_ZDP, "ZDP §19(1)(zi), (ze) bod 2, §19(9)",
            "příjmy z podílu na zisku, plynoucí od dceřiné společnosti, která je daňovým "
            "rezidentem jiného členského státu [...] podléhá dani obdobné dani z příjmů "
            "právnických osob, u níž sazba daně není nižší než 12 %"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=10, min_holding_period_months=12, subject_to_tax_condition=True,
        min_subject_to_tax_rate=12, exempt_share_pct=100,
        notes="EU subsidiaries and treaty-country subsidiaries taxed ≥12% (≥10%, 12 months): "
        "dividends and gains exempt",
    )
    sd.cfc(
        cz, date(2019, 1, 1),
        Src(zdp, CZ_ZDP, "ZDP §38fa",
            "daň [...] je nižší než polovina daně, která by jí byla stanovena, pokud by byla "
            "daňovým rezidentem České republiky [...] z více než 50 %"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="ZDP §38fa",
        effect="Income of a >50%-controlled company without substantial activity taxed below "
        "half the Czech tax is included (EU-listed jurisdictions always).",
    )

    t = sd.treaty(fr, cz, name="Convention between France and the Czech Republic (2003)",
                  signed=date(2003, 4, 28), in_force=date(2005, 7, 1), src=Src(
                      "Convention France–République tchèque modifiée par la CML (impots.gouv.fr)",
                      FR_CZ, None, "signée à Prague le 28 avril 2003, approuvée par la loi n° "
                      "2005-226 du 14 mars 2005 [...], entrée en vigueur le 1er juillet 2005"))
    start = date(2006, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–République tchèque (impots.gouv.fr)", FR_CZ, "Article 10(2)(b)",
        "b) 10 % du montant brut des dividendes dans tous les autres cas."), max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–République tchèque (impots.gouv.fr)", FR_CZ, "Article 10(2)(a)",
        "a) 0 % du montant brut des dividendes si le bénéficiaire effectif est une société qui "
        "détient directement au moins 25 % du capital"),
        exclusive=True, ownership_threshold="25")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Convention France–République tchèque (impots.gouv.fr)", FR_CZ, "Article 11(1)",
        "Les intérêts provenant d'un Etat contractant et dont le bénéficiaire effectif est un "
        "résident de l'autre Etat contractant ne sont imposables que dans cet autre Etat."),
        exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Convention France–République tchèque (impots.gouv.fr)", FR_CZ, "Article 12(2)(b)",
        "b) 10 % du montant brut des redevances pour les rémunérations visées à l'alinéa c du "
        "paragraphe 3 (patents, trademarks, software, know-how; 5% equipment, 0% copyright)"),
        max_rate="10")
    sd.ppt(t, date(2021, 1, 1), Src(
        "Convention France–République tchèque modifiée par la CML (impots.gouv.fr)", FR_CZ,
        "MLI art. 7(1)",
        "un avantage [...] ne sera pas accordé [...] s'il est raisonnable de conclure [...] "
        "que l'octroi de cet avantage était l'un des objets principaux d'un montage ou d'une "
        "transaction"))

    t = sd.treaty(cz, ae, name="Agreement between the Czech Republic and the UAE (2023)",
                  signed=date(2023, 5, 24), in_force=date(2024, 5, 29), src=Src(
                      "Smlouva ČR–SAE, 206/2024 Sb. (zakonyprolidi.cz)", CZ_AE, None,
                      "dne 24. května 2023 byla v Praze podepsána Smlouva [...] Smlouva "
                      "vstoupila v platnost [...] dne 29. května 2024"))
    start = date(2025, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 11", start, Src(
        "Smlouva ČR–SAE, 206/2024 Sb. (zakonyprolidi.cz)", CZ_AE, "Article 11(2)",
        "daň takto uložená nepřesáhne 5 procent hrubé částky dividend"), max_rate="5")
    sd.treaty_rate(t, "INTEREST", "Article 12", start, Src(
        "Smlouva ČR–SAE, 206/2024 Sb. (zakonyprolidi.cz)", CZ_AE, "Article 12(1)",
        "podléhají zdanění jen v tomto druhém státě"), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 13", start, Src(
        "Smlouva ČR–SAE, 206/2024 Sb. (zakonyprolidi.cz)", CZ_AE, "Article 13(2)",
        "nepřesáhne 10 procent hrubé částky licenčních poplatků"), max_rate="10")
    sd.ppt(t, start, Src(
        "Smlouva ČR–SAE, 206/2024 Sb. (zakonyprolidi.cz)", CZ_AE, "Article 27(1)",
        "získání výhody plynoucí ze Smlouvy bylo jedním z hlavních cílů jakéhokoliv opatření "
        "nebo jakékoliv transakce [...] tato výhoda [...] nebude poskytnuta"))


def _mauritius(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, mu: Jurisdiction) -> None:
    ita = "Income Tax Act 1995, consolidated up to May 2026 (MRA)"
    sd.cit(mu, date(2019, 7, 1), Src(
        ita, MU_ITA, "ITA s.44; First Schedule Part IV",
        "every company shall be liable to income tax on its chargeable income at the rate "
        "specified in Part IV of the First Schedule. [...] PART IV Rate of income tax 15 per "
        "cent"), rate="15")
    # 80% partial exemption of interest (with substance) → 3% effective on interest income.
    sd.cit(mu, date(2019, 7, 1), Src(
        ita, MU_ITA, "ITA Second Schedule Part II Sub-Part B item 7; reg. 23D",
        "80 per cent of interest derived by a company other than – (i) a bank [...] (15% on the "
        "remaining 20% = 3%, subject to the reg. 23D substance conditions)"),
        rate="3", category="INTEREST")
    sd.wht(mu, "DIVIDEND", "0", date(2019, 7, 1), Src(
        ita, MU_ITA, "ITA s.111B",
        "[Summary — no single clause to quote] Dividends are not among the payments subject "
        "to withholding under ITA s.111B (a)-(n) or the Sixth Schedule."))
    sd.wht(mu, "INTEREST", "15", date(2019, 7, 1), Src(
        ita, MU_ITA, "ITA s.111B(a), Sixth Schedule item 1",
        "Interest payable by any person, other than by a bank or non-bank deposit taking "
        "institution [...] to any person, other than a company resident in Mauritius 15 "
        "(exempt when paid by a GBL company out of foreign source income)"))
    sd.wht(mu, "ROYALTY", "15", date(2019, 7, 1), Src(
        ita, MU_ITA, "ITA s.111B(b), Sixth Schedule item 2(b)",
        "Royalties payable to - (a) a resident (b) a non-resident 10 15"))
    sd.regime(
        mu, date(2019, 7, 1),
        Src(ita, MU_ITA, "ITA Second Schedule Part II Sub-Part B items 1, 6",
            "80 per cent of foreign source dividend derived by a company, other than a bank "
            "[...] provided – (i) the dividend has not been allowed as a deduction in the "
            "country of source; (ii) the company satisfies the conditions relating to the "
            "substance"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=80,
        notes="Foreign dividends 80% exempt (3% effective) with substance; no credit if the "
        "exemption is claimed; Fair Share Contribution (5% above MUR 24m, 2025-2028) and the "
        "10% alternative minimum tax (from YA 2026/27) not modelled",
    )
    sd.cfc(
        mu, date(2020, 7, 1),
        Src(ita, MU_ITA, "ITA s.90A",
            "in which more than 50 per cent of its total participation rights are held [...] "
            "(iii) the tax rate in the country of residence [...] is more than 50 per cent of "
            "the tax rate in Mauritius (exclusion)"),
        control_threshold_pct=50, low_tax_relative_pct=50, threshold_inclusive=True,
        legal_ref="ITA s.90A",
        effect="Undistributed income from non-genuine arrangements of a >50% CFC taxed at no "
        "more than half the Mauritian rate is included.",
    )

    t = sd.treaty(fr, mu, name="Convention between France and Mauritius (1980, as amended)",
                  signed=date(1980, 12, 11), in_force=date(1982, 9, 17), src=Src(
                      "Convention France–Maurice modifiée par la CML (impots.gouv.fr)", FR_MU,
                      None, "signée à Port-Louis le 11 décembre 1980 [...] entrée en vigueur le "
                      "17 septembre 1982 [...] modifiée par l'Avenant signé le 23 juin 2011 "
                      "[...] entré en vigueur le 1er mai 2012"))
    start = date(2012, 5, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Maurice modifiée par la CML (impots.gouv.fr)", FR_MU,
        "Article 10(2)(b)", "b) 15 p. cent du montant brut des dividendes, dans tous les autres "
        "cas."), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Maurice modifiée par la CML (impots.gouv.fr)", FR_MU,
        "Article 10(2)(a)", "a) 5 p. cent du montant brut des dividendes si le bénéficiaire "
        "effectif est une société [...] qui détient directement au moins 10 p. cent du "
        "capital"), max_rate="5", ownership_threshold="10")
    # Interest (art. 11): taxable at source under domestic law — no treaty cap recorded.
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Convention France–Maurice modifiée par la CML (impots.gouv.fr)", FR_MU,
        "Article 12(2)", "l'impôt ainsi établi ne peut excéder 15 p. cent du montant brut des "
        "redevances."), max_rate="15")
    sd.ppt(t, date(2021, 1, 1), Src(
        "Convention France–Maurice modifiée par la CML (impots.gouv.fr)", FR_MU,
        "MLI art. 7(1)",
        "un avantage au titre de la présente Convention ne sera pas accordé [...] s'il est "
        "raisonnable de conclure [...] que l'octroi de cet avantage était l'un des objets "
        "principaux d'un montage"))

    # Entry into force: secondary sources give 31 Jul or 25 Sep 2007; either way art. 28 makes
    # it apply in Mauritius from income years beginning 1 July 2008. MLI effective dates for
    # this treaty were not confirmed, so no PPT row is recorded.
    t = sd.treaty(mu, ae, name="Convention between Mauritius and the UAE (2006)",
                  signed=date(2006, 9, 18), in_force=date(2007, 9, 25), src=Src(
                      "UAE/Mauritius double taxation convention, GN 14 of 2007 (MRA)",
                      MRA + "RegulationsUAE.pdf", None,
                      "UAE/MAURITIUS DOUBLE TAXATION CONVENTION SIGNED 18 September 2006 "
                      "(entry into force 2007 per secondary sources; applies from 1 July 2008)"))
    for cat, art in (("DIVIDEND", "Article 10"), ("INTEREST", "Article 11"),
                     ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, date(2008, 7, 1), Src(
            "UAE–Mauritius convention, synthesised text (MRA)",
            MRA + "UnitedArabEmiratesSynthesised.pdf", f"{art}(1)",
            "if the recipient is the beneficial owner [...] be taxable only in that other "
            "State."), exclusive=True)


def _qatar(sd: Seeder, fr: Jurisdiction, qa: Jurisdiction) -> None:
    itl = "Income Tax Law No. 24 of 2018 and Executive Regulations, 2024 edition (GTA)"
    # 10% applies to the share of profits attributable to non-Qatari/non-GCC owners; the
    # Qatari/GCC-owned share is exempt (art. 4) — a foreign-owned holding is assumed here.
    sd.cit(qa, date(2019, 1, 1), Src(
        itl, QA_ITL, "ITL art. 9; art. 4(14)-(15)",
        "The tax rate is 10% of the taxable income of the taxpayer during the tax year. "
        "(Qatari- and GCC-owned shares of profit exempt; 35% minimum for petroleum)"),
        rate="10")
    wht = Src(
        itl, QA_ITL, "ITL art. 9(2); ER art. 21",
        "Subject to the provisions of tax agreements, a final withholding tax of 5% of the "
        "gross amount applies to royalties, interest, commissions, and payments for services "
        "[...] paid to non-residents")
    sd.wht(qa, "INTEREST", "5", date(2019, 1, 1), wht)
    sd.wht(qa, "ROYALTY", "5", date(2019, 1, 1), wht)
    sd.wht(qa, "DIVIDEND", "0", date(2019, 1, 1), Src(
        itl, QA_ITL, "ITL art. 9(2)",
        "[Summary — no single clause to quote] ITL art. 9(2) lists royalties, interest, "
        "commissions and services only; dividends to non-residents are not subject to "
        "withholding."))
    # No participation-exemption regime is recorded: art. 4(8) exempts dividends paid out of
    # profits taxed under Qatari law, and its application to foreign dividends is not settled
    # in the sources fetched — the engine treats them as taxable and flags it. No CFC rules.

    t = sd.treaty(fr, qa, name="Convention between France and Qatar (1990, as amended 2008)",
                  signed=date(1990, 12, 4), in_force=date(1994, 12, 1), src=Src(
                      "BOI-INT-CVB-QAT (BOFiP)",
                      "https://bofip.impots.gouv.fr/bofip/1727-PGP.html/"
                      "identifiant=BOI-INT-CVB-QAT-20120912", None,
                      "La convention [...] est entrée en vigueur le 1er décembre 1994. [...] Cet "
                      "avenant est entré en vigueur le 23 avril 2009."))
    start = date(2009, 4, 23)
    for cat, art, quote in (
        ("DIVIDEND", "Article 8", "Les dividendes payés par une société qui est un résident "
         "d'un Etat à un résident de l'autre Etat ne sont imposables que dans cet autre Etat"),
        ("INTEREST", "Article 9", "Les revenus de créances provenant d'un Etat et payés à un "
         "résident de l'autre Etat ne sont imposables que dans cet autre Etat"),
        ("ROYALTY", "Article 10", "Les redevances provenant d'un Etat et payées à un résident "
         "de l'autre Etat ne sont imposables que dans cet autre Etat"),
    ):
        sd.treaty_rate(t, cat, art, start, Src(
            "Convention France–Qatar, version consolidée (impots.gouv.fr)", FR_QA, f"{art}(1)",
            quote), exclusive=True)
    sd.ppt(t, date(2021, 1, 1), Src(
        "Convention France–Qatar modifiée par la CML (impots.gouv.fr)", FR_QA_MLI,
        "MLI art. 7(1)",
        "la CML est entrée en vigueur le 1er janvier 2019 pour la France et le 1er avril 2020 "
        "pour le Qatar [...] à compter du 1er janvier 2021"))
    # No Qatar–UAE income tax treaty appears on Qatar's official treaty list.
