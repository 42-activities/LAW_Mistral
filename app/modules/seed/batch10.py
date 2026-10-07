"""P8 batch 10: Norway, Canada, the Western Balkans (AL, BA, ME, MK, XK), India and China.

Figures were sourced on 2026-10-07 from the texts cited on each `Src` and are stored as
`unreviewed` until a named reviewer confirms them (spec §10). Kosovo uses the user-assigned code
"XK". Research notes: docs/superpowers/plans/2026-10-07-p8-batch10.md.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import JurisdictionGroup
from app.modules.seed.builder import Seeder, Src, period
from app.modules.treaty.models import MfnClause, Treaty
from app.modules.treaty.repository import TreatyRepository

MLI_PARTIES = (
    "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/"
    "beps-mli-signatories-and-parties.pdf"
)
MLI_AE = (
    "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/"
    "beps-mli-position-united-arab-emirates-instrument-deposit.pdf"
)
UAE_DTA_LIST = (
    "https://mof.gov.ae/wp-content/uploads/2023/08/Avoidance-of-Double-Taxation-Agreements1.pdf"
)
EU_LIST_2026 = "https://data.consilium.europa.eu/doc/document/ST-5869-2026-INIT/en/pdf"
FATF_JUNE_2026 = (
    "https://scb.gov.bs/wp-content/uploads/2026/06/Financial-Action-Task-Force-Public-"
    "Statement-on-list-of-Jurisdictions-under-Increased-Monitoring-June-2026.pdf"
)
FR_YU = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/ex_yougoslavie/"
    "convention-avec-l-ex-yougoslavie_fd_1730.pdf"
)
FR_YU_SRC = "Convention France–Yougoslavie du 28 mars 1974 (impots.gouv.fr)"

NO_SKL = "https://lovdata.no/dokument/NL/lov/1999-03-26-14"
NO_SKL_SRC = "Skatteloven (LOV-1999-03-26-14), lovdata.no"
NO_VEDTAK = (
    "https://stortinget.no/no/Saker-og-publikasjoner/Publikasjoner/Innstillinger/Stortinget/"
    "2025-2026/inns-202526-003s/?m=21"
)
NO_VEDTAK_SRC = "Stortingets skattevedtak for inntektsåret 2026 (Innst. 3 S (2025–2026), kap. 22)"
FR_NO = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/norvege/"
    "norvege_convention-avec-la-norvege_fd_1966.pdf"
)

CA_ITA = "https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-{}.html"
CA_ITA_SRC = "Income Tax Act, R.S.C. 1985, c. 1 (5th Supp.), current to 2026-09-21 (Justice Laws)"
CA_CRA = (
    "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/corporations/"
    "corporation-tax-rates.html"
)
FR_CA = (
    "https://www.canada.ca/en/department-finance/programs/tax-policy/tax-treaties/country/"
    "france-convention-consolidated-1975-1987-1995-2010.html"
)
CA_AE = (
    "https://www.canada.ca/en/department-finance/programs/tax-policy/tax-treaties/country/"
    "united-arab-emirates-convention-2002.html"
)

AL_LAW = "https://www.tatime.gov.al/shkarko.php?id=14530"
AL_SRC = "Ligji nr. 29/2023 «Për tatimin mbi të ardhurat», consolidated to Law 81/2025 (DPT)"
FR_AL = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/albanie/"
    "albanie_version_consolidee_convention_avec_albanie_modifiee_par_convention_multilaterale.pdf"
)
AL_AE = "https://www.tatime.gov.al/shkarko.php?id=344"
AL_MLI = "https://www.tatime.gov.al/shkarko.php?id=9521"

BA_FBIH = (
    "https://ik.imagekit.io/9qcwbg8wl/15-16_i_15-20-zakon-o-porezu-na-dobit-precisceni_"
    "07YP9wNd9.pdf"
)
BA_SRC = "Zakon o porezu na dobit FBiH (SN FBiH 15/16, 15/20), PU FBiH consolidated text"
FR_BA = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/bosnie-herzegovine/"
    "version_consolidee_de_la_convention_applicable_entre_la_bosnie-herzegovine_et_la_france_"
    "modifiee_par_la_convention_multilaterale.pdf"
)
BA_AE = (
    "https://chj.mft.gov.ba/data/Fiskalni%20sporazumi%202/"
    "BIH-UAE-komb.tekst-hrv-kona%C4%8Dno.pdf"
)

ME_CIT = "https://www.sluzbenilist.me/propisi/333948"
ME_WHT = "https://www.sluzbenilist.me/propisi/363013"
ME_DIV = "https://www.sluzbenilist.me/propisi/336497"
ME_SRC = "Zakon o porezu na dobit pravnih lica (Sl. list CG, sluzbenilist.me)"
ME_AE = "https://www.gov.me/dokumenta/491baa5b-c911-4b29-b16b-5ee42daba3e3"

MK_LAW = "https://www.ujp.gov.mk/files/attachment/0000/0965/Zakon_za_danok_na_dobivka_199_2023.pdf"
MK_SRC = "Закон за данокот на добивка, consolidated to SV RSM 199/23 (UJP)"
MK_TABLE = "https://www.ujp.gov.mk/en/plakjanje/category/137?print=1"
FR_MK = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/macedoine/"
    "nid_6149_macedoine.pdf"
)
MK_AE = "https://www.ujp.gov.mk/files/attachment/0000/0955/OAE_MKD_megjunaroden_dogovor_pdf.pdf"

XK_LAW = "https://www.atk-ks.org/wp-content/uploads/2019/09/Ligji-Nr.-06-L-105.pdf"
XK_SRC = "Ligji Nr. 06/L-105 për tatimin në të ardhurat e korporatave (ATK)"
FR_XK = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/kosovo/"
    "kosovo-_accord_de_succession_detat.pdf"
)
XK_AE = (
    "https://www.atk-ks.org/wp-content/uploads/2017/12/"
    "SHQIP_METD-me-Emiratet-e-Bashkuara-Arabe-1.pdf"
)
XK_TREATIES = "https://www.atk-ks.org/marreveshjet/marreveshjet-nderkombetare/"

IN_BILL = "https://www.indiabudget.gov.in/doc/Finance_Bill.pdf"
IN_BILL_SRC = "Finance Bill 2026 (Bill No. 3 of 2026), indiabudget.gov.in"
IN_MEMO = "https://www.indiabudget.gov.in/doc/memo.pdf"
FR_IN = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/inde/"
    "inde_convention-avec-l-inde_fd_1878.pdf"
)
FR_IN_MLI = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/inde/"
    "version_consolidee_de_la_convention_avec_inde_modifiee_par_la_convention_multilaterale.pdf"
)
FR_IN_BOFIP = "https://bofip.impots.gouv.fr/bofip/1188-PGP.html/identifiant=BOI-INT-CVB-IND-20120912"
IN_AE = "https://mof.gov.ae/wp-content/uploads/2025/06/UAE-India-DTA.pdf"

CN_LAW = "https://fgk.chinatax.gov.cn/zcfgk/c100009/c5193018/content.html"
CN_LAW_SRC = "中华人民共和国企业所得税法 (EIT Law, as amended 2018-12-29), STA law database"
CN_REGS = "https://fgk.chinatax.gov.cn/zcfgk/c100010/c5194417/content.html"
CN_REGS_SRC = "企业所得税法实施条例 (EIT Implementation Regulations, revised 2024-12-06), STA"
FR_CN = (
    "https://www.chinatax.gov.cn/chinatax/n810341/n810770/c1152674/5026955/files/11526741.pdf"
)
FR_CN_SRC = "Agreement between China and France (2013), STA English text"
CN_AE = (
    "https://guangdong.chinatax.gov.cn/gdsw/stsw_zsfwpt_zczy_ssty_yz/2023-03/17/"
    "8eae5ef2be4e43cea33fd9509a9b32d6/files/3ecb8d83cff14555867718e835882481.pdf"
)


def seed_batch10(session: Session) -> None:
    sd = Seeder(session)
    fr = sd.jurisdiction("FR", "France")
    ae = sd.jurisdiction("AE", "United Arab Emirates")
    eu = sd.group("EU", "European Union member states")
    _norway(sd, fr, eu, sd.jurisdiction("NO", "Norway"))
    _canada(sd, fr, ae, sd.jurisdiction("CA", "Canada"))
    _albania(sd, fr, ae, sd.jurisdiction("AL", "Albania"))
    ba = sd.jurisdiction("BA", "Bosnia and Herzegovina")
    _bosnia(sd, fr, ae, ba)
    sd.listing(ba, "FATF_GREY", "increased_monitoring", date(2026, 6, 19), None, Src(
        "FATF — Jurisdictions under increased monitoring, 19 June 2026 (printout relayed by the "
        "Securities Commission of The Bahamas, 25 June 2026)", FATF_JUNE_2026, None,
        "In June 2026, Bosnia and Herzegovina made a high-level political commitment to work "
        "with the FATF and MONEYVAL ... Since the adoption of its MER in December 2024"))
    me = sd.jurisdiction("ME", "Montenegro")
    _montenegro(sd, fr, ae, me)
    sd.listing(me, "EU_TAX_ANNEX_II", "state_of_play", date(2026, 2, 17), None, Src(
        "Council conclusions on the EU list of non-cooperative jurisdictions, 17 Feb 2026 "
        "(doc. 5869/26)", EU_LIST_2026, "Annex II 1.1 and 1.2",
        "committed to addressing the identified deficiencies … on both core requirements 1 and "
        "2 … AEOI peer review report in 2026: Jordan and Montenegro; committed to fulfilling the "
        "necessary steps to request and being granted, by 15 August 2026, an in-depth review by "
        "the Global Forum … Montenegro"))
    _north_macedonia(sd, fr, ae, sd.jurisdiction("MK", "North Macedonia"))
    _kosovo(sd, fr, ae, sd.jurisdiction("XK", "Kosovo"))
    _india(sd, fr, ae, sd.jurisdiction("IN", "India"))
    _china(sd, fr, ae, sd.jurisdiction("CN", "China"))


def _mfn(sd: Seeder, t: Treaty, category: str, start: date, src: Src, description: str) -> None:
    """A most-favoured-nation clause: flagged by the engine for review, never auto-applied."""
    if TreatyRepository(sd.s).get_mfn(t.id, category, start) is None:
        sd.s.add(MfnClause(
            treaty_id=t.id, income_category_id=sd._id("cat", category), description=description,
            source_evidence_id=sd.ev(src), valid_period=period(start),
        ))
        sd.s.flush()


def _norway(sd: Seeder, fr: Jurisdiction, eu: JurisdictionGroup, no: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(no, start, Src(
        NO_VEDTAK_SRC, NO_VEDTAK, "Skattevedtak 2026 § 3-3 (1)",
        "Selskaper og innretninger som nevnt i skatteloven § 2-36 annet ledd, svarer skatt til "
        "staten med 22 pst. av inntekten. (25% for companies paying financial tax on wages)"),
        rate="22")
    sd.wht(no, "DIVIDEND", "25", start, Src(
        NO_VEDTAK_SRC, NO_VEDTAK, "Skattevedtak 2026 § 3-5 (3); skatteloven § 10-13 (1)",
        "Av aksjeutbytte som utdeles til aksjonær som er hjemmehørende i utlandet, svares skatt "
        "til staten med 25 pst. eller i tilfelle den sats som følger av skatteavtale"))
    sd.exemption(
        no, "DIVIDEND", eu, start,
        Src(NO_SKL_SRC, NO_SKL + "/KAPITTEL_2", "skatteloven § 2-38 (1) i, (5)",
            "fritar for skatteplikt etter § 10-13 bare dersom skattyter er reelt etablert og "
            "driver reell økonomisk aktivitet i et EØS-land"),
        min_holding_pct=None, min_holding_months=None, legal_ref="skatteloven § 2-38 (5)",
        description="Dividends to a company genuinely established with real economic activity "
        "in an EEA state are exempt (no holding test); stored for the EU group — EEA-only "
        "states (IS, LI) are not in the group",
    )
    # The 15% charge on interest and royalties (§ 10-80/10-81) applies only to related (≥50%)
    # recipients in low-tax countries — like the Dutch conditional WHT, the general 0% is stored.
    narrow = Src(
        NO_SKL_SRC, NO_SKL + "/KAPITTEL_10-7", "skatteloven § 10-80 (1), § 10-81",
        "Selskap eller innretning hjemmehørende i et lavskatteland, jf. § 10-63, skal svare "
        "skatt … av renter av gjeld mottatt fra nærstående selskap (15% only for related "
        "(≥50%) recipients in low-tax countries outside genuine EEA establishment; no "
        "withholding otherwise)")
    sd.wht(no, "INTEREST", "0", start, narrow)
    sd.wht(no, "ROYALTY", "0", start, narrow)
    sd.regime(
        no, start,
        Src(NO_SKL_SRC, NO_SKL + "/KAPITTEL_2", "skatteloven § 2-38 (3) d, (6)",
            "…dersom skattyteren ikke sammenhengende de to siste årene … har eid minst 10 "
            "prosent av kapitalen og hatt minst 10 prosent av stemmene… ; tre prosent av "
            "utbytte … skal … anses som skattepliktig inntekt"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=10, min_holding_period_months=24, subject_to_tax_condition=True,
        exempt_share_pct=97,
        notes="Fritaksmetoden: EEA subsidiaries qualify with no holding test (low-tax EEA only "
        "if genuinely established); non-EEA needs ≥10% for 2 years (stored). 3% of dividends "
        "taxable (0.66%) except within a § 10-4 group; gains 100% exempt. Non-EEA low-tax "
        "countries (§ 10-63) excluded",
    )
    sd.cfc(
        no, start,
        Src(NO_SKL_SRC, NO_SKL + "/KAPITTEL_10-9", "skatteloven § 10-62, § 10-63",
            "land hvor den alminnelige inntektsskatt … utgjør mindre enn to tredjedeler av den "
            "skatten selskapet … ville ha blitt ilagt dersom det/den hadde vært hjemmehørende i "
            "Norge"),
        control_threshold_pct=50, low_tax_relative_pct=Decimal("66.667"), threshold_inclusive=False,
        legal_ref="skatteloven §§ 10-60 to 10-68 (NOKUS)",
        effect="Income of a ≥50% Norwegian-controlled company in a country taxing below "
        "two-thirds of the Norwegian tax is included (exemptions: treaty-country companies with "
        "mainly active income; genuine EEA establishment).",
    )

    # Norway's MLI position does not list France, so the treaty is not covered: no PPT.
    # No Norway–UAE income tax treaty (UAE MoF dashboard and DTA table).
    t = sd.treaty(fr, no, name="Convention between France and Norway (1980)",
                  signed=date(1980, 12, 19), in_force=date(1981, 9, 10), src=Src(
                      "Convention France–Norvège, texte consolidé (impots.gouv.fr)", FR_NO,
                      None, "signed in Paris on 19 Dec 1980, in force 10 Sep 1981; avenants of "
                      "1984, 1995 (in force 1 Sep 1996) and 1999 (in force 1 Dec 2002)"))
    src = "Convention France–Norvège, texte consolidé (impots.gouv.fr)"
    start = date(1996, 9, 1)  # 1995 avenant
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_NO, "Article 10(2)(a)", "ne peut excéder 15 p. cent du montant brut"),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_NO, "Article 10(2)(b)(i)",
        "…qui détient directement ou indirectement au moins 10 p. cent du capital … ne peut "
        "excéder 5 p. cent (Norwegian company paying a French company)"),
        max_rate="5", ownership_threshold="10", source=no)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_NO, "Article 10(2)(b)(ii)",
        "taxable only in France where the French company holds directly at least 25 p. cent"),
        exclusive=True, ownership_threshold="25", source=no)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_NO, "Article 10(2)(c)",
        "taxable only in Norway where the Norwegian company holds at least 10 p. cent (French "
        "company paying)"),
        exclusive=True, ownership_threshold="10", source=fr)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, FR_NO, "Article 11", "ne sont imposables que dans cet autre Etat"), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, FR_NO, "Article 12", "ne sont imposables que dans cet autre Etat"), exclusive=True)


def _canada(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, ca: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(ca, start, Src(
        "CRA — Corporation tax rates: federal 15% + Ontario 11.5% = 26.5% (combined, Ontario as "
        "illustrative province)", CA_CRA, "ITA s. 123, 124, 123.4; Ontario higher rate",
        "The basic rate of Part I tax is 38% of your taxable income, 28% after the federal tax "
        "abatement. After the general tax reduction, the net tax rate is 15% … Ontario 3.2% | "
        "11.5% | $500,000"), rate="26.5")
    sd.wht(ca, "DIVIDEND", "25", start, Src(
        CA_ITA_SRC, CA_ITA.format("212"), "ITA s. 212(2)",
        "Every non-resident person shall pay an income tax of 25% on every amount that a "
        "corporation resident in Canada pays or credits … (a) a taxable dividend"))
    # Arm's-length interest is exempt; a typical intra-group loan is non-arm's-length, so 25%.
    sd.wht(ca, "INTEREST", "25", start, Src(
        CA_ITA_SRC, CA_ITA.format("212"), "ITA s. 212(1)(b)",
        "interest that (i) is not fully exempt interest and is paid or payable (A) to a person "
        "with whom the payer is not dealing at arm's length … or (ii) is participating debt "
        "interest (25%; arm's-length interest is not taxed)"))
    sd.wht(ca, "ROYALTY", "25", start, Src(
        CA_ITA_SRC, CA_ITA.format("212"), "ITA s. 212(1)(d)",
        "rent, royalty or similar payment… (25%)"))
    sd.regime(
        ca, start,
        Src(CA_ITA_SRC, CA_ITA.format("113"), "ITA s. 113(1)(a); s. 95(1); s. 38(a)",
            "foreign-affiliate dividends deductible to the extent paid out of exempt surplus; "
            "a taxpayer's taxable capital gain … is ½ of the taxpayer's capital gain"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="No classic participation exemption. Foreign-affiliate (≥1%, ≥10% with related "
        "persons) dividends are deductible out of exempt surplus (s. 113) — exempt-surplus rules "
        "(Reg. 5907) not read, so not modelled. Domestic dividends deductible (s. 112). Share "
        "gains: 50% inclusion",
    )
    # FAPI is included whatever the foreign rate; foreign tax relief makes the charge bite only
    # below the Canadian rate, so 100% is stored (as for Uzbekistan in batch 8).
    sd.cfc(
        ca, start,
        Src(CA_ITA_SRC, CA_ITA.format("91"), "ITA s. 91(1); s. 95(1)",
            "the taxpayer includes its participating percentage of the foreign accrual property "
            "income of each controlled foreign affiliate"),
        control_threshold_pct=50, low_tax_relative_pct=100, threshold_inclusive=False,
        legal_ref="ITA s. 91, 95 (FAPI)",
        effect="Passive income (FAPI) of a controlled foreign affiliate is included currently; "
        "there is no rate test (relief for foreign tax not modelled).",
    )

    t = sd.treaty(fr, ca, name="Convention between France and Canada (1975)",
                  signed=date(1975, 5, 2), in_force=date(1976, 7, 29), src=Src(
                      "Canada–France convention, consolidated 1975-1987-1995-2010 (Finance "
                      "Canada)", FR_CA, None, "signed 2 May 1975, in force 29 Jul 1976; "
                      "protocol of 2 Feb 2010 in force 27 Dec 2013"))
    src = "Canada–France convention, consolidated 1975-1987-1995-2010 (Finance Canada)"
    start = date(2013, 12, 27)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_CA, "Article 10(2)(c)", "15 per cent of the gross amount of the dividends in "
        "all other cases"), max_rate="15")
    # The 5% tier is on ≥10% of voting power (Canadian payer) or capital (French payer).
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_CA, "Article 10(2)(a)",
        "(i) controls directly or indirectly at least 10 per cent of the voting power in the "
        "company paying the dividends where that company is a resident of Canada (stored as a "
        "10% holding)"), max_rate="5", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, FR_CA, "Article 11(2)", "shall not exceed 10 per cent of the gross amount of the "
        "interest"), max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, FR_CA, "Article 12(2)", "10 per cent (copyright, computer software, patent and "
        "know-how royalties taxable only in the residence State, art. 12(3)(a) — not "
        "modelled)"), max_rate="10")
    sd.ppt(t, date(2020, 1, 1), Src(
        "MLI signatories and parties (OECD), status 15 Sep 2026", MLI_PARTIES, "MLI art. 7(1)",
        "France–Canada covered by both (CA no. 81, FR no. 19); MLI in force 1 Jan 2019 (FR) and "
        "1 Dec 2019 (CA) — withholding taxes from 1 Jan 2020 (art. 35(1)(a))"))

    t = sd.treaty(ca, ae, name="Convention between Canada and the UAE (2002)",
                  signed=date(2002, 6, 9), in_force=date(2004, 5, 25), src=Src(
                      "UAE Ministry of Finance — list of double taxation agreements",
                      UAE_DTA_LIST, None, "25 Canada 9/6/2002 … 25/5/2004"))
    src = "Canada–UAE convention 2002 (Finance Canada)"
    start = date(2004, 5, 25)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, CA_AE, "Article 10(2)(c)", "15 per cent of the gross amount of the dividends in "
        "all other cases"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, CA_AE, "Article 10(2)(a)",
        "if the beneficial owner is a company which controls directly or indirectly at least 10 "
        "per cent of the voting power in the company paying the dividends (stored as a 10% "
        "holding)"), max_rate="5", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, CA_AE, "Article 11(2)", "shall not exceed 10 per cent of the gross amount of the "
        "interest"), max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, CA_AE, "Article 12(2)", "10 per cent (copyright, software, patent and know-how "
        "royalties taxable only in the residence State, art. 12(3) — not modelled)"),
        max_rate="10")
    sd.ppt(t, date(2020, 1, 1), Src(
        "MLI signatories and parties (OECD), status 15 Sep 2026", MLI_PARTIES, "MLI art. 7(1)",
        "Canada–UAE covered by both (CA no. 80, UAE no. 22); MLI in force 1 Sep 2019 (UAE) and "
        "1 Dec 2019 (CA) — withholding taxes from 1 Jan 2020 (art. 35(1)(a))"))


def _albania(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, al: Jurisdiction) -> None:
    start = date(2024, 1, 1)
    sd.cit(al, start, Src(
        AL_SRC, AL_LAW, "Law 29/2023 art. 41",
        "Norma e tatimit mbi të ardhurat e korporatave është 15%. (0% to ALL 14m turnover "
        "until 2029; 5% sector regimes)"), rate="15")
    wht = Src(AL_SRC, AL_LAW, "Law 29/2023 art. 58(2)(a), 59",
              "Norma e mbajtjes së tatimit në burim mbi dividendët është 8%. Norma e tatimit të "
              "mbajtur në burim mbi të ardhurat dhe pagesat sipas nenit 58 … është 15%.")
    sd.wht(al, "DIVIDEND", "8", start, wht)
    sd.wht(al, "INTEREST", "15", start, wht)
    sd.wht(al, "ROYALTY", "15", start, wht)
    sd.regime(
        al, start,
        Src(AL_SRC, AL_LAW, "Law 29/2023 art. 29(1)",
            "në qoftë se: a) entiteti marrës ka aksione apo pjesëmarrje prej të paktën 10% … dhe "
            "b) aksionet … janë mbajtur për një periudhë të pandërprerë prej së paku 24 muajsh"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=10, min_holding_period_months=24, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Dividends exempt at ≥10% held 24 months (no subject-to-tax condition); share "
        "gains taxed at 15%. CFC rules (art. 19) apply only to individuals — no corporate CFC "
        "seeded. No Pillar Two law (Deloitte, Jan 2026)",
    )

    t = sd.treaty(fr, al, name="Convention between France and Albania (2002)",
                  signed=date(2002, 12, 24), in_force=date(2005, 10, 1), src=Src(
                      "Convention France–Albanie modifiée par la CML (impots.gouv.fr)", FR_AL,
                      None, "signée à Tirana le 24 décembre 2002 … entrée en vigueur le 1er "
                      "octobre 2005"))
    src = "Convention France–Albanie modifiée par la CML (impots.gouv.fr)"
    start = date(2006, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_AL, "Article 10(2)(b)", "15 % … dans tous les autres cas"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_AL, "Article 10(2)(a)", "5 % du montant brut des dividendes si le bénéficiaire "
        "effectif est une société qui détient directement ou indirectement au moins 25 % du "
        "capital"), max_rate="5", ownership_threshold="25", end=date(2021, 1, 1))
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(2021, 1, 1), Src(
        src, FR_AL, "Article 10(2)(a); MLI art. 8",
        "au moins 25 % du capital … tout au long d'une période de 365 jours incluant le jour du "
        "paiement"), max_rate="5", ownership_threshold="25", min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, FR_AL, "Article 11(2)", "ne peut excéder 10 % du montant brut des intérêts"),
        max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, FR_AL, "Article 12(1)(b)", "ne peut excéder 5 % du montant brut des redevances"),
        max_rate="5")
    sd.ppt(t, date(2021, 1, 1), Src(
        src, FR_AL, "MLI art. 7(1)", "si le fait générateur de ces impôts intervient à compter "
        "du 1er janvier 2021"))

    # Entry into force from Albania's MLI ratification list (Law 93/2020); not confirmed by a
    # gazette notice or the UAE side.
    t = sd.treaty(al, ae, name="Agreement between Albania and the UAE (2014)",
                  signed=date(2014, 3, 13), in_force=date(2015, 3, 26), src=Src(
                      "Law 93/2020 ratifying the MLI — Albania's list of covered agreements (DPT)",
                      AL_MLI, None, "40 United Arab Emirates — signed 14-03-2014, in force "
                      "26-03-2015 (DPT treaty table: Me efekte nga data 01.01.2014)"))
    src = "Law 61/2014 ratifying the Albania–UAE agreement (DPT copy)"
    start = date(2014, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, AL_AE, "Article 10(2)(c)", "10 % … në të gjitha rastet e tjera"), max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, AL_AE, "Article 10(2)(b)",
        "5% … nëse pronari përfitues është një shoqëri … e cila zotëron të paktën drejtpërdrejt "
        "10% të kapitalit"), max_rate="5", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, AL_AE, "Article 11(1)",
        "Interesi i nxjerrë në një Shtet Kontraktues dhe i paguar një rezidenti të Shtetit "
        "tjetër Kontraktues tatohet në Shtetin tjetër Kontraktues"), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, AL_AE, "Article 12(2)", "tatimi i vendosur nuk tejkalon 5% të shumës bruto të "
        "tarifave të licencave"), max_rate="5")
    sd.ppt(t, date(2021, 1, 1), Src(
        "MLI position of the UAE — instrument of deposit (OECD)", MLI_AE, "MLI art. 7(1)",
        "1. Albania Original 14-03-2014 (covered by both; MLI in force for Albania 1 Jan 2021 — "
        "WHT date derived from art. 35(1)(a))"))


def _bosnia(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, ba: Jurisdiction) -> None:
    # Profit tax is set by the entities: Federation of BiH values are stored; Republika Srpska
    # (10% CIT, 10% dividend WHT) and Brčko District (10% CIT, no dividend WHT) differ.
    start = date(2026, 1, 1)
    sd.cit(ba, start, Src(
        BA_SRC, BA_FBIH, "Zakon o porezu na dobit FBiH čl. 31",
        "Porez na dobit plaća se po stopi od 10% na poreznu osnovicu utvrđenu u poreznom "
        "bilansu. (Federation of BiH; RS and Brčko District also 10%)"), rate="10")
    wht = Src(BA_SRC, BA_FBIH, "Zakon o porezu na dobit FBiH čl. 38(7)",
              "Porez po odbitku plaća se po stopi 10% a na dividende po stopi 5%. Stopa poreza po "
              "odbitku može biti i niža u slučaju primjene Ugovora o izbjegavanju dvostrukog "
              "oporezivanja.")
    sd.wht(ba, "DIVIDEND", "5", start, wht)
    sd.wht(ba, "INTEREST", "10", start, wht)
    sd.wht(ba, "ROYALTY", "10", start, wht)
    sd.regime(
        ba, start,
        Src(BA_SRC, BA_FBIH, "Zakon o porezu na dobit FBiH čl. 21(1)",
            "Prihodi ostvareni na osnovu učešća u kapitalu drugog poreznog obveznika ne ulaze u "
            "osnovicu za oporezivanje, ukoliko se isplaćuju iz dobiti na koju je obračunat i "
            "plaćen porez na dobit."),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="FBiH stored. Dividends from taxed profits of another taxpayer excluded; whether "
        "foreign dividends qualify is unclear, so treated as taxable. Share gains taxed. RS: "
        "10% dividend WHT, domestic dividends only; Brčko: no dividend WHT. No CFC rules in any "
        "of the three laws",
    )

    t = sd.treaty(fr, ba, name="Convention between France and Yugoslavia (1974), applied to "
                  "Bosnia and Herzegovina", signed=date(1974, 3, 28), in_force=date(1975, 8, 1),
                  src=Src("Convention France–Bosnie-Herzégovine modifiée par la CML "
                          "(impots.gouv.fr)", FR_BA, None,
                          "entrée en vigueur le 1er août 1975"))
    src = "Convention France–Bosnie-Herzégovine modifiée par la CML (impots.gouv.fr)"
    start = date(1975, 8, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_BA, "Article 10(2)(b)", "15 p. cent … dans tous les autres cas"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_BA, "Article 10(2)(a)", "5 p. cent du montant brut des dividendes si le "
        "bénéficiaire est une société qui dispose directement d'au moins 25 p. cent du capital"),
        max_rate="5", ownership_threshold="25")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, FR_BA, f"{art}(1)", "ne sont imposables que dans cet autre Etat"),
            exclusive=True)
    sd.ppt(t, date(2021, 1, 1), Src(
        src, FR_BA, "MLI art. 7(1)", "si le fait générateur de ces impôts intervient à compter "
        "du 1er janvier 2021"))

    # Entry into force not found (60 days after ratification; mof.gov.ae not reached): stored
    # without the date, so the engine does not apply it. The header says 18 Sep 2006; the
    # testimonium (stored) says 19 Sep 2006.
    t = sd.treaty(ba, ae, name="Agreement between Bosnia and Herzegovina and the UAE (2006)",
                  signed=date(2006, 9, 19), in_force=None, src=Src(
                      "BiH–UAE agreement, MLI synthesised text (BiH Ministry of Finance)", BA_AE,
                      None, "Sačinjeno ... u Singapuru, dana 19. septembra 2006 (Sl. glasnik BiH "
                      "– Međunarodni ugovori 10/07); entry into force not published"))
    src = "BiH–UAE agreement, MLI synthesised text (BiH Ministry of Finance)"
    start = date(2007, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, BA_AE, "Article 10(2)(b)", "10 posto ... u svim ostalim slučajevima"),
        max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, BA_AE, "Article 10(2)(a)", "5 posto bruto iznosa dividendi ako je stvarni vlasnik "
        "kompanija (osim parterstva), koja posjeduje direktno najmanje 10 posto kapitala"),
        max_rate="5", ownership_threshold="10")
    # Art. 11 has no source-State paragraph; reading it as residence-only is an interpretation
    # — interest not seeded.
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, BA_AE, "Article 12(2)", "porez ne može biti veći od 5 posto bruto iznosa autorskih "
        "naknada"), max_rate="5")
    sd.ppt(t, date(2021, 1, 1), Src(
        src, BA_AE, "MLI art. 7(1)", "MLI in force for BiH 1.1.2021 and the UAE 1.9.2019 — PPT "
        "applies to withholding taxes from 1.1.2021"))


def _montenegro(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, me: Jurisdiction) -> None:
    sd.cit(me, date(2022, 1, 1), Src(
        ME_SRC + " — art. 28 as replaced by Sl. list CG 146/2021", ME_CIT, "ZPDPL čl. 28",
        "Stope poreza na iznos oporezive dobiti iznose: 1) do 100.000,00 eura 9%; 2) od "
        "100.000,01 eura do 1.500.000,00 eura: 9.000,00 eura +12% na iznos preko 100.000,01 "
        "eura; 3) preko 1.500.000,01 eura: 177.000,00 eura +15% na iznos preko 1.500.000,01 "
        "eura"), brackets=[("0", "100000", "9"), ("100000", "1500000", "12"),
                            ("1500000", None, "15")])
    start = date(2024, 1, 1)
    wht = Src(ME_SRC + " — art. 29 as replaced by Sl. list CG 125/2023", ME_WHT,
              "ZPDPL čl. 29(1), (4)",
              "Porez po odbitku obračunava se i plaća u trenutku isplate prihoda, po stopi od 15% "
              "na osnovicu koju čini iznos bruto prihoda. (30% for territories on the MoF "
              "tax-sovereignty list without a treaty, art. 29(5)-(7))")
    sd.wht(me, "DIVIDEND", "15", start, wht)
    sd.wht(me, "INTEREST", "15", start, wht)
    sd.wht(me, "ROYALTY", "15", start, wht)
    sd.regime(
        me, start,
        Src(ME_SRC + " — art. 9 as replaced by Sl. list CG 40/08", ME_DIV, "ZPDPL čl. 9",
            "Prihodi od dividendi i udjela u dobiti drugih pravnih lica izuzimaju se iz poreske "
            "osnovice primaoca, ako je njihov isplatilac obveznik poreza po ovom zakonu."),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="Only dividends from Montenegrin taxpayers are exempt; foreign dividends and share "
        "gains taxed. CFC rules, EU-directive WHT exemptions and GAAR (Sl. list CG 104/26) "
        "apply only from EU accession — not seeded. QDMTT law 33/2026 in force 10 Mar 2026",
    )

    # France's MLI position lists the 1974 convention only for BiH and Serbia: no PPT.
    t = sd.treaty(fr, me, name="Convention between France and Yugoslavia (1974), applied to "
                  "Montenegro", signed=date(1974, 3, 28), in_force=date(1975, 8, 1), src=Src(
                      FR_YU_SRC, FR_YU, None,
                      "Convention France–Yougoslavie signée à Paris le 28 mars 1974, entrée en "
                      "vigueur le 1er août 1975 (Montenegrin DTT table: SFRJ 28/75, 1.1.1976)"))
    start = date(1976, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        FR_YU_SRC, FR_YU, "Article 10(2)(b)", "15 p. cent… dans tous les autres cas."),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        FR_YU_SRC, FR_YU, "Article 10(2)(a)", "5 p. cent… si le bénéficiaire est une société qui "
        "dispose directement d'au moins 25 p. cent du capital"),
        max_rate="5", ownership_threshold="25")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            FR_YU_SRC, FR_YU, f"{art}(1)", "ne sont imposables que dans cet autre Etat"),
            exclusive=True)

    t = sd.treaty(me, ae, name="Agreement between Montenegro and the UAE (2012)",
                  signed=date(2012, 3, 26), in_force=date(2013, 12, 10), src=Src(
                      "Montenegro–UAE double tax treaty (gov.me)", ME_AE, None,
                      "Ugovor je stupio na snagu 10.12.2013 (applies from 1.1.2014)"))
    src = "Montenegro–UAE double tax treaty (gov.me)"
    start = date(2014, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 11", start, Src(
        src, ME_AE, "Article 11(2)", "10 odsto… u svim drugim slučajevima"), max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 11", start, Src(
        src, ME_AE, "Article 11(2)", "5 odsto… ako je stvarni vlasnik kompanija koja neposredno "
        "ili posredno ima najmanje 5 odsto kapitala"), max_rate="5", ownership_threshold="5")
    sd.treaty_rate(t, "INTEREST", "Article 12", start, Src(
        src, ME_AE, "Article 12(2)", "ne može biti veći od 10 odsto"), max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 13", start, Src(
        src, ME_AE, "Article 13(2), (4)", "10% for patents, trademarks, designs, secret formulas, "
        "equipment and know-how (5% for copyright — not modelled)"), max_rate="10")
    sd.ppt(t, date(2027, 1, 1), Src(
        "MLI signatories and parties (OECD), status 15 Sep 2026", MLI_PARTIES, "MLI art. 7(1)",
        "covered by both (UAE no. 73 Montenegro Original 26-03-2012 10-12-2013); MLI in force "
        "for Montenegro 01-09-2026 — withholding taxes from 1 Jan 2027 (art. 35(1)(a))"))


def _north_macedonia(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, mk: Jurisdiction) -> None:
    start = date(2023, 9, 25)
    sd.cit(mk, start, Src(
        MK_SRC, MK_LAW, "Закон за данокот на добивка чл. 2",
        "Стапката на данокот на добивка изнесува 10%."), rate="10")
    wht = Src(MK_SRC, MK_LAW, "Закон за данокот на добивка чл. 21(1), 22(1)",
              "Данокот што ќе се задржи … се пресметува на бруто приходите по стапка од 10%.")
    sd.wht(mk, "DIVIDEND", "10", start, wht)
    sd.wht(mk, "INTEREST", "10", start, wht)
    sd.wht(mk, "ROYALTY", "10", start, wht)
    sd.regime(
        mk, start,
        Src(MK_SRC, MK_LAW, "Закон за данокот на добивка чл. 18",
            "Даночната основа се намалува за износот на приходите од дивиденди остварени со "
            "учество во капиталот на друг обврзник - резидент на Република Северна Македонија"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="Only dividends from taxed MK residents are deducted; foreign dividends taxed with "
        "a credit (art. 37); share gains taxed at 10%. No CFC rules. QDMTT/IIR from FY 2024, "
        "UTPR from FY 2025 (SV RSM 3/2025)",
    )

    # North Macedonia has signed but not ratified the MLI: no PPT on either treaty.
    t = sd.treaty(fr, mk, name="Convention between France and North Macedonia (1999)",
                  signed=date(1999, 2, 10), in_force=date(2004, 5, 1), src=Src(
                      "UJP — treaty rate table (official)", MK_TABLE, None,
                      "France|23/1999|01.05.2004|01.01.2005"))
    src = "Convention France–Macédoine (impots.gouv.fr)"
    start = date(2005, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_MK, "Article 10(2)(a)", "l'impôt ainsi établi ne peut excéder 15% du montant "
        "brut des dividendes"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_MK, "Article 10(2)(b)", "société … qui détient directement ou indirectement au "
        "moins 10% du capital … ne sont imposables que dans l'Etat contractant dont le "
        "bénéficiaire effectif est un résident"), exclusive=True, ownership_threshold="10")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, FR_MK, f"{art}(1)", "ne sont imposables que dans cet autre Etat"),
            exclusive=True)

    t = sd.treaty(mk, ae, name="Agreement between North Macedonia and the UAE (2015)",
                  signed=date(2015, 10, 26), in_force=date(2017, 2, 7), src=Src(
                      "UJP — treaty rate table (official)", MK_TABLE, None,
                      "United Arab Emirates|63/2016|07.02.2017|01.01.2018"))
    src = "North Macedonia–UAE agreement, SV RM 63/2016 (UJP scan, Macedonian text)"
    start = date(2018, 1, 1)
    for cat, art, word in (("DIVIDEND", "Article 10", "дивидендите"),
                           ("INTEREST", "Article 11", "каматата"),
                           ("ROYALTY", "Article 12", "приходите од авторските права")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, MK_AE, f"{art}(2)", "не смее да надмине повеќе од 5 проценти од бруто износот "
            f"на {word}"), max_rate="5")


def _kosovo(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, xk: Jurisdiction) -> None:
    start = date(2026, 1, 1)  # law in force ~3 Aug 2019 (15 days after publication)
    sd.cit(xk, start, Src(
        XK_SRC, XK_LAW, "Law 06/L-105 art. 7",
        "Tatimi në të ardhurat e korporatave është dhjetë përqind (10%) e të ardhurave të "
        "tatueshme."), rate="10")
    sd.wht(xk, "DIVIDEND", "0", start, Src(
        XK_SRC, XK_LAW, "Law 06/L-105 art. 8(1.8)",
        "dividenta e paguar apo pranuar për personin rezident dhe jorezident (exempt income)"))
    ir = Src(XK_SRC, XK_LAW, "Law 06/L-105 art. 31(2)",
             "interes … apo të drejta pronësore personave rezidentë dhe jo rezidentë, mbajnë në "
             "burim tatimin në shkallën dhjetë përqind (10%)")
    sd.wht(xk, "INTEREST", "10", start, ir)
    sd.wht(xk, "ROYALTY", "10", start, ir)
    sd.regime(
        xk, start,
        Src(XK_SRC, XK_LAW, "Law 06/L-105 art. 8(1.8); art. 22(6)",
            "dividenta e paguar apo pranuar për personin rezident dhe jorezident; Fitimet "
            "kapitale pranohen si të ardhura biznesi"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Dividends received (domestic and foreign) fully exempt, no holding test; share "
        "gains taxed as business income at 10%. No CFC rules. No Pillar Two law",
    )

    # France applies the 1974 Yugoslav convention to Kosovo under a succession agreement in
    # force 6 Feb 2013; ATK's own treaty list omits France. Kosovo is not in the MLI.
    t = sd.treaty(fr, xk, name="Convention between France and Yugoslavia (1974), applied to "
                  "Kosovo", signed=date(1974, 3, 28), in_force=date(2013, 2, 6), src=Src(
                      "Accord de succession d'État France–Kosovo, décret n° 2013-349 "
                      "(impots.gouv.fr)", FR_XK, None,
                      "(1) Le présent accord est entré en vigueur le 6 février 2013. — item 12: "
                      "Convention … signée à Paris le 28 mars 1974"))
    start = date(2013, 2, 6)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        FR_YU_SRC, FR_YU, "Article 10(2)(b)", "15 p. cent… dans tous les autres cas"),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        FR_YU_SRC, FR_YU, "Article 10(2)(a)", "si le bénéficiaire est une société qui dispose "
        "directement d'au moins 25 p. cent du capital"), max_rate="5", ownership_threshold="25")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            FR_YU_SRC, FR_YU, f"{art}(1)", "ne sont imposables que dans cet autre Etat"),
            exclusive=True)

    t = sd.treaty(xk, ae, name="Agreement between Kosovo and the UAE (2016)",
                  signed=date(2016, 5, 20), in_force=date(2017, 7, 3), src=Src(
                      "ATK — international agreements list", XK_TREATIES, None,
                      "Emiratet e bashkuara Arabe … 03.07 2017 [in force] 01.01.2017 "
                      "[applicable] 5% 5% 5/10%"))
    src = "Kosovo–UAE agreement, Albanian text (ATK scan)"
    start = date(2017, 1, 1)
    for cat, art in (("DIVIDEND", "Article 10"), ("INTEREST", "Article 11")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, XK_AE, f"{art}(2)", "tatimi i ngarkuar nuk duhet të kalojë 5%"), max_rate="5")
    # The Albanian art. 12(1) reads as residence-only, ATK's table says 5/10%; the English text
    # (prevailing) was not read — the higher 10% is stored.
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "ATK — international agreements list", XK_TREATIES, "Article 12",
        "Emiratet e bashkuara Arabe … 5% 5% 5/10% (Albanian art. 12(1): taxed in the other "
        "State — conflict unresolved, higher cap stored)"), max_rate="10")


def _india(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, in_: Jurisdiction) -> None:
    start = date(2026, 4, 1)
    # Section 200 regime: 22% + 10% surcharge + 4% cess = 25.168%.
    sd.cit(in_, start, Src(
        "Finance Bill 2026 — Memorandum (indiabudget.gov.in): s. 200 Income-tax Act 2025, 22% + "
        "10% surcharge + 4% cess = 25.168%", IN_MEMO, "Income-tax Act 2025 s. 200; Finance Bill "
        "2026 cl. 3(4)(b) Sl. 9",
        "The rate of income-tax rate is 22% in section 200. Surcharge would be at 10% on such "
        "tax. (Health and Education Cess at the rate of 4% of such income-tax and surcharge)"),
        rate="25.168")
    # Highest effective rate: 20% + 5% surcharge (payments over ₹10 crore) + 4% cess.
    for cat, item, text in (
        ("DIVIDEND", "(xiii)", "on income by way of dividend other than the income referred to "
         "in item (b)(xii) 20%"),
        ("INTEREST", "(iv)", "on income by way of interest payable by Government or an Indian "
         "concern on moneys borrowed or debt incurred ... in foreign currency ... 20%"),
        ("ROYALTY", "(vi)(B)", "where the agreement is made after the 31st March, 1976 20%"),
    ):
        sd.wht(in_, cat, "21.84", start, Src(
            IN_BILL_SRC, IN_BILL, f"First Schedule Part II, item 2(b){item}",
            f"{text}; surcharge ... exceeds ₹ 100000000, at the rate of 5%; cess 4% — 21.84% "
            "effective"))
    sd.regime(
        in_, start,
        Src(IN_BILL_SRC, IN_BILL, "Income-tax Act 2025 s. 148 (secondary text: taxheal.com)",
            "a domestic company receiving dividends from any other domestic company; a foreign "
            "company; or a business trust deducts them only up to dividends it distributes"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="No participation exemption: s. 148 is a pass-through deduction limited to "
        "dividends redistributed. Share gains taxed (12.5% LTCG listed). No CFC regime "
        "(POEM and GAAR instead). Income-tax Act 2025 in force 1 Apr 2026",
    )

    t = sd.treaty(fr, in_, name="Convention between France and India (1992)",
                  signed=date(1992, 9, 29), in_force=date(1994, 8, 1), src=Src(
                      "Convention France–Inde (impots.gouv.fr)", FR_IN, None,
                      "signed Paris 29 September 1992; in force 1 August 1994 (décret n° "
                      "94-670); avenant of 18 Feb 2026 not in force"))
    src = "Convention France–Inde (impots.gouv.fr)"
    start = date(1994, 8, 1)
    # Treaty-text rates are stored; the 10% MFN rates (France: BOFiP 2012; India requires a
    # notification, Nestlé SC 2023) are flagged for review, never applied.
    sd.treaty_rate(t, "DIVIDEND", "Article 11", start, Src(
        src, FR_IN, "Article 11(2)", "l'impôt ainsi établi ne peut excéder 15 p. cent du "
        "montant brut des dividendes"), max_rate="15")
    sd.treaty_rate(t, "INTEREST", "Article 12", start, Src(
        src, FR_IN, "Article 12(2)(b)", "15 p. cent ... dans tous les autres cas"),
        max_rate="15")
    sd.treaty_rate(t, "INTEREST", "Article 12", start, Src(
        src, FR_IN, "Article 12(2)(a)",
        "10 p. cent ... des intérêts payés à raison de prêts accordés ... par une entreprise qui "
        "détient directement ou indirectement au moins 10 p. cent du capital de la société qui "
        "paie les intérêts (bank loans also 10% — not modelled)"),
        max_rate="10", ownership_threshold="10")
    sd.treaty_rate(t, "ROYALTY", "Article 13", start, Src(
        src, FR_IN, "Article 13(2)", "ne peut excéder 20 p. cent"), max_rate="20")
    bofip = Src("BOI-INT-CVB-IND-20120912 (BOFiP)", FR_IN_BOFIP, "Protocole point 7 (NPF)",
                "Le taux de 15 % prévu au paragraphe 2 de l'article 11 ... est remplacé par le "
                "taux de 10 % prévu par la convention fiscale signée par l'Inde avec "
                "l'Allemagne")
    for cat in ("DIVIDEND", "INTEREST", "ROYALTY"):
        _mfn(sd, t, cat, date(1997, 4, 1), bofip,
             "Protocol point 7 MFN: France reads the dividend, non-bank interest and royalty "
             "caps as 10% from 1 Apr 1997; India requires an express notification (Nestlé SC, "
             "2023) — the treaty-text rate is stored. The 18 Feb 2026 avenant is not in force")
    sd.ppt(t, date(2020, 1, 1), Src(
        "Convention France–Inde modifiée par la CML (impots.gouv.fr)", FR_IN_MLI,
        "MLI art. 7(1)",
        "à compter du premier jour de la période d'imposition qui commence à compter du 1er "
        "octobre 2019 pour l'Inde (France: 1 Jan 2020)"))

    # The 2007 protocol reportedly set dividends at 10% flat (PwC only; text not obtained):
    # the original 1992 rates are stored.
    t = sd.treaty(in_, ae, name="Agreement between India and the UAE (1992)",
                  signed=date(1992, 4, 29), in_force=date(1993, 9, 22), src=Src(
                      "MLI position of the UAE — instrument of deposit (OECD)", MLI_AE, None,
                      "India Original 29-04-1992 (in force 22-09-1993; UAE MoF list gives "
                      "15/9/1993); protocols (a) 26-03-2007, (b) 16-04-2012 12-03-2013"))
    src = "Agreement UAE–India 1992 (UAE Ministry of Finance, scanned text)"
    start = date(1993, 9, 22)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, IN_AE, "Article 10(2)(b)", "15 per cent of the gross amount of the dividends in "
        "all other cases (2007 protocol reportedly 10% flat — unverified)"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, IN_AE, "Article 10(2)(a)", "5 per cent of the gross amount of the dividends if the "
        "beneficial owner is a company which owns at least ten percent of the shares of the "
        "company paying the dividends"), max_rate="5", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, IN_AE, "Article 11(2)(b)", "12.5 per cent of the gross amount of the interest in "
        "all other cases (5% on bank loans — not modelled)"), max_rate="12.5")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, IN_AE, "Article 12(2)", "the tax so charged shall not exceed 10% of the gross "
        "amount of such royalties"), max_rate="10")
    sd.ppt(t, date(2020, 4, 1), Src(
        "MLI position of the UAE — instrument of deposit (OECD)", MLI_AE, "MLI art. 7(1)",
        "India Original 29-04-1992 (covered by both; MLI in force UAE 01-09-2019, India "
        "01-10-2019; India WHT date 1 Apr 2020 assumed by analogy with the France text)"))


def _china(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, cn: Jurisdiction) -> None:
    start = date(2008, 1, 1)
    sd.cit(cn, start, Src(
        CN_LAW_SRC, CN_LAW, "EIT Law art. 4(1)",
        "企业所得税的税率为25％。 (15% for high/new-tech enterprises; 5% effective for small "
        "low-profit enterprises to 2027)"), rate="25")
    wht = Src(CN_REGS_SRC, CN_REGS, "EIT Regs art. 91(1); EIT Law art. 3(3), 27(5), 37",
              "非居民企业取得企业所得税法第二十七条第(五)项规定的所得，减按10%的税率征收企业所得税。")
    sd.wht(cn, "DIVIDEND", "10", start, wht)
    sd.wht(cn, "INTEREST", "10", start, wht)
    sd.wht(cn, "ROYALTY", "10", start, wht)
    sd.regime(
        cn, start,
        Src(CN_REGS_SRC, CN_REGS, "EIT Law art. 26(2); Regs art. 83",
            "是指居民企业直接投资于其他居民企业取得的投资收益…不包括连续持有居民企业公开发行并上市"
            "流通的股票不足12个月取得的投资收益。"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="Dividends between resident enterprises exempt (direct, no minimum %; listed "
        "shares 12 months); foreign dividends taxable with an indirect credit at ≥20% (Regs "
        "art. 80); share gains taxed",
    )
    sd.cfc(
        cn, start,
        Src(CN_REGS_SRC, CN_REGS, "EIT Law art. 45; Regs arts. 117-118",
            "是指低于企业所得税法第四条第一款规定税率的50% (below 50% of the 25% rate; control: "
            "each resident ≥10% of votes and together ≥50%, or de facto control)"),
        control_threshold_pct=50, low_tax_relative_pct=50, threshold_inclusive=False,
        legal_ref="EIT Law art. 45; Regs arts. 116-118",
        effect="Undistributed profits of a controlled enterprise taxed below 12.5% are deemed "
        "distributed; white-listed countries (incl. France, not the UAE), active income or "
        "profit under RMB 5m exempt.",
    )

    t = sd.treaty(fr, cn, name="Agreement between France and China (2013)",
                  signed=date(2013, 11, 26), in_force=date(2014, 12, 28), src=Src(
                      "STA Announcement 2015 No. 11 (shanghai.chinatax.gov.cn)",
                      "http://shanghai.chinatax.gov.cn/zcfw/zcfgk/ssxd/201507/t417790.html", None,
                      "根据协定第三十条的规定，协定及议定书将自2014年12月28日起生效，并适用于2015年1月1日"
                      "或以后取得的所得。"))
    start = date(2015, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        FR_CN_SRC, FR_CN, "Article 10(2)(b)", "10 per cent … in all other cases"),
        max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        FR_CN_SRC, FR_CN, "Article 10(2)(a)",
        "5 per cent of the gross amount of the dividends if the beneficial owner is a company "
        "(other than a partnership) which holds directly at least 25 per cent of the capital"),
        max_rate="5", ownership_threshold="25", end=date(2023, 1, 1))
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(2023, 1, 1), Src(
        FR_CN_SRC, FR_CN, "Article 10(2)(a); MLI art. 8",
        "holds directly at least 25 per cent of the capital (365-day holding period added by "
        "MLI art. 8)"), max_rate="5", ownership_threshold="25", min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        FR_CN_SRC, FR_CN, "Article 11(2)", "10 per cent of the gross amount of the interest"),
        max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        FR_CN_SRC, FR_CN, "Article 12(2); Protocol para. 6",
        "10 per cent (equipment royalties taxed on 60 per cent of the gross amount — not "
        "modelled)"), max_rate="10")
    sd.ppt(t, date(2023, 1, 1), Src(
        "China–France agreement, STA page", "https://www.chinatax.gov.cn/chinatax/n810341/"
        "n810770/c1152674/content.html", "MLI art. 7(1)",
        "…是直接或间接产生该优惠的安排或交易的主要目的之一，则不应对该项所得给予该优惠… "
        "(withholding taxes: taxable events from 2023-01-01)"))

    # Entry into force not confirmed officially (secondary sources: 1994): not applied.
    t = sd.treaty(cn, ae, name="Agreement between China and the UAE (1993)",
                  signed=date(1993, 7, 1), in_force=None, src=Src(
                      "China–UAE agreement (STA page)", "https://www.chinatax.gov.cn/chinatax/"
                      "n810341/n810770/c1153711/content.html", None,
                      "本协定于一九九三年七月一日在阿布扎比签订 (entry into force: 30th day "
                      "after the exchange of notes — date not confirmed)"))
    src = "China–UAE agreement, MLI synthesised text (guangdong.chinatax.gov.cn)"
    start = date(1993, 7, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, CN_AE, "Article 10(2)", "…不应超过股息总额的百分之七"), max_rate="7")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, CN_AE, "Article 11(2)", "…不应超过利息总额的百分之七"), max_rate="7")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, CN_AE, "Article 12(2)", "…不应超过特许权使用费总额的百分之十"), max_rate="10")
    sd.ppt(t, date(2023, 1, 1), Src(
        src, CN_AE, "MLI art. 7(1)", "MLI in force China 2022-09-01, UAE 2019-09-01 — "
        "withholding taxes from 2023-01-01"))
