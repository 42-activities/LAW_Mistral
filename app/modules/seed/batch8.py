"""P8 batch 8: remaining EU members (SK, HR, SI, EE, FI, LV, LT), Serbia and the CIS
(KZ, UZ, MD, AZ, AM).

Figures were sourced on 2026-10-05 from the texts cited on each `Src` and are stored as
`unreviewed` until a named reviewer confirms them (spec §10). Research notes:
docs/superpowers/plans/2026-10-05-p8-batch8.md.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import JurisdictionGroup
from app.modules.seed.builder import Seeder, Src

EU_URL = "https://european-union.europa.eu/principles-countries-history/eu-countries/{}_en"
SK_ZDP = "https://static.slov-lex.sk/static/SK/ZZ/2003/595/20260101.html"
SK_SRC = "Zákon č. 595/2003 Z. z. o dani z príjmov, version in force from 1 Jan 2026 (Slov-Lex)"
FR_SK = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/slovaquie/"
    "convention_avec_la_slovaquie_modifiee_par_la_cml.pdf"
)
KZ_TC = "http://insecure.zan.kz/rus/docs/K2500000214"
KZ_SRC = "Налоговый кодекс РК от 18.07.2025 № 214-VIII (adilet mirror, version 01.07.2026)"
FR_KZ = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/kazakhstan/"
    "kazakhstan_modifiee_cml.pdf"
)
KZ_AE = "http://insecure.zan.kz/rus/docs/Z1300000134"
UZ_TC = "https://lex.uz/docs/4674902"
UZ_SRC = "Солиқ кодекси / Налоговый кодекс РУз (ZRU-599), LexUz"
FR_UZ = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/ouzbekistan/"
    "ouzbekistan_convention-avec-l-ouzbekistan_fd_2348.pdf"
)
UZ_AE = "https://mof.gov.ae/wp-content/uploads/2025/06/UAE-Uzbekistan-DTA.pdf"
LV_CIT = "https://likumi.lv/ta/id/292700"
LV_SRC = "Uzņēmumu ienākuma nodokļa likums, consolidated from 01.01.2026 (likumi.lv)"
FR_LV = (
    "https://www.impots.gouv.fr/"
    "version-consolidee-de-la-convention-avec-la-lettonie-modifiee-par-la-convention-multilaterale"
)
LV_FM = "https://fm.gov.lv/lv/media/24146/download?attachment="
LV_AE = "https://likumi.lv/ta/en/starptautiskie-ligumi/id/19"
LT_PMI = "https://e-seimas.lrs.lt/portal/legalAct/lt/TAD/TAIS.157066/asr"
LT_SRC = "Pelno mokesčio įstatymas Nr. IX-675, consolidated 2026-05-19 (e-seimas)"
FR_LT = "https://www.impots.gouv.fr/filesmedia10conventionslituanieconventionaveclalituaniemodifieeparlacmlpdf"
LT_AE = "https://e-seimas.lrs.lt/portal/legalAct/lt/TAD/TAIS.460811"
EE_TUMS = "https://www.riigiteataja.ee/akt/109072026066"
EE_SRC = "Tulumaksuseadus, RT I, 09.07.2026, 66 (Riigi Teataja)"
FR_EE = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/estonie/"
    "estonie_convention-avec-l-estonie_fd_1428.pdf"
)
EE_AE = "https://www.riigiteataja.ee/akt/206032012004"
FI_TVL = "https://www.finlex.fi/fi/lainsaadanto/1992/1535"
FI_LVL = "https://www.finlex.fi/fi/lainsaadanto/1978/627"
FI_EVL = "https://www.finlex.fi/fi/lainsaadanto/1968/360"
FR_FI_OLD = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/finlande/"
    "version-consolidee-cml-finlande.pdf"
)
FR_FI_NEW = "https://www.finlex.fi/fi/valtiosopimukset/sopimussarja/2026/34"
FI_AE = "https://www.finlex.fi/en/treaties/tax-treaties/1997/90"
MD_GUIDE = "https://invest.gov.md/wp-content/uploads/2026/06/Investor-Guide-EN-2026.pdf"
MD_SRC = "Moldova Investment Agency, Investor Guide 2026 (official summary — secondary to the law)"
FR_MD = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/moldavie/"
    "convention_franco-moldave.pdf"
)
MD_AE = "https://mof.gov.ae/wp-content/uploads/2025/06/UAE-Moldova-DTA.pdf"
AM_TC = "https://www.arlis.am/hy/acts/109017/latest"
AM_SRC = "ՀՀ հարկային օրենսգիրք (RA Tax Code), arlis.am official consolidation"
FR_AM = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/armenie/"
    "27156_armenie_convention_version-consolidee_cml.pdf"
)
AM_AE = "https://www.arlis.am/hy/acts/29928/latest"
AZ_TC = "https://e-qanun.az/frameworks/46/f_46948.html"
AZ_SRC = "Vergi Məcəlləsi (Tax Code of Azerbaijan), e-qanun.az consolidation 2026-09-18"
FR_AZ = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/azerbaidjan/"
    "nid_28290_azerbaidjan_consolidee_cml.pdf"
)
AZ_AE = "https://mof.gov.ae/wp-content/uploads/2025/06/UAE-Azerbaijan-DTA.pdf"
RS_ZPDP = (
    "https://www.purs.gov.rs/upload/media/2026/9/18/760987/"
    "Закон_о_порезу_на_добит_правних_лица.pdf"
)
RS_SRC = "Закон о порезу на добит правних лица, PURS consolidation 18.9.2026"
FR_RS = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/serbie/"
    "serbie_modifiee_cml_20190805.pdf"
)
RS_AE = "https://mof.gov.ae/wp-content/uploads/2025/06/UAE-Serbia-DTA.pdf"
HR_ZPD = "https://www.zakon.hr/z/99/Zakon-o-porezu-na-dobit"
HR_SRC = "Zakon o porezu na dobit, NN 177/04 … 151/25 (zakon.hr consolidation — secondary)"
HR_NN114 = "https://narodne-novine.nn.hr/clanci/sluzbeni/2023_10_114_1613.html"
FR_HR = "https://www.impots.gouv.fr/croatie"
HR_AE = "https://narodne-novine.nn.hr/clanci/medunarodni/2017_11_13_71.html"
SI_ZORZFS = "https://www.uradni-list.si/glasilo-uradni-list-rs/vsebina/2023-01-4011"
SI_ZDDPO = "https://www.uradni-list.si/glasilo-uradni-list-rs/vsebina/2006-01-5014"
SI_SRC = "ZDDPO-2, Ur.l. RS 117/2006 original text (current consolidation on pisrs.si blocked)"
FR_SI = "https://www.impots.gouv.fr/slovenie"
SI_AE = "https://www.uradni-list.si/glasilo-uradni-list-rs/vsebina/2014-02-0028"
SK_AE = "https://static.slov-lex.sk/static/SK/ZZ/2017/58/20170321.html"


def seed_batch8(session: Session) -> None:
    sd = Seeder(session)
    fr = sd.jurisdiction("FR", "France")
    ae = sd.jurisdiction("AE", "United Arab Emirates")
    eu = sd.group("EU", "European Union member states")

    sk = sd.jurisdiction("SK", "Slovakia")
    sd.member(eu, sk, date(2004, 5, 1), Src(
        "Slovakia — EU member country profile (european-union.europa.eu)",
        EU_URL.format("slovakia"), None, "EU Member State: since 1 May 2004"))
    _slovakia(sd, fr, ae, sk, eu)
    _eu_annex_i(sd)
    hr = sd.jurisdiction("HR", "Croatia")
    sd.member(eu, hr, date(2013, 7, 1), Src(
        "Croatia — EU member country profile (european-union.europa.eu)",
        EU_URL.format("croatia"), None, "EU Member State : since 1 July 2013"))
    _croatia(sd, fr, ae, hr, eu)
    si = sd.jurisdiction("SI", "Slovenia")
    sd.member(eu, si, date(2004, 5, 1), Src(
        "Slovenia — EU member country profile (european-union.europa.eu)",
        EU_URL.format("slovenia"), None, "EU Member State: since 1 May 2004"))
    _slovenia(sd, fr, ae, si, eu)
    ee = sd.jurisdiction("EE", "Estonia")
    sd.member(eu, ee, date(2004, 5, 1), Src(
        "Estonia — EU member country profile (european-union.europa.eu)",
        EU_URL.format("estonia"), None, "EU Member State: since 1 May 2004"))
    _estonia(sd, fr, ae, ee, eu)
    fi = sd.jurisdiction("FI", "Finland")
    sd.member(eu, fi, date(1995, 1, 1), Src(
        "Finland — EU member country profile (european-union.europa.eu)",
        EU_URL.format("finland"), None, "EU Member State: since 1 January 1995"))
    _finland(sd, fr, ae, fi, eu)
    for code, name, slug in (("LV", "Latvia", "latvia"), ("LT", "Lithuania", "lithuania")):
        j = sd.jurisdiction(code, name)
        sd.member(eu, j, date(2004, 5, 1), Src(
            f"{name} — EU member country profile (european-union.europa.eu)",
            EU_URL.format(slug), None, "EU Member State: since 1 May 2004"))
    _latvia(sd, fr, ae, sd.jurisdiction("LV", "Latvia"))
    _lithuania(sd, fr, ae, sd.jurisdiction("LT", "Lithuania"), eu)
    _moldova(sd, fr, ae, sd.jurisdiction("MD", "Moldova"))
    _armenia(sd, fr, ae, sd.jurisdiction("AM", "Armenia"))
    _azerbaijan(sd, fr, ae, sd.jurisdiction("AZ", "Azerbaijan"))
    _serbia(sd, fr, ae, sd.jurisdiction("RS", "Serbia"))
    kz = sd.jurisdiction("KZ", "Kazakhstan")
    _kazakhstan(sd, fr, ae, kz)
    sd.listing(kz, "GLOBAL_FORUM_RATING", "partially_compliant", date(2018, 1, 1), None, Src(
        "OECD Global Forum EOIR ratings table (embedded on oecd.org)",
        "https://datawrapper.dwcdn.net/LGXCI/73/dataset.csv", None,
        "Kazakhstan (Round 2), 2018, Partially Compliant"))
    _uzbekistan(sd, fr, ae, sd.jurisdiction("UZ", "Uzbekistan"))


def _slovakia(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, sk: Jurisdiction, eu: JurisdictionGroup
) -> None:
    start = date(2025, 1, 1)
    # Rates depend on revenue (not profit): 10% up to EUR 100k, 24% above EUR 5m. The general
    # 21% rate is stored; the engine's brackets are profit-based.
    sd.cit(sk, start, Src(
        SK_SRC, SK_ZDP, "ZDP § 15 písm. b) bod 1",
        "21 % pre daňovníka neuvedeného v bode 1a. alebo bode 1c. (10% up to EUR 100,000 of "
        "revenue; 24% above EUR 5,000,000 of revenue)"), rate="21")
    sd.wht(sk, "DIVIDEND", "0", start, Src(
        SK_SRC, SK_ZDP, "ZDP § 12 ods. 7 písm. c)",
        "Predmetom dane nie je [...] podiel na zisku (dividenda) [...] v rozsahu, v akom nie je "
        "daňovým výdavkom u daňovníka vyplácajúceho (outside the tax base; 35% to residents of "
        "non-cooperating states)"))
    ir = Src(SK_SRC, SK_ZDP, "ZDP § 43 ods. 1 písm. b)",
             "19 % z príjmov podľa odsekov 2 a 3 (35% if paid to a non-cooperating state)")
    sd.wht(sk, "INTEREST", "19", start, ir)
    sd.wht(sk, "ROYALTY", "19", start, ir)
    ird = Src(SK_SRC, SK_ZDP, "ZDP § 13 ods. 2 písm. f), h)",
              "počas obdobia najmenej dvadsiatich štyroch mesiacov [...] najmenej 25 % (EU "
              "associated company, 24 months)")
    for cat in ("INTEREST", "ROYALTY"):
        sd.exemption(
            sk, cat, eu, start, ird, min_holding_pct="25", min_holding_months=24,
            legal_ref="ZDP § 13 ods. 2",
            description="Interest and Royalties Directive: associated EU company (≥25%, 24 months)",
        )
    sd.regime(
        sk, start,
        Src(SK_SRC, SK_ZDP, "ZDP § 12 ods. 7 písm. c); § 13c",
            "Predmetom dane nie je [...] podiel na zisku (dividenda) — share gains exempt at "
            "≥10% held 24 months with substance in Slovakia (§ 13c)"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Dividends outside the tax base (unless deductible at the payer or from a "
        "non-cooperating state); share gains exempt at ≥10% for 24 months with substance",
    )
    sd.cfc(
        sk, start,
        Src(SK_SRC, SK_ZDP, "ZDP § 17h",
            "viac ako 50 % [...] je nižšia ako rozdiel medzi daňou [...] vypočítanou podľa § 17 "
            "až 29 a daňou [...], ktorú by platila [...] v zahraničí"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="ZDP § 17h",
        effect="Income of a >50%-controlled entity taxed below half the Slovak tax is included "
        "(non-genuine arrangements, ATAD model B).",
    )

    t = sd.treaty(fr, sk, name="Convention between France and Czechoslovakia (1973), applied "
                  "by Slovakia", signed=date(1973, 6, 1), in_force=date(1975, 1, 25), src=Src(
                      "BOI-INT-CVB-SVK (BOFiP)",
                      "https://bofip.impots.gouv.fr/bofip/400-PGP.html/"
                      "identifiant=BOI-INT-CVB-SVK-20120912", None,
                      "Cette convention est entrée en vigueur le 25 janvier 1975 [...] continue "
                      "à produire ses pleins effets à l'égard de la Slovaquie"))
    start = date(1976, 1, 1)
    src = "Convention France–Slovaquie modifiée par la CML (impots.gouv.fr)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_SK, "Article 10(2)",
        "l'impôt ainsi établi ne peut excéder 10 p. cent du montant brut des dividendes"),
        max_rate="10")
    sd.treaty_rate(t, "INTEREST", "Article 12", start, Src(
        src, FR_SK, "Article 12(1)", "ne sont imposables que dans cet autre Etat"),
        exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 13", start, Src(
        src, FR_SK, "Article 13(2)",
        "ne peut excéder 5 p. cent du montant brut des redevances"), max_rate="5")
    sd.ppt(t, date(2019, 1, 1), Src(
        src, FR_SK, "MLI art. 7(1)",
        "un avantage [...] ne sera pas accordé [...] l'un des objets principaux d'un montage — "
        "CML en vigueur le 1er janvier 2019 pour les deux États"))

    # UAE treaty: art. 27 limitation-on-benefits (not modelled); not an MLI covered agreement.
    t = sd.treaty(sk, ae, name="Agreement between Slovakia and the UAE (2015)",
                  signed=date(2015, 12, 21), in_force=date(2017, 4, 1), src=Src(
                      "Zmluva SR–SAE, 58/2017 Z. z. (Slov-Lex)", SK_AE, "Article 28",
                      "Zmluva nadobudne platnosť 1. apríla 2017 v súlade s čl. 28 ods. 2"))
    start = date(2018, 1, 1)
    src = "Zmluva SR–SAE, 58/2017 Z. z. (Slov-Lex)"
    sd.treaty_rate(t, "DIVIDEND", "Article 11", start, Src(
        src, SK_AE, "Article 11(1)", "podliehajú zdaneniu len v tomto druhom štáte"),
        exclusive=True)
    sd.treaty_rate(t, "INTEREST", "Article 12", start, Src(
        src, SK_AE, "Article 12(2)", "nepresiahne 10 % hrubej sumy úrokov"), max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 13", start, Src(
        src, SK_AE, "Article 13(2)", "nepresiahne 10 % hrubej sumy licenčných poplatkov"),
        max_rate="10")


def _kazakhstan(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, kz: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(kz, start, Src(
        KZ_SRC, KZ_TC, "НК РК ст. 357 п. 2 пп. 5)",
        "от иной деятельности [...] – 20 процентов"), rate="20")
    # 5% applies to a ≥25% holder only up to 230,000 MRP of dividends a year: the general 15%
    # is stored.
    sd.wht(kz, "DIVIDEND", "15", start, Src(
        KZ_SRC, KZ_TC, "НК РК ст. 682 п. 1 пп. 5), 6)",
        "доходы от прироста стоимости, дивиденды, вознаграждения, роялти [...] – 15 процентов "
        "(5% for a ≥25% holder up to 230,000 MRP; 20% to low-tax states)"))
    sd.wht(kz, "INTEREST", "10", start, Src(
        KZ_SRC, KZ_TC, "НК РК ст. 682 п. 1 пп. 7)",
        "вознаграждения по кредитам (займам), долговым ценным бумагам – 10 процентов"))
    sd.wht(kz, "ROYALTY", "15", start, Src(
        KZ_SRC, KZ_TC, "НК РК ст. 682 п. 1 пп. 5)",
        "дивиденды, вознаграждения, роялти [...] – 15 процентов"))
    sd.regime(
        kz, start,
        Src(KZ_SRC, KZ_TC, "НК РК ст. 255 п. 1 пп. 1)",
            "дивиденды, кроме полученных постоянным учреждением юридического лица – "
            "нерезидента (deducted from aggregate income)"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Dividends deducted with no holding test; gains exempt only on resident "
        "non-subsoil shares held >3 years (art. 337) — foreign share gains taxed",
    )
    sd.cfc(
        kz, start,
        Src(KZ_SRC, KZ_TC, "НК РК ст. 332, 335",
            "25 и более процентов долей участия [...] эффективная ставка налога на прибыль "
            "[...] составляет менее 10 процентов"),
        control_threshold_pct=25, low_tax_relative_pct=50, threshold_inclusive=True,
        legal_ref="НК РК ст. 332",
        effect="Income of a ≥25%-controlled entity with an effective rate below 10% (half the "
        "20% rate) is taxed at 20%.",
    )

    t = sd.treaty(fr, kz, name="Convention between France and Kazakhstan (1998)",
                  signed=date(1998, 2, 3), in_force=date(2000, 7, 1), src=Src(
                      "Convention France–Kazakhstan modifiée par la CML (impots.gouv.fr)", FR_KZ,
                      None, "signée à Paris le 3 février 1998 [...] entrée en vigueur le 1er "
                      "juillet 2000"))
    src = "Convention France–Kazakhstan modifiée par la CML (impots.gouv.fr)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(2001, 1, 1), Src(
        src, FR_KZ, "Article 10(2)(b)", "15 p. cent du montant brut des dividendes dans tous "
        "les autres cas"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(2021, 1, 1), Src(
        src, FR_KZ, "Article 10(2)(a); MLI art. 8",
        "si le bénéficiaire est une société qui détient directement ou indirectement au moins "
        "10 p. cent du capital [...] tout au long d'une période de 365 jours"),
        max_rate="5", ownership_threshold="10", min_holding_days=365)
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, date(2001, 1, 1), Src(
            src, FR_KZ, f"{art}(2)", "ne peut excéder 10 p. cent du montant brut"),
            max_rate="10")
    sd.ppt(t, date(2021, 1, 1), Src(
        src, FR_KZ, "MLI art. 7(1)",
        "un avantage [...] ne sera pas accordé [...] — si le fait générateur de ces impôts "
        "intervient à compter du 1er janvier 2021"))

    t = sd.treaty(kz, ae, name="Convention between Kazakhstan and the UAE (2008)",
                  signed=date(2008, 12, 22), in_force=date(2013, 11, 27), src=Src(
                      "UAE Ministry of Finance — list of double taxation agreements",
                      "https://mof.gov.ae/wp-content/uploads/2023/08/Avoidance-of-Double-"
                      "Taxation-Agreements1.pdf", None, "Kazakhstan [...] 27/11/2013"))
    start = date(2014, 1, 1)
    src = "Закон РК от 04.10.2013 № 134-V о ратификации Конвенции РК–ОАЭ (adilet mirror)"
    # No general dividend cap: below a 10% holding the domestic rate applies.
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, KZ_AE, "Article 10(2)",
        "если фактическим владельцем дивидендов является компания (иная, чем партнерство), "
        "которая прямо владеет не менее, чем 10 процентами капитала — 5 процентов"),
        max_rate="5", ownership_threshold="10")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, KZ_AE, f"{art}(2)", "не должен превышать 10 процентов от общей суммы"),
            max_rate="10")
    sd.ppt(t, date(2021, 1, 1), Src(
        "MLI positions of Kazakhstan and the UAE — instruments of deposit (OECD)",
        "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/"
        "beps-mli-position-kazakhstan-instrument-deposit.pdf", "MLI art. 7(1)",
        "United Arab Emirates — covered by both (KZ No. 50, UAE No. 53); MLI in force for "
        "Kazakhstan 1 Oct 2020"))


def _uzbekistan(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, uz: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(uz, start, Src(
        UZ_SRC, UZ_TC, "НК РУз ст. 337 п. 12",
        "Қолган солиқ тўловчилар [...] 15 (other taxpayers: 15%)"), rate="15")
    sd.cit(uz, start, Src(
        UZ_SRC, UZ_TC, "НК РУз ст. 337 п. 11",
        "Дивидендлар тарзидаги даромадлар 5 (dividend income: 5%)"), rate="5",
        category="DIVIDEND")
    dir_ = Src(UZ_SRC, UZ_TC, "НК РУз ст. 353",
               "Дивидендлар ва фоизлар 10 (dividends and interest: 10%)")
    sd.wht(uz, "DIVIDEND", "10", start, dir_)
    sd.wht(uz, "INTEREST", "10", start, dir_)
    sd.wht(uz, "ROYALTY", "20", start, Src(
        UZ_SRC, UZ_TC, "НК РУз ст. 353, 351",
        "иные доходы — 20 (royalties are taxed as other income)"))
    sd.regime(
        uz, start,
        Src(UZ_SRC, UZ_TC, "НК РУз ст. 343",
            "не вправе уменьшить сумму налога [...] на сумму налога, уплаченную по месту "
            "нахождения источника дохода (foreign dividends taxed at 5%)"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="No participation exemption: foreign dividends taxed at 5%, share gains at 15%",
    )
    sd.cfc(
        uz, start,
        Src(UZ_SRC, UZ_TC, "НК РУз ст. 40, 204",
            "доля участия которого в иностранной компании составляет более 25 процентов [...] "
            "не менее размера налоговой ставки [...] пункте 12 статьи 337"),
        control_threshold_pct=25, low_tax_relative_pct=100, legal_ref="НК РУз ст. 40, 204",
        effect="Profits of a >25%-held foreign company taxed below the 15% Uzbek rate are "
        "included (exemptions for active companies and treaty-state banks).",
    )

    # Uzbekistan is not an MLI signatory: no PPT.
    t = sd.treaty(fr, uz, name="Convention between France and Uzbekistan (1996)",
                  signed=date(1996, 4, 22), in_force=date(2003, 10, 1), src=Src(
                      "Convention France–Ouzbékistan (impots.gouv.fr)", FR_UZ, None,
                      "La présente convention est entrée en vigueur le 1er octobre 2003"))
    start = date(2004, 1, 1)
    src = "Convention France–Ouzbékistan (impots.gouv.fr)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_UZ, "Article 10(2)(b)", "10 % du montant brut des dividendes dans tous les "
        "autres cas"), max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_UZ, "Article 10(2)(a)",
        "si le bénéficiaire effectif est une société qui détient directement ou indirectement "
        "au moins 10 % du capital"), max_rate="5", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, FR_UZ, "Article 11(2)", "ne peut excéder 5 % du montant brut des intérêts (0% "
        "on bank loans)"), max_rate="5")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, FR_UZ, "Article 12(1)", "ne sont imposables que dans cet autre Etat"),
        exclusive=True)

    t = sd.treaty(uz, ae, name="Agreement between Uzbekistan and the UAE (2007)",
                  signed=date(2007, 10, 26), in_force=date(2011, 2, 25), src=Src(
                      "UAE Ministry of Finance — UAE–Uzbekistan DTA", UZ_AE, None,
                      "entry into force 25/2/2011"))
    start = date(2012, 1, 1)
    src = "Agreement UAE–Uzbekistan (UAE Ministry of Finance)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, UZ_AE, "Article 10(2)(b)", "15 per cent of the gross amount of the dividends in "
        "all other cases"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, UZ_AE, "Article 10(2)(a)",
        "if the beneficial owner is a company (other than partnership) which holds directly at "
        "least 25 per cent of the capital"), max_rate="5", ownership_threshold="25")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, UZ_AE, f"{art}(2)", "shall not exceed 10 per cent of the gross amount"),
            max_rate="10")


def _latvia(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, lv: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    # Distribution tax: 20% of the distribution grossed up by 0.8 — 20% of profit when profits
    # are fully distributed; retained profits are untaxed (deferral not modelled).
    sd.cit(lv, start, Src(
        LV_SRC, LV_CIT, "UIN likums 3. panta (1) daļa, 4. panta (9) daļa",
        "Nodokļa likme ir 20 procenti no aprēķinātās ar nodokli apliekamās bāzes [...] dala ar "
        "koeficientu 0,8 (tax on distributed profits only)"), rate="20")
    no_wht = Src(LV_SRC, LV_CIT, "UIN likums 5. panta (1) daļa",
                 "Art. 5(1) lists the payments subject to withholding — management and "
                 "consultancy fees, Latvian real estate — dividends, interest and royalties are "
                 "not among them (except to low-tax jurisdictions, 20%)")
    for cat in ("DIVIDEND", "INTEREST", "ROYALTY"):
        sd.wht(lv, cat, "0", start, no_wht)
        sd.consequence(
            lv, "EU_TAX_ANNEX_I", cat, "20", date(2023, 7, 1), Src(
                "UIN likums 5. panta (6), (8) daļa; MK noteikumi Nr. 333 (27.06.2023)",
                "https://likumi.lv/ta/id/343175", "MK noteikumi Nr. 333, 2. punkts",
                "zemu nodokļu vai beznodokļu valstīs vai teritorijās — Eiropas Savienības "
                "Padomes [...] secinājumiem (I pielikuma aktuālā redakcija)"),
            legal_ref="UIN likums 5. panta (6), (8) daļa",
            description=f"20% withholding on {cat.lower()} to a jurisdiction on Annex I of the "
            "EU list (Cabinet Regulation 333)",
        )
    sd.regime(
        lv, start,
        Src(LV_SRC, LV_CIT, "UIN likums 6. panta (1) daļa; 13. panta (1) daļa",
            "tā rezidences valstī ir uzņēmumu ienākuma nodokļa maksātājs [...] tiešās "
            "līdzdalības akciju [...] kuru turēšanas periods [...] ir vismaz 36 mēneši"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=True,
        exempt_share_pct=100,
        notes="Dividends from CIT-paying companies reduce the distribution base (no holding "
        "test); share gains exempt after 36 months. CFC (art. 6.1): >50% control, non-genuine "
        "arrangements only, no low-tax test — not seeded",
    )

    t = sd.treaty(fr, lv, name="Convention between France and Latvia (1997)",
                  signed=date(1997, 4, 14), in_force=date(2001, 5, 1), src=Src(
                      "Latvian Ministry of Finance — tax treaty status table (15.01.2026)",
                      LV_FM, None, "14 Francija 13.04.95. 14.04.97. 01.05.01. 01.01.02."))
    src = "Convention France–Lettonie modifiée par la CML (impots.gouv.fr)"
    start = date(2002, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_LV, "Article 10(2)(b)", "15 p. cent [...] dans tous les autres cas"),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_LV, "Article 10(2)(a)",
        "5 p. cent [...] si le bénéficiaire effectif est une société qui détient directement au "
        "moins 10 p. cent du capital"), max_rate="5", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, FR_LV, "Article 11(2)", "ne peut excéder 10 p. cent du montant brut des intérêts"),
        max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", date(2017, 7, 5), Src(
        "BOI-INT-CVB-LVA-20241016 (BOFiP)",
        "https://bofip.impots.gouv.fr/bofip/3245-PGP.html/identifiant=BOI-INT-CVB-LVA-20241016",
        "Protocol points 8-9 (MFN)",
        "Ces règles s'appliquent à compter du 5 juillet 2017 (royalties taxable only in the "
        "residence State under the MFN clause)"), exclusive=True)
    sd.ppt(t, date(2021, 1, 1), Src(
        src, FR_LV, "MLI art. 7(1)",
        "s'agissant des impôts prélevés à la source [...] si le fait générateur [...] intervient "
        "à compter du 1er janvier 2021"))

    t = sd.treaty(lv, ae, name="Convention between Latvia and the UAE (2012)",
                  signed=date(2012, 3, 11), in_force=date(2013, 6, 11), src=Src(
                      "Latvian Ministry of Finance — tax treaty status table (15.01.2026)",
                      LV_FM, None,
                      "5 Apvienotie Arābu Emirāti 20.02.09. 11.03.12. 11.06.13. 01.01.14."))
    start = date(2014, 1, 1)
    src = "Convention Latvia–UAE (likumi.lv)"
    for cat, art, rate in (("DIVIDEND", "Article 10", "5"), ("INTEREST", "Article 11", "2.5"),
                           ("ROYALTY", "Article 12", "5")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, LV_AE, f"{art}(2)", f"shall not exceed {rate.replace('.', ',')} per cent of the "
            "gross amount"), max_rate=rate)
    sd.ppt(t, date(2021, 1, 1), Src(
        "MLI position of Latvia — instrument of deposit (OECD)",
        "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/"
        "beps-mli-position-latvia-instrument-deposit.pdf", "MLI art. 7(1)",
        "United Arab Emirates — covered by both; MLI in force for Latvia 1 Feb 2020"))


def _lithuania(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, lt: Jurisdiction, eu: JurisdictionGroup
) -> None:
    sd.cit(lt, date(2025, 1, 1), Src(
        "Įstatymas Nr. XIV-2774 (TAR 2024-12078, e-seimas)",
        "https://e-seimas.lrs.lt/portal/legalAct/lt/TAD/1cf405e22f9d11efb121d2fe3a0eff27",
        "PMĮ 5 str. 1 d. 1 p.", "taikant 16 procentų mokesčio tarifą [...] 2025 metų ir "
        "vėlesnių mokestinių laikotarpių"), rate="16", end=date(2026, 1, 1))
    start = date(2026, 1, 1)
    sd.cit(lt, start, Src(
        LT_SRC, LT_PMI, "PMĮ 5 str. 1 d. 1 p.",
        "apmokestinamasis pelnas apmokestinamas taikant 17 procentų mokesčio tarifą"),
        rate="17")
    sd.wht(lt, "DIVIDEND", "17", start, Src(
        LT_SRC, LT_PMI, "PMĮ 34 str. 1 d.",
        "dividendai apmokestinami taikant 17 procentų (exempt at ≥10% of voting shares held "
        "12 months unless the recipient is in a target territory, art. 34(2))"))
    ir = Src(LT_SRC, LT_PMI, "PMĮ 5 str. 1 d. 2 p.",
             "10 procentų (interest to EEA or treaty-country recipients not taxed)")
    sd.wht(lt, "INTEREST", "10", start, ir)
    sd.wht(lt, "ROYALTY", "10", start, ir)
    sd.exemption(
        lt, "DIVIDEND", eu, start,
        Src(LT_SRC, LT_PMI, "PMĮ 34 str. 2 d.",
            "ne mažiau kaip 10 procentų balsus suteikiančių akcijų [...] ne trumpiau kaip 12 "
            "mėnesių"),
        min_holding_pct="10", min_holding_months=12, legal_ref="PMĮ 34 str. 2 d.",
        description="Dividends to a ≥10% holder for 12 months exempt (not target territories)",
    )
    sd.exemption(
        lt, "INTEREST", eu, start,
        Src(LT_SRC, LT_PMI, "PMĮ 4 str. 4 d.; 5 str. 1 d. 2 p.",
            "interest to EEA residents is not taxed (neapmokestinamos)"),
        min_holding_pct=None, min_holding_months=None, legal_ref="PMĮ 5 str. 1 d. 2 p.",
        description="Interest paid to EEA/treaty-country companies not taxed",
    )
    sd.exemption(
        lt, "ROYALTY", eu, start,
        Src(LT_SRC, LT_PMI, "PMĮ 37-1 str.",
            "at least 25% [...] for at least 2 years without interruption (Directive "
            "2003/49/EC companies)"),
        min_holding_pct="25", min_holding_months=24, legal_ref="PMĮ 37-1 str.",
        description="Interest and Royalties Directive: associated EU company (≥25%, 2 years)",
    )
    sd.regime(
        lt, start,
        Src(LT_SRC, LT_PMI, "PMĮ 35 str. 2-3 d.; 12 str. 15 p.",
            "EEA dividends exempt if the payer's profits are subject to CIT; others at ≥10% for "
            "12 months; share gains at >10% held 2 years"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=10, min_holding_period_months=12, subject_to_tax_condition=True,
        exempt_share_pct=100,
        notes="Non-EEA dividends exempt at ≥10% for 12 months (EEA: no holding test); share "
        "gains exempt at >10% for 2 years; target territories excluded",
    )
    sd.cfc(
        lt, start,
        Src(LT_SRC, LT_PMI, "PMĮ 39 str. 1 d.",
            "mažesnis negu 50 procentų faktinio pelno mokesčio, kuris būtų apskaičiuotas [...] "
            "pagal šio Įstatymo nuostatas"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="PMĮ 39 str.",
        effect="Passive income (>1/3) of a >50%-controlled entity taxed below half the "
        "Lithuanian tax, or any income in a target territory, is included.",
    )

    t = sd.treaty(fr, lt, name="Convention between France and Lithuania (1997)",
                  signed=date(1997, 7, 7), in_force=date(2001, 5, 1), src=Src(
                      "BOI-INT-CVB-LTU-20231004 (BOFiP)",
                      "https://bofip.impots.gouv.fr/bofip/425-PGP.html/"
                      "identifiant=BOI-INT-CVB-LTU-20231004", None,
                      "Cette convention est entrée en vigueur le 1er mai 2001"))
    src = "Convention France–Lituanie modifiée par la CML (impots.gouv.fr)"
    start = date(2002, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_LT, "Article 10(2)(b)", "15 p. cent [...] dans tous les autres cas"),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_LT, "Article 10(2)(a)",
        "5 p. cent [...] si le bénéficiaire effectif est une société qui : i) détient "
        "directement au moins 10 p. cent du capital"), max_rate="5", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, FR_LT, "Article 11(2)", "ne peut excéder 10 p. cent du montant brut des intérêts"),
        max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", date(2018, 8, 31), Src(
        src, FR_LT, "Article 12(1) (MFN, Protocol)",
        "ne sont imposables que dans cet autre Etat (from 31 August 2018 under the MFN clause)"),
        exclusive=True)
    sd.ppt(t, date(2019, 1, 1), Src(
        src, FR_LT, "MLI art. 7(1)",
        "si le fait générateur de ces impôts intervient à compter du premier jour de l'année "
        "civile qui commence à compter du 1er janvier 2019"))

    t = sd.treaty(lt, ae, name="Convention between Lithuania and the UAE (2013)",
                  signed=date(2013, 6, 30), in_force=date(2014, 12, 19), src=Src(
                      "Convention Lithuania–UAE (e-seimas, TAR 2014-04871)", LT_AE, None,
                      "Įsigaliojo 2014-12-19"))
    start = date(2015, 1, 1)
    src = "Convention Lithuania–UAE (e-seimas)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, LT_AE, "Article 10(2)(b)", "5 per cent [...] in all other cases"), max_rate="5")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, LT_AE, "Article 10(2)(a)",
        "0 per cent [...] if the beneficial owner is a company (other than a partnership) which "
        "holds directly at least 10 per cent of the capital"), max_rate="0",
        ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, LT_AE, "Article 11(1)", "shall be taxable only in that other State"),
        exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, LT_AE, "Article 12(2)", "shall not exceed 5 per cent"), max_rate="5")
    sd.ppt(t, date(2020, 1, 1), Src(
        "MLI position of the UAE — instrument of deposit (OECD)",
        "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/"
        "beps-mli-position-united-arab-emirates-instrument-deposit.pdf", "MLI art. 7(1)",
        "Lithuania Original 30-06-2013 19-12-2014 (covered by both; Art. 30 existing clause)"))


def _eu_annex_i(sd: Seeder) -> None:
    """Annex I of the EU list (Council conclusions 17 Feb 2026) for jurisdictions in the
    database — it drives list-triggered rates (Latvia, Cyprus) and the compliance score."""
    src = Src(
        "Council conclusions on the EU list of non-cooperative jurisdictions, 17 Feb 2026 "
        "(OJ C/2026/1465)", "http://publications.europa.eu/resource/celex/52026XG01465",
        "Annex I", "American Samoa, Anguilla, Guam, Palau, Panama, Russian Federation, Turks "
        "and Caicos Islands, US Virgin Islands, Vanuatu, Viet Nam")
    for code, name in (("PA", "Panama"), ("VU", "Vanuatu")):
        sd.listing(sd.jurisdiction(code, name), "EU_TAX_ANNEX_I", "non_cooperative",
                   date(2026, 2, 17), None, src)


def _estonia(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, ee: Jurisdiction, eu: JurisdictionGroup
) -> None:
    start = date(2025, 1, 1)
    # Distribution tax 22/78 of the net distribution = 22% of profit when fully distributed;
    # retained profits are untaxed (deferral not modelled).
    sd.cit(ee, start, Src(
        EE_SRC, EE_TUMS, "TuMS § 4 lg 1, 1¹; § 50 lg 1",
        "Tulumaksu määr [...] on 22%. [...] jagatakse maksustatav summa enne maksumääraga "
        "korrutamist arvuga 0,78 (tax on distributed profit only)"), rate="22")
    no_wht = Src(EE_SRC, EE_TUMS, "TuMS § 41, § 29 lg 7",
                 "dividends are taxed at company level under § 50 (no withholding); interest is "
                 "taxed only from real-estate funds (§ 29(7))")
    sd.wht(ee, "DIVIDEND", "0", start, no_wht)
    sd.wht(ee, "INTEREST", "0", start, no_wht)
    sd.wht(ee, "ROYALTY", "10", start, Src(
        EE_SRC, EE_TUMS, "TuMS § 41 p 8; § 43 lg 1 p 2",
        "punktides 8–10 ja punktis 12 nimetatud väljamaksetelt – 10%"))
    sd.exemption(
        ee, "ROYALTY", eu, start,
        Src(EE_SRC, EE_TUMS, "TuMS § 31 lg 4",
            "vähemalt 25% [...] kaheaastase või pikema perioodi jooksul"),
        min_holding_pct="25", min_holding_months=24, legal_ref="TuMS § 31 lg 4",
        description="Interest and Royalties Directive: associated EU/Swiss company (≥25%, "
        "2 years)",
    )
    sd.regime(
        ee, start,
        Src(EE_SRC, EE_TUMS, "TuMS § 50 lg 1¹",
            "vähemalt 10% [...] dividends from an EEA/Swiss company subject to tax, or a "
            "third-country company whose profit was taxed, may be redistributed tax-free"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=10, min_holding_period_months=None, subject_to_tax_condition=True,
        exempt_share_pct=100,
        notes="Dividends received at ≥10% can be redistributed without the 22/78 tax; share "
        "gains bear the tax when distributed. CFC (§ 54³): >50%, non-genuine arrangements "
        "only, no low-tax test — not seeded",
    )

    # MLI: both list the treaty but Estonia has not notified completion (art. 35(7)) — no PPT.
    t = sd.treaty(fr, ee, name="Convention between France and Estonia (1997)",
                  signed=date(1997, 10, 28), in_force=date(2001, 5, 1), src=Src(
                      "Convention France–Estonie (impots.gouv.fr)", FR_EE, None,
                      "signée à Paris le 28 octobre 1997 [...] entrée en vigueur le 1er mai 2001"))
    src = "Convention France–Estonie (impots.gouv.fr)"
    start = date(2001, 5, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_EE, "Article 10(2)(b)", "15 p. cent [...] dans tous les autres cas"),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_EE, "Article 10(2)(a)",
        "5 p. cent [...] si le bénéficiaire effectif est une société qui [...] détient "
        "directement au moins 10 p. cent du capital"), max_rate="5", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, FR_EE, "Article 11(2)", "ne peut excéder 10 p. cent du montant brut des intérêts"),
        max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", date(2015, 12, 11), Src(
        "Convention France–Estonie, version consolidée clause NPF (impots.gouv.fr)", FR_EE,
        "Article 12(1); Protocol para. 10 (MFN)",
        "ne sont imposables que dans cet autre État (MFN clause triggered by the "
        "Estonia–Luxembourg treaty)"), exclusive=True)

    t = sd.treaty(ee, ae, name="Convention between Estonia and the UAE (2011)",
                  signed=date(2011, 4, 20), in_force=date(2012, 3, 29), src=Src(
                      "Convention Estonia–UAE, RT II 06.03.2012, 4 (Riigi Teataja)", EE_AE, None,
                      "entry into force 29.03.2012; effect from 1 January 2011 (Art. 31)"))
    src = "Convention Estonia–UAE, RT II 06.03.2012, 4 (Riigi Teataja)"
    start = date(2011, 1, 1)
    for cat, art in (("DIVIDEND", "Article 10"), ("INTEREST", "Article 11"),
                     ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, EE_AE, f"{art}(1)", "shall be taxable only in that other Contracting State"),
            exclusive=True)
    sd.ppt(t, start, Src(
        src, EE_AE, "Article 23",
        "Benefits [...] shall not be available [...] if the main purpose or one of the main "
        "purposes [...] was to obtain benefits under this Convention"))


def _finland(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, fi: Jurisdiction, eu: JurisdictionGroup
) -> None:
    start = date(2026, 1, 1)
    sd.cit(fi, start, Src(
        "Tuloverolaki 1535/1992 (Finlex, ajantasa 2026-07-09)", FI_TVL, "TVL 124 § 2 mom",
        "Yhteisön tuloveroprosentti on 20. (18% from 2027 proposed in HE 151/2026)"),
        rate="20")
    lvl = Src("Lähdeverolaki 627/1978 (Finlex)", FI_LVL, "LVL 7 § 2 kohta",
              "20 prosenttia rajoitetusti verovelvolliselle yhteisölle maksettavasta osingosta, "
              "korosta ja rojaltista")
    sd.wht(fi, "DIVIDEND", "20", start, lvl)
    sd.wht(fi, "ROYALTY", "20", start, lvl)
    sd.wht(fi, "INTEREST", "0", start, Src(
        "Tuloverolaki 1535/1992 (Finlex)", FI_TVL, "TVL 9 § 2 mom",
        "Rajoitetusti verovelvollinen ei ole verovelvollinen täältä saamastaan korkotulosta, "
        "joka on maksettu [...] ulkomailta Suomeen otetulle lainalle, jota ei ole katsottava "
        "[...] omaan pääomaan rinnastettavaksi (interest on ordinary loans from abroad exempt)"))
    sd.exemption(
        fi, "DIVIDEND", eu, start,
        Src("Lähdeverolaki 627/1978 (Finlex)", FI_LVL, "LVL 3 §",
            "jos yhtiö omistaa välittömästi vähintään kymmenen prosenttia"),
        min_holding_pct="10", min_holding_months=None, legal_ref="LVL 3 §",
        description="Parent-Subsidiary Directive: EU parent holding ≥10% directly",
    )
    sd.exemption(
        fi, "ROYALTY", eu, start,
        Src("Lähdeverolaki 627/1978 (Finlex)", FI_LVL, "LVL 3 b–3 d §",
            "välittömästi vähintään 25 prosenttia (associated EU companies)"),
        min_holding_pct="25", min_holding_months=None, legal_ref="LVL 3 b §",
        description="Interest and Royalties Directive: associated EU company (≥25%)",
    )
    sd.regime(
        fi, start,
        Src("Elinkeinoverolaki 360/1968 (Finlex)", FI_EVL, "EVL 6 a §, 6 b §",
            "Yhteisön veronalaista tuloa on muilta kuin 1 ja 2 momentissa tarkoitetuilta "
            "yhteisöiltä saatu osinko (dividends from non-EEA companies are taxable)"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=True,
        min_subject_to_tax_rate=10, exempt_share_pct=100, payer_group_id=eu.id,
        notes="Dividends from domestic, PSD and EEA companies taxed at ≥10% exempt; non-EEA "
        "dividends taxable; share gains exempt at ≥10% held 1 year (EVL 6 b §)",
    )
    sd.cfc(
        fi, start,
        Src("Laki ulkomaisten väliyhteisöjen osakkaiden verotuksesta 1217/1994 (Finlex)",
            "https://www.finlex.fi/fi/lainsaadanto/1994/1217", "CFC act",
            "vähintään 25 prosenttia [...] alhaisempi kuin 3/5 Suomessa asuvan yhteisön "
            "verotuksen tasosta"),
        control_threshold_pct=25, low_tax_relative_pct=60, threshold_inclusive=True,
        legal_ref="Laki 1217/1994",
        effect="Income of a ≥25%-held entity taxed below 3/5 of the Finnish level is included.",
    )

    # The 1970 convention governs withholding until 31 Dec 2026; the 2023 convention (in force
    # 28 Aug 2026) applies from 1 Jan 2027 and terminates it.
    t = sd.treaty(fr, fi, name="Convention between France and Finland (1970; replaced by the "
                  "2023 convention from 2027)", signed=date(1970, 9, 11),
                  in_force=date(1972, 3, 1), src=Src(
                      "Convention France–Finlande modifiée par la CML (impots.gouv.fr)",
                      FR_FI_OLD, None, "signée le 11 septembre 1970 — entrée en vigueur le 1er "
                      "mars 1972"))
    old = "Convention France–Finlande 1970 modifiée par la CML (impots.gouv.fr)"
    new = "Convention France–Finlande 2023, SopS 34/2026 (Finlex)"
    cut = date(2027, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(1973, 1, 1), Src(
        old, FR_FI_OLD, "Article 10(1)", "ne sont imposables que dans cet autre Etat"),
        exclusive=True, end=cut)
    sd.treaty_rate(t, "INTEREST", "Article 11", date(1973, 1, 1), Src(
        old, FR_FI_OLD, "Article 11(2)", "ne peut excéder 10 p. cent du montant des intérêts"),
        max_rate="10", end=cut)
    sd.treaty_rate(t, "ROYALTY", "Article 12", date(1973, 1, 1), Src(
        old, FR_FI_OLD, "Article 12(1)", "ne sont imposables que dans cet autre Etat"),
        exclusive=True, end=cut)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", cut, Src(
        new, FR_FI_NEW, "Article 10(2)(b)", "15 pour cent du montant brut des dividendes dans "
        "tous les autres cas"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", cut, Src(
        new, FR_FI_NEW, "Article 10(2)(a)",
        "est nul si le bénéficiaire effectif [...] est une société [...] qui détient directement "
        "au moins 5 pour cent du capital [...] tout au long d'une période de 365 jours"),
        exclusive=True, ownership_threshold="5", min_holding_days=365)
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, cut, Src(
            new, FR_FI_NEW, f"{art}(1)", "ne sont imposables que dans cet autre État"),
            exclusive=True)
    sd.ppt(t, date(2020, 1, 1), Src(
        old, FR_FI_OLD, "MLI art. 7(1); new convention art. 27",
        "un avantage [...] ne sera pas accordé [...] l'un des objets principaux — MLI in force "
        "for Finland 1 June 2019"))

    t = sd.treaty(fi, ae, name="Agreement between Finland and the UAE (1996)",
                  signed=date(1996, 3, 12), in_force=date(1997, 12, 26), src=Src(
                      "Finland–UAE tax treaty, SopS 89–90/1997 (Finlex)", FI_AE, None,
                      "entry into force 26.12.1997"))
    src = "Finland–UAE tax treaty, SopS 89–90/1997 (Finlex)"
    for cat, art in (("DIVIDEND", "Article 10"), ("INTEREST", "Article 11"),
                     ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, date(1998, 1, 1), Src(
            src, FI_AE, f"{art}(1)", "shall be taxable only in that other State if such "
            "resident is the beneficial owner"), exclusive=True)
    sd.ppt(t, date(2020, 1, 1), Src(
        "Finnish MLI notice SopS 62/2019 (Finlex)", FI_AE, "MLI art. 7(1)",
        "MLI in force for the UAE 1.9.2019; the treaty is a covered agreement"))


def _moldova(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, md: Jurisdiction) -> None:
    # legis.md / sfs.md blocked (Cloudflare): domestic figures from the official investor guide.
    start = date(2026, 1, 1)
    sd.cit(md, start, Src(
        MD_SRC, MD_GUIDE, "Fiscal Code art. 15",
        "Rate: The standard corporate income tax rate is 12%."), rate="12")
    sd.wht(md, "DIVIDEND", "6", start, Src(
        MD_SRC, MD_GUIDE, "Fiscal Code art. 91",
        "A 6% withholding tax applies to dividends paid to non-resident shareholders"))
    ir = Src(MD_SRC, MD_GUIDE, "Fiscal Code art. 91",
             "A 12% withholding tax applies to interest and royalties paid to non-residents.")
    sd.wht(md, "INTEREST", "12", start, ir)
    sd.wht(md, "ROYALTY", "12", start, ir)
    sd.regime(
        md, start,
        Src("Moldova income determination (PwC Worldwide Tax Summaries — secondary source)",
            "https://taxsummaries.pwc.com/moldova/corporate/income-determination", None,
            "dividends [from foreign companies are] included in taxable income [...] entitled to "
            "a credit for the tax paid in the foreign country"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="Only dividends from Moldovan companies are exempt; foreign dividends and share "
        "gains taxed at 12%. No CFC rules",
    )

    # Moldova is not an MLI signatory; the 2022 convention has its own PPT (art. 27).
    t = sd.treaty(fr, md, name="Convention between France and Moldova (2022)",
                  signed=date(2022, 6, 15), in_force=date(2024, 4, 23), src=Src(
                      "Décret n° 2024-481 du 27 mai 2024 (Légifrance)",
                      "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049607876", None,
                      "(1) Entrée en vigueur : 23 avril 2024."))
    src = "Convention France–Moldavie (impots.gouv.fr)"
    start = date(2025, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_MD, "Article 10(2)(b)", "10 pour cent du montant brut des dividendes dans tous "
        "les autres cas"), max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_MD, "Article 10(2)(a)",
        "directement au moins 10 pour cent du capital [...] tout au long d'une période de 365 "
        "jours"), max_rate="5", ownership_threshold="10", min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, FR_MD, "Article 11(2)", "ne peut excéder 5 pour cent du montant brut des "
        "intérêts"), max_rate="5")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, FR_MD, "Article 12(2)", "ne peut excéder 6 pour cent du montant brut des "
        "redevances"), max_rate="6")
    sd.ppt(t, start, Src(
        src, FR_MD, "Article 27",
        "Refus d'octroi des avantages conventionnels [...] l'un des objets principaux d'un "
        "montage ou d'une transaction"))

    t = sd.treaty(md, ae, name="Agreement between Moldova and the UAE (2017)",
                  signed=date(2017, 7, 10), in_force=date(2018, 7, 26), src=Src(
                      "UAE Ministry of Finance — list of double taxation agreements",
                      "https://mof.gov.ae/wp-content/uploads/2023/08/Avoidance-of-Double-"
                      "Taxation-Agreements1.pdf", None, "87 Moldova 10/7/2017 ... 26/7/2018"))
    src = "Agreement UAE–Moldova (UAE Ministry of Finance)"
    start = date(2017, 1, 1)  # art. 30: from 1 January of the year of signature
    for cat, art, rate in (("DIVIDEND", "Article 10", "5"), ("INTEREST", "Article 11", "6"),
                           ("ROYALTY", "Article 12", "6")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, MD_AE, f"{art}(2)", f"shall not exceed {rate} per cent of the gross amount"),
            max_rate=rate)


def _armenia(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, am: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(am, start, Src(
        AM_SRC, AM_TC, "ՀՕ 125 հոդված 1 մաս",
        "շահութահարկը հաշվարկվում է 18 տոկոս դրույքաչափով (profit tax at 18%)"), rate="18")
    sd.wht(am, "DIVIDEND", "5", start, Src(
        AM_SRC, AM_TC, "ՀՕ 125 հոդված 4 մաս 3.1 կետ",
        "շահաբաժինների մասով՝ հինգ տոկոս (dividends: 5%; 15% on unlisted bank shares from 1 "
        "Feb 2027)"))
    passive = Src(AM_SRC, AM_TC, "ՀՕ 125 հոդված 4 մաս 2 կետ",
                  "պասիվ եկամուտների մասով՝ տասը տոկոս (passive income — incl. interest and "
                  "royalties — 10%)")
    sd.wht(am, "INTEREST", "10", start, passive)
    sd.wht(am, "ROYALTY", "10", start, passive)
    sd.regime(
        am, start,
        Src(AM_SRC, AM_TC, "ՀՕ 123 հոդված 2 մաս 1 կետ",
            "ստացվող շահաբաժինները (dividends received are deducted — scope for foreign "
            "dividends unclear)"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="Deduction of dividends received treated as domestic-only (conservative); share "
        "gains taxed at 18%. No CFC rules",
    )

    t = sd.treaty(fr, am, name="Convention between France and Armenia (1997)",
                  signed=date(1997, 12, 9), in_force=date(2001, 5, 1), src=Src(
                      "Convention France–Arménie modifiée par la CML (impots.gouv.fr)", FR_AM,
                      None, "signée à Paris le 9 décembre 1997 [...] entrée en vigueur le 1er "
                      "mai 2001"))
    src = "Convention France–Arménie modifiée par la CML (impots.gouv.fr)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(2002, 1, 1), Src(
        src, FR_AM, "Article 10(2)(b)", "15 p. cent [...] dans tous les autres cas"),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(2024, 1, 1), Src(
        src, FR_AM, "Article 10(2)(a); MLI art. 8",
        "directement ou indirectement au moins 10 p. cent du capital [...] tout au long d'une "
        "période de 365 jours"), max_rate="5", ownership_threshold="10", min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 11", date(2002, 1, 1), Src(
        src, FR_AM, "Article 11(2)", "ne peut excéder 10 p. cent du montant brut des intérêts "
        "(0% on bank loans)"), max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", date(2002, 1, 1), Src(
        src, FR_AM, "Article 12(2)(b)", "10 p. cent du montant brut des redevances dans les "
        "autres cas (5% for copyright)"), max_rate="10")
    sd.ppt(t, date(2024, 1, 1), Src(
        src, FR_AM, "MLI art. 7(1)",
        "si le fait générateur [...] intervient à compter du 1er janvier 2024"))

    # Entry into force: 19 Dec 2005 per arlis.am; 19 Dec 2004 per both MLI positions; 11 Jan
    # 2005 per the UAE MoF list — the Armenian official record is stored.
    t = sd.treaty(am, ae, name="Agreement between Armenia and the UAE (2002)",
                  signed=date(2002, 4, 20), in_force=date(2005, 12, 19), src=Src(
                      "Համաձայնագիր ՀՀ–ԱՄԷ (arlis.am)", AM_AE, None,
                      "Համաձայնագիրն ուժի մեջ է մտել 2005 թ. դեկտեմբերի 19-ից (MLI positions "
                      "give 19-12-2004)"))
    src = "Համաձայնագիր ՀՀ–ԱՄԷ (arlis.am)"
    start = date(2006, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, AM_AE, "Article 10(1)", "չպետք է գերազանցի [...] 3 (երեք) տոկոսը (shall not "
        "exceed 3%)"), max_rate="3")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, AM_AE, "Article 11(1)", "ենթակա են հարկման միայն այդ մյուս [...] պետությունում "
        "(taxable only in the other State)"), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, AM_AE, "Article 12(2)", "5 percent of the gross amount of the royalties"),
        max_rate="5")
    sd.ppt(t, date(2024, 1, 1), Src(
        "MLI position of Armenia — instrument of deposit (OECD)",
        "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/"
        "beps-mli-position-armenia-instrument-deposit.pdf", "MLI art. 7(1)",
        "United Arab Emirates — covered by both (AM No. 10, UAE No. 7); MLI in force for "
        "Armenia 1 Jan 2024"))


def _azerbaijan(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, az: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(az, start, Src(
        AZ_SRC, AZ_TC, "VM 105.1", "Müəssisələrin mənfəətindən 20 faiz dərəcəsi ilə vergi "
        "tutulur"), rate="20")
    sd.wht(az, "DIVIDEND", "5", date(2024, 1, 1), Src(
        AZ_SRC, AZ_TC, "VM 122.1, 125.1.1",
        "Rezident müəssisə tərəfindən ödənilən dividenddən ödəmə mənbəyində 5 faiz dərəcə ilə "
        "vergi tutulur"))
    sd.wht(az, "INTEREST", "10", start, Src(
        AZ_SRC, AZ_TC, "VM 123.1", "ödəniş mənbəyində 10 faiz dərəcə ilə vergi tutulur"))
    sd.wht(az, "ROYALTY", "14", start, Src(
        AZ_SRC, AZ_TC, "VM 124.1", "royaltidən [...] ödəmə mənbəyində 14 faiz dərəcə ilə vergi "
        "tutulur"))
    sd.regime(
        az, start,
        Src(AZ_SRC, AZ_TC, "VM 122.2, 106.1.19",
            "bir daha vergi tutulmur (domestic dividends taxed at source only) — 50 faizi of "
            "gains on shares held at least 3 years exempt"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="Foreign dividends taxed with a credit; 50% of gains on shares held ≥3 years "
        "exempt (not modelled). CFC rule repealed from 2023 (Law 677-VIQD)",
    )

    t = sd.treaty(fr, az, name="Convention between France and Azerbaijan (2001)",
                  signed=date(2001, 12, 20), in_force=date(2005, 10, 1), src=Src(
                      "Convention France–Azerbaïdjan modifiée par la CML (impots.gouv.fr)", FR_AZ,
                      None, "signée à Paris le 20 décembre 2001 [...] entrée en vigueur le 1er "
                      "octobre 2005"))
    src = "Convention France–Azerbaïdjan modifiée par la CML (impots.gouv.fr)"
    start = date(2006, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_AZ, "Article 10(2)", "l'impôt ainsi établi ne peut excéder 10 % du montant brut "
        "des dividendes"), max_rate="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        src, FR_AZ, "Article 11(2)", "ne peut excéder 10 % du montant brut des intérêts"),
        max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        src, FR_AZ, "Article 12(2)(b)", "10 % du montant brut des redevances dans tous les "
        "autres cas (5% for copyright)"), max_rate="10")
    sd.ppt(t, date(2025, 1, 1), Src(
        src, FR_AZ, "MLI art. 7(1)",
        "si le fait générateur de ces impôts intervient à compter du 1er janvier 2025"))

    # Entry into force: 12 Jun 2007 per the UAE, 25 Jul 2007 per Azerbaijan — effect 2008 either
    # way. Articles 11-13 in this text are dividends, interest and royalties.
    t = sd.treaty(az, ae, name="Agreement between Azerbaijan and the UAE (2006)",
                  signed=date(2006, 11, 20), in_force=date(2007, 7, 25), src=Src(
                      "MLI position of Azerbaijan (OECD)",
                      "https://www.oecd.org/tax/treaties/beps-mli-position-azerbaijan.pdf", None,
                      "United Arab Emirates [...] 25.07.2007 (UAE position: 12-06-2007)"))
    src = "Agreement UAE–Azerbaijan (UAE Ministry of Finance)"
    start = date(2008, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 11", start, Src(
        src, AZ_AE, "Article 11(2)(b)", "10 per cent of the gross amount of the dividends in "
        "all other cases (5% for governmental owners)"), max_rate="10")
    sd.treaty_rate(t, "INTEREST", "Article 12", start, Src(
        src, AZ_AE, "Article 12(2)", "shall not exceed 7 per cent of the gross amount of the "
        "interest"), max_rate="7")
    sd.treaty_rate(t, "ROYALTY", "Article 13", start, Src(
        src, AZ_AE, "Article 13(2)(b)", "10 per cent of the gross amount of the royalties in "
        "all other cases (5% for software, patents and know-how)"), max_rate="10")
    sd.ppt(t, date(2025, 1, 1), Src(
        "MLI positions of Azerbaijan and the UAE (OECD)",
        "https://www.oecd.org/tax/treaties/beps-mli-position-azerbaijan.pdf", "MLI art. 7(1)",
        "covered by both (AZ No. 53, UAE No. 9); MLI in force for Azerbaijan 1 Jan 2025"))


def _serbia(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, rs: Jurisdiction) -> None:
    start = date(2026, 1, 1)
    sd.cit(rs, start, Src(
        RS_SRC, RS_ZPDP, "ЗПДПЛ чл. 39", "Стопа пореза на добит правних лица износи 15%."),
        rate="15")
    wht = Src(RS_SRC, RS_ZPDP, "ЗПДПЛ чл. 40 ст. 1",
              "порез на добит по одбитку по стопи од 20% обрачунава се и плаћа на приходе [...] "
              "по основу: 1) дивиденди [...] 2) [...] ауторска накнада [...] 3) камата (25% on "
              "royalties and interest to preferential-tax jurisdictions, art. 40(4))")
    for cat in ("DIVIDEND", "INTEREST", "ROYALTY"):
        sd.wht(rs, cat, "20", start, wht)
    sd.regime(
        rs, start,
        Src(RS_SRC, RS_ZPDP, "ЗПДПЛ чл. 52-53",
            "10% или више акција [...] непрекидно у периоду од најмање годину дана (indirect "
            "credit, not an exemption)"),
        participation_exemption_dividends=False, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=False,
        exempt_share_pct=0,
        notes="Foreign dividends taxed with an indirect credit at ≥10% held 1 year (not "
        "modelled); share gains taxed at 15%. EU-directive and CFC articles apply only from EU "
        "accession",
    )

    t = sd.treaty(fr, rs, name="Convention between France and Yugoslavia (1974), applied by "
                  "Serbia", signed=date(1974, 3, 28), in_force=date(1975, 8, 1), src=Src(
                      "BOI-INT-CVB-SRB-20120912 (BOFiP)",
                      "https://bofip.impots.gouv.fr/bofip/BOI-INT-CVB-SRB-20120912", None,
                      "continue à produire ses effets [...] aux relations bilatérales entre la "
                      "République française et la République de Serbie"))
    src = "Convention France–Serbie modifiée par la CML (impots.gouv.fr)"
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(1976, 1, 1), Src(
        src, FR_RS, "Article 10(2)(b)", "15 p. cent du montant brut des dividendes dans tous "
        "les autres cas"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", date(2019, 1, 1), Src(
        src, FR_RS, "Article 10(2)(a); MLI art. 8",
        "si le bénéficiaire est une société qui dispose directement d'au moins 25 p. cent du "
        "capital [...] tout au long d'une période de 365 jours incluant le jour du paiement"),
        max_rate="5", ownership_threshold="25", min_holding_days=365)
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, date(1976, 1, 1), Src(
            src, FR_RS, f"{art}(1)", "ne sont imposables que dans cet autre Etat"),
            exclusive=True)
    sd.ppt(t, date(2019, 1, 1), Src(
        src, FR_RS, "MLI art. 7(1)",
        "si le fait générateur [...] intervient à compter du premier jour de l'année civile "
        "qui commence à compter du 1er janvier 2019"))

    t = sd.treaty(rs, ae, name="Agreement between Serbia and the UAE (2013)",
                  signed=date(2013, 1, 13), in_force=date(2013, 7, 2), src=Src(
                      "MLI position of Serbia — instrument of deposit (OECD)",
                      "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/"
                      "beps-mli/beps-mli-position-serbia-instrument-deposit.pdf", None,
                      "United Arab Emirates Original 13-01-2013 02-07-2013"))
    src = "Agreement UAE–Serbia (UAE Ministry of Finance)"
    start = date(2013, 8, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, RS_AE, "Article 10(2)(b)", "10 per cent of the gross amount of the dividends in "
        "all other cases"), max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, RS_AE, "Article 10(2)(a)",
        "if the beneficial owner is a company which holds directly or indirectly at least 5% "
        "of the capital"), max_rate="5", ownership_threshold="5")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, RS_AE, f"{art}(2)", "shall not exceed 10 per cent of the gross amount"),
            max_rate="10")
    sd.ppt(t, date(2020, 1, 1), Src(
        "MLI position of the UAE — instrument of deposit (OECD)",
        "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/"
        "beps-mli-position-united-arab-emirates-instrument-deposit.pdf", "MLI art. 7(1)",
        "Serbia — covered by both (RS No. 61, UAE No. 90); MLI in force for the UAE 1 Sep 2019"))


def _directives(
    sd: Seeder, j: Jurisdiction, eu: JurisdictionGroup, start: date, div: Src, ird: Src, *,
    div_ref: str, ird_ref: str,
) -> None:
    sd.exemption(
        j, "DIVIDEND", eu, start, div, min_holding_pct="10", min_holding_months=24,
        legal_ref=div_ref, description="Parent-Subsidiary Directive: EU parent ≥10% for 24 months",
    )
    for cat in ("INTEREST", "ROYALTY"):
        sd.exemption(
            j, cat, eu, start, ird, min_holding_pct="25", min_holding_months=24,
            legal_ref=ird_ref,
            description="Interest and Royalties Directive: associated EU company (≥25%, "
            "24 months)",
        )


def _croatia(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, hr: Jurisdiction, eu: JurisdictionGroup
) -> None:
    start = date(2024, 1, 1)
    sd.cit(hr, start, Src(
        HR_SRC, HR_ZPD, "ZPD čl. 28",
        "18% ako su u poreznom razdoblju ostvareni prihodi jednaki ili veći od 1.000.000,00 eura "
        "(10% below EUR 1m of revenue)"), rate="18")
    sd.wht(hr, "DIVIDEND", "10", start, Src(
        "Zakon o izmjenama Zakona o porezu na dobit, NN 114/2023", HR_NN114, "ZPD čl. 31 st. 7",
        "porez po odbitku na dividende i udjele u dobiti plaća se po stopi od 10 %."))
    ir = Src("Zakon o izmjenama Zakona o porezu na dobit, NN 114/2023", HR_NN114,
             "ZPD čl. 31 st. 6", "Porez po odbitku plaća se po stopi od 15 %. (interest on "
             "loans from foreign banks and on bonds exempt, st. 5)")
    sd.wht(hr, "INTEREST", "15", start, ir)
    sd.wht(hr, "ROYALTY", "15", start, ir)
    for cat in ("DIVIDEND", "INTEREST", "ROYALTY"):
        sd.consequence(
            hr, "EU_TAX_ANNEX_I", cat, "25", start, Src(
                "Zakon o izmjenama Zakona o porezu na dobit, NN 114/2023", HR_NN114,
                "ZPD čl. 31 st. 12",
                "na EU popisu nekooperativnih jurisdikcija u porezne svrhe, a s kojima Republika "
                "Hrvatska ne primjenjuje ugovor o izbjegavanju dvostrukog oporezivanja — 25 %"),
            legal_ref="ZPD čl. 31 st. 12",
            description=f"25% withholding on {cat.lower()} to an EU-listed jurisdiction without "
            "a Croatian tax treaty",
        )
    _directives(
        sd, hr, eu, start,
        Src(HR_SRC, HR_ZPD, "ZPD čl. 31.e st. 1",
            "ima najmanje 10% udjela u kapitalu [...] u neprekidnom razdoblju od 24 mjeseca"),
        Src(HR_SRC, HR_ZPD, "ZPD čl. 31.a st. 4, 31.b",
            "izravni minimalni udjel od 25 % kapitala [...] neprekidno najmanje 24 mjeseca"),
        div_ref="ZPD čl. 31.e", ird_ref="ZPD čl. 31.a",
    )
    sd.regime(
        hr, start,
        Src(HR_SRC, HR_ZPD, "ZPD čl. 6 st. 1 t. 1",
            "dividende i udjeli u dobiti [...] koji isplatitelju nisu porezno priznati rashod "
            "(payer subject to profit tax; no holding test)"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=True,
        exempt_share_pct=100,
        notes="Dividends from payers subject to profit tax exempt with no holding test; no "
        "capital-gains participation exemption found",
    )
    sd.cfc(
        hr, start,
        Src(HR_SRC, HR_ZPD, "ZPD čl. 30.b",
            "više od 50% [...] manji je od razlike između poreza na dobit koji bi se naplatio "
            "[...] prema Zakonu i stvarnog poreza na dobit"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="ZPD čl. 30.b",
        effect="Passive income of a >50%-controlled entity taxed below half the Croatian tax "
        "is included (substance carve-out).",
    )

    t = sd.treaty(fr, hr, name="Convention between France and Croatia (2003)",
                  signed=date(2003, 6, 19), in_force=date(2005, 9, 1), src=Src(
                      "BOI-INT-CVB-HRV-20120912 (BOFiP)",
                      "https://bofip.impots.gouv.fr/bofip/BOI-INT-CVB-HRV-20120912", None,
                      "entrée en vigueur le 1er septembre 2005 [...] aux sommes imposables à "
                      "compter du 1er janvier 2006"))
    src = "Convention France–Croatie modifiée par la CML (impots.gouv.fr)"
    start = date(2006, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_HR, "Article 10(2)(b)", "15 % du montant brut des dividendes dans tous les "
        "autres cas"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_HR, "Article 10(2)(a)",
        "0 % du montant brut des dividendes si le bénéficiaire effectif est une société qui "
        "détient directement ou indirectement au moins 10 % du capital"), max_rate="0",
        ownership_threshold="10")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, FR_HR, f"{art}(1)", "ne sont imposables que dans cet autre Etat"),
            exclusive=True)
    sd.ppt(t, date(2022, 1, 1), Src(
        src, FR_HR, "MLI art. 7(1)",
        "MLI in force for Croatia 1 June 2021 — withholding taxes from 1 January 2022"))

    t = sd.treaty(hr, ae, name="Agreement between Croatia and the UAE (2017)",
                  signed=date(2017, 7, 13), in_force=date(2018, 9, 28), src=Src(
                      "MVEP treaty register (Croatian Ministry of Foreign Affairs)",
                      "https://mvep.gov.hr/print.aspx?id=21905&country=143&url=print", None,
                      "entry into force 28 September 2018 (NN-MU 7/2018)"))
    src = "Ugovor RH–UAE, NN Međunarodni ugovori 13/2017"
    start = date(2019, 1, 1)
    for cat, art, word in (("DIVIDEND", "Article 11", "dividendi"),
                           ("INTEREST", "Article 12", "kamata"),
                           ("ROYALTY", "Article 13", "naknada za autorska prava")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, HR_AE, f"{art}(2)", f"ne smije biti veći od 5 posto brutoiznosa {word}"),
            max_rate="5")
    sd.ppt(t, date(2022, 1, 1), Src(
        "MLI position of the UAE — instrument of deposit (OECD)",
        "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/"
        "beps-mli-position-united-arab-emirates-instrument-deposit.pdf", "MLI art. 7(1)",
        "Croatia — covered by both (HR No. 63); MLI in force for Croatia 1 June 2021"))


def _slovenia(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, si: Jurisdiction, eu: JurisdictionGroup
) -> None:
    sd.cit(si, date(2024, 1, 1), Src(
        "ZORZFS, Ur.l. RS 131/2023", SI_ZORZFS, "ZORZFS čl. 64 odst. 1",
        "se davek plačuje po stopnji 22 odstotkov od davčne osnove za leta 2024, 2025, 2026, "
        "2027 in 2028."), rate="22", end=date(2029, 1, 1))
    sd.cit(si, date(2029, 1, 1), Src(
        SI_SRC, SI_ZDDPO, "ZDDPO-2 čl. 60", "Davek se plačuje po stopnji 19 % (base rate)"),
        rate="19")
    start = date(2026, 1, 1)
    wht = Src(SI_SRC, SI_ZDDPO, "ZDDPO-2 čl. 70",
              "po stopnji 15% (dividends, interest and royalties paid to non-residents)")
    for cat in ("DIVIDEND", "INTEREST", "ROYALTY"):
        sd.wht(si, cat, "15", start, wht)
    _directives(
        sd, si, eu, start,
        Src(SI_SRC, SI_ZDDPO, "ZDDPO-2 čl. 71", "at least 10% held at least 24 months"),
        Src(SI_SRC, SI_ZDDPO, "ZDDPO-2 čl. 72", "direct holding of at least 25% held at least "
            "24 months"),
        div_ref="ZDDPO-2 čl. 71", ird_ref="ZDDPO-2 čl. 72",
    )
    sd.regime(
        si, start,
        Src("Slovenia income determination (PwC Worldwide Tax Summaries — secondary source)",
            "https://taxsummaries.pwc.com/slovenia/corporate/income-determination",
            "ZDDPO-2 čl. 24",
            "dividends [...] generally 95% exempt [...] the distributor is subject to Slovenian "
            "CIT or a comparable tax"),
        participation_exemption_dividends=True, participation_exemption_capgains=False,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=True,
        exempt_share_pct=95,
        notes="95% of dividends exempt (payer subject to comparable tax); gains on ≥8% holdings "
        "held 6 months 47.5% effectively exempt (not modelled)",
    )
    sd.cfc(
        si, start,
        Src("FURS ruling 0920-6175/2023-3",
            "https://www.fu.gov.si/davki_in_druge_dajatve/podrocja/davek_od_dohodkov_pravnih_"
            "oseb_ddpo/", "ZDDPO-2 čl. 67.h",
            "več kot 50 % [...] nižji od polovice davka od dohodkov pravnih oseb, ki bi se za ta "
            "dobiček zaračunal osebi po tem zakonu"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="ZDDPO-2 čl. 67.h",
        effect="Income of a >50%-controlled entity taxed below half the Slovenian tax is "
        "included.",
    )

    t = sd.treaty(fr, si, name="Convention between France and Slovenia (2004)",
                  signed=date(2004, 4, 7), in_force=date(2007, 3, 1), src=Src(
                      "Convention France–Slovénie (impots.gouv.fr)", FR_SI, None,
                      "signée à Ljubljana le 7 avril 2004 — entrée en vigueur le 1er mars 2007"))
    src = "Convention France–Slovénie (impots.gouv.fr)"
    start = date(2008, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        src, FR_SI, "Article 10(2)(a)", "15 % du montant brut des dividendes"), max_rate="15")
    for cat, art, cap in (("DIVIDEND", "Article 10", None), ("INTEREST", "Article 11", "5"),
                          ("ROYALTY", "Article 12", "5")):
        if cap:
            sd.treaty_rate(t, cat, art, start, Src(
                src, FR_SI, f"{art}(2)", f"ne peut excéder {cap} % du montant brut"),
                max_rate=cap)
        sd.treaty_rate(t, cat, art, start, Src(
            src, FR_SI, f"{art} (20% affiliation)",
            "ne sont imposables que dans cet autre Etat [...] société qui détient directement "
            "au moins 20 % du capital"), exclusive=True, ownership_threshold="20")
    sd.ppt(t, date(2019, 1, 1), Src(
        "BOI-ANNX-000511-20260429 (BOFiP)",
        "https://bofip.impots.gouv.fr/bofip/BOI-ANNX-000511-20260429", "MLI art. 7(1)",
        "Slovénie — retenues à la source à compter du 1er janvier 2019"))

    t = sd.treaty(si, ae, name="Agreement between Slovenia and the UAE (2013)",
                  signed=date(2013, 10, 12), in_force=date(2014, 8, 27), src=Src(
                      "MLI position of Slovenia (OECD)",
                      "https://www.oecd.org/tax/treaties/beps-mli-position-slovenia.pdf", None,
                      "United Arab Emirates [...] 27-08-2014"))
    src = "Sporazum SI–UAE, Ur.l. RS – MP 37/2014"
    start = date(2015, 1, 1)
    for cat, art in (("DIVIDEND", "Article 10"), ("INTEREST", "Article 11"),
                     ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            src, SI_AE, f"{art}(2)", "shall not exceed 5 per cent of the gross amount"),
            max_rate="5")
    sd.ppt(t, date(2020, 1, 1), Src(
        "MLI position of the UAE — instrument of deposit (OECD)",
        "https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/"
        "beps-mli-position-united-arab-emirates-instrument-deposit.pdf", "MLI art. 7(1)",
        "Slovenia — covered by both (SI No. 54); MLI in force for the UAE 1 Sep 2019"))
