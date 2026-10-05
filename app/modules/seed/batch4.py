"""P8 batch 4: Hong Kong, Italy, Portugal, Austria.

Figures were sourced on 2026-10-05 from the official texts cited on each `Src` and are stored
as `unreviewed` until a named reviewer confirms them (spec §10). Research notes:
docs/superpowers/plans/2026-10-05-p8-batch4.md.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.modules.core.models import Jurisdiction
from app.modules.core.reference import JurisdictionGroup
from app.modules.seed.builder import Seeder, Src

IRD = "https://www.ird.gov.hk/eng/"
FR_HK = IRD + "pdf/Synthesised_Text_HKSAR_France.pdf"
HK_AE = IRD + "pdf/Synthesised_Text_HKSAR_UAE.pdf"
PWC_HK = "https://taxsummaries.pwc.com/hong-kong-sar/corporate/withholding-taxes"
RIS = "https://www.ris.bka.gv.at/"
AT_KSTG = RIS + "NormDokument.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10004569&Paragraf={}"
AT_ESTG = RIS + "NormDokument.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10004570&Paragraf={}"
FR_AT = (
    RIS + "Dokumente/Bundesnormen/NOR40213378/III_93_2018_DBA_Frankreich_synthesised_deutsch.pdf"
)
AT_AE = RIS + "Dokumente/BgblAuth/BGBLA_2022_III_211/BGBLA_2022_III_211.pdf"
EU_URL = "https://european-union.europa.eu/principles-countries-history/eu-countries/{}_en"
NORM = "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:"
IT_TUIR = NORM + "decreto.del.presidente.della.repubblica:1986-12-22;917~art{}!vig=2026-10-05"
IT_DPR600 = NORM + "decreto.del.presidente.della.repubblica:1973-09-29;600~art{}!vig=2026-10-05"
IT_IRAP = NORM + "decreto.legislativo:1997-12-15;446~art16!vig=2014-01-01"
IT_DL66 = NORM + "decreto.legge:2014-04-24;66~art3!vig=2026-10-05"
FR_IT = (
    "https://www.impots.gouv.fr/portail/files/media/10_conventions/italie/"
    "italie_convention-avec-l-italie-impot-sur-le-revenu-impot-sur-la-fortune_fd_1736.pdf"
)
IT_AE = "https://www.normattiva.it/eli/id/1997/09/18/097G0336/ORIGINAL"
PT_CIRC = (
    "https://info.portaldasfinancas.gov.pt/pt/informacao_fiscal/codigos_tributarios/CIRC_2R/"
    "Pages/irc{}.aspx"
)
FR_PT = (
    "https://www.impots.gouv.fr/sites/default/files/media/10_conventions/portugal/"
    "portugal_20190805.pdf"
)
PT_AE = (
    "https://info.portaldasfinancas.gov.pt/pt/informacao_fiscal/convencoes_evitar_dupla_"
    "tributacao/convencoes_tabelas_doclib/Documents/CDT%20EAU.pdf"
)


def seed_batch4(session: Session) -> None:
    sd = Seeder(session)
    fr = sd.jurisdiction("FR", "France")
    ae = sd.jurisdiction("AE", "United Arab Emirates")
    _hong_kong(sd, fr, ae, sd.jurisdiction("HK", "Hong Kong SAR"))
    eu = sd.group("EU", "European Union member states")
    at = sd.jurisdiction("AT", "Austria")
    sd.member(eu, at, date(1995, 1, 1), Src(
        "Austria — EU member country profile (european-union.europa.eu)",
        EU_URL.format("austria"), None, "EU Member State: since 1 January 1995"))
    _austria(sd, fr, ae, at, eu)
    pt = sd.jurisdiction("PT", "Portugal")
    sd.member(eu, pt, date(1986, 1, 1), Src(
        "Portugal — EU member country profile (european-union.europa.eu)",
        EU_URL.format("portugal"), None, "EU Member State: since 1 January 1986"))
    _portugal(sd, fr, ae, pt, eu)
    it = sd.jurisdiction("IT", "Italy")
    sd.member(eu, it, date(1958, 1, 1), Src(
        "Italy — EU member country profile (european-union.europa.eu)",
        EU_URL.format("italy"), None, "since 1 January 1958"))
    _italy(sd, fr, ae, it, eu)


def _hong_kong(sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, hk: Jurisdiction) -> None:
    sd.cit(hk, date(2018, 4, 1), Src(
        "Profits Tax (Inland Revenue Department)", IRD + "tax/bus_pft.htm",
        "IRO Cap. 112 s.14, Sch. 8B",
        "8.25% on assessable profits up to $2,000,000; and 16.5% on any part of assessable "
        "profits over $2,000,000"),
        brackets=[("0", "2000000", "8.25"), ("2000000", None, "16.5")])
    no_wht = Src(
        "Hong Kong SAR withholding taxes (PwC Worldwide Tax Summaries — secondary source)",
        PWC_HK, None, "There is no withholding tax (WHT) on dividends and interest.")
    sd.wht(hk, "DIVIDEND", "0", date(2018, 4, 1), no_wht)
    sd.wht(hk, "INTEREST", "0", date(2018, 4, 1), no_wht)
    sd.wht(hk, "ROYALTY", "4.95", date(2018, 4, 1), Src(
        "Departmental Interpretation and Practice Notes No. 22 (IRD)", IRD + "pdf/dipn22.pdf",
        "IRO s.21A",
        "Under section 21A, the assessable profits in respect of a sum specified in section "
        "15(1)(a), (b) or (ba) are deemed to be 30% of the sum received or accrued (30% × 16.5% "
        "= 4.95%; 100% for associates where the IP was owned by a Hong Kong business)"))
    sd.regime(
        hk, date(2023, 1, 1),
        Src("Foreign-sourced income exemption (IRD)", IRD + "tax/bus_fsie.htm",
            "IRO s.15L",
            "continuously held not less than 5% of equity interests in the investee entity "
            "concerned for a period of not less than 12 months [...] the tax rate applicable to "
            "the sum (applicable rate) is at least 15%."),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=5, min_holding_period_months=12, subject_to_tax_condition=True,
        min_subject_to_tax_rate=15, exempt_share_pct=100,
        notes="FSIE: foreign dividends/gains received in HK by an MNE entity exempt with "
        "economic substance or the participation requirement (≥5%, 12 months, ≥15% foreign "
        "rate); foreign interest/IP income taxed unless substance/nexus — not modelled",
    )

    t = sd.treaty(fr, hk, name="Agreement between France and Hong Kong SAR (2010)",
                  signed=date(2010, 10, 21), in_force=date(2011, 12, 1), src=Src(
                      "Comprehensive double taxation agreements (IRD)", IRD + "tax/dta_inc.htm",
                      None, "France: signed 21.10.2010; entry into force 01.12.2011"))
    start = date(2012, 1, 1)
    for cat, art, word in (("DIVIDEND", "Article 10", "dividends"),
                           ("INTEREST", "Article 11", "interest"),
                           ("ROYALTY", "Article 12", "royalties")):
        sd.treaty_rate(t, cat, art, start, Src(
            "HKSAR–France agreement, synthesised text with the MLI (IRD)", FR_HK, f"{art}(2)",
            f"the tax so charged shall not exceed 10 per cent of the gross amount of the "
            f"{word}."), max_rate="10")
    sd.ppt(t, date(2024, 1, 1), Src(
        "HKSAR–France agreement, synthesised text with the MLI (IRD)", FR_HK, "MLI art. 7(1)",
        "a benefit under the Agreement shall not be granted [...] if it is reasonable to "
        "conclude [...] that obtaining that benefit was one of the principal purposes"))

    t = sd.treaty(hk, ae, name="Agreement between Hong Kong SAR and the UAE (2014)",
                  signed=date(2014, 12, 11), in_force=date(2015, 12, 10), src=Src(
                      "Comprehensive double taxation agreements (IRD)", IRD + "tax/dta_inc.htm",
                      None, "United Arab Emirates: signed 11.12.2014; entry into force "
                      "10.12.2015"))
    start = date(2016, 4, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "HKSAR–UAE agreement, synthesised text with the MLI (IRD)", HK_AE, "Article 10(2)(b)",
        "(b) five per cent of the gross amount of the dividends in all other cases."),
        max_rate="5")
    for cat, art, word in (("INTEREST", "Article 11", "interest"),
                           ("ROYALTY", "Article 12", "royalties")):
        sd.treaty_rate(t, cat, art, start, Src(
            "HKSAR–UAE agreement, synthesised text with the MLI (IRD)", HK_AE, f"{art}(2)",
            f"shall not exceed five per cent of the gross amount of the {word}"), max_rate="5")
    sd.ppt(t, date(2023, 4, 1), Src(
        "HKSAR–UAE agreement, synthesised text with the MLI (IRD)", HK_AE, "MLI art. 7(1)",
        "a benefit under this Agreement shall not be granted in respect of an item of income "
        "if [...] one of the principal purposes"))


def _austria(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, at: Jurisdiction, eu: JurisdictionGroup
) -> None:
    sd.cit(at, date(2024, 1, 1), Src(
        "§22 KStG 1988 (RIS)", AT_KSTG.format(22), "§22(1) KStG",
        "Die Körperschaftsteuer vom Einkommen [...] beträgt für das Kalenderjahr 2023 24% und "
        "für die Kalenderjahre ab 2024 23%."), rate="23", end=date(2028, 1, 1))
    sd.cit(at, date(2028, 1, 1), Src(
        "§22 KStG 1988 as amended by BGBl. I 62/2026 (RIS)",
        AT_KSTG.format(22) + "&FassungVom=2028-01-02", "§22(1) KStG; §26c Z 102 KStG",
        "Die Körperschaftsteuer vom Einkommen (§ 7 Abs. 2) beträgt 23%. Für Einkommensteile "
        "über 1 000 000 Euro erhöht sich der Steuersatz auf 24%."),
        brackets=[("0", "1000000", "23"), ("1000000", None, "24")])
    sd.wht(at, "DIVIDEND", "27.5", date(2024, 7, 20), Src(
        "§27a EStG 1988 (RIS)", AT_ESTG.format("27a"), "§27a(1) Z 2, §93 EStG",
        "Einkünfte aus Kapitalvermögen unterliegen [...] 2. in allen anderen Fällen einem "
        "besonderen Steuersatz von 27,5%"))
    sd.wht(at, "INTEREST", "0", date(2024, 7, 20), Src(
        "§98 EStG 1988 (RIS)", AT_ESTG.format(98), "§98(1) Z 5 lit. b EStG",
        "Von der beschränkten Steuerpflicht ausgenommen sind – (Stück)Zinsen, die nicht von "
        "natürlichen Personen erzielt werden"))
    sd.wht(at, "ROYALTY", "20", date(2024, 7, 20), Src(
        "§99 / §100 EStG 1988 (RIS)", AT_ESTG.format(100), "§99(1) Z 3, §100(1) EStG",
        "Die Abzugsteuer gemäß § 99 beträgt 20%, bei Einkünften gemäß § 99 Abs. 1 Z 6 und 7 "
        "jedoch 27,5%."))
    sd.exemption(
        at, "DIVIDEND", eu, date(2025, 12, 24),
        Src("§94 EStG 1988 (RIS)", AT_ESTG.format(94), "§94 Z 2 EStG",
            "die Körperschaft ist mindestens zu einem Zehntel [...] beteiligt. Dies gilt auch "
            "für ausländische Körperschaften, die [...] Richtlinie 2011/96/EU [...] erfüllen, "
            "wenn die Beteiligung während eines ununterbrochenen Zeitraumes von mindestens "
            "einem Jahr bestanden hat."),
        min_holding_pct="10", min_holding_months=12, legal_ref="§94 Z 2 EStG",
        description="Parent-Subsidiary Directive: EU parent holding ≥10% for 1 year",
    )
    ird = Src(
        "§99a EStG 1988 (RIS)", AT_ESTG.format("99a"), "§99a EStG",
        "unmittelbar mindestens zu einem Viertel in Form von Gesellschaftsrechten [...] Diese "
        "Beteiligungserfordernisse müssen zum Zeitpunkt der Zahlung [...] für einen "
        "ununterbrochenen Zeitraum von mindestens einem Jahr bestanden haben.")
    sd.exemption(
        at, "ROYALTY", eu, date(2010, 1, 14), ird, min_holding_pct="25", min_holding_months=12,
        legal_ref="§99a EStG",
        description="Interest and Royalties Directive: associated EU company (≥25%, 1 year)",
    )
    sd.regime(
        at, date(2020, 1, 1),
        Src("§10 KStG 1988 (RIS)", AT_KSTG.format(10), "§10(1) Z 7, §10(2) KStG",
            "nachweislich in Form von Kapitalanteilen während eines ununterbrochenen Zeitraumes "
            "von mindestens einem Jahr mindestens zu einem Zehntel [...] beteiligt sind."),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=10, min_holding_period_months=12, subject_to_tax_condition=False,
        exempt_share_pct=100,
        notes="Internationale Schachtelbeteiligung: ≥10% for 1 year, 100% exempt, gains "
        "tax-neutral; switch-over to credit for passive subsidiaries taxed <15% (§10a, from "
        "2026) — not modelled. CFC (§10a) uses an absolute 15% test — not seeded",
    )

    t = sd.treaty(fr, at, name="Convention between France and Austria (1993)",
                  signed=date(1993, 3, 26), in_force=date(1994, 9, 1), src=Src(
                      "DBA Frankreich, BGBl. 613/1994 (RIS)",
                      RIS + "Dokumente/Bundesnormen/NOR11004959/NOR11004959.html", None,
                      "das Abkommen tritt [...] mit 1. September 1994 in Kraft."))
    start = date(1995, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "DBA Frankreich, synthetisierter Text mit dem MLI (RIS)", FR_AT, "Article 10(2)(a)",
        "15 vom Hundert des Bruttobetrags der Dividenden nicht übersteigen"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "DBA Frankreich, synthetisierter Text mit dem MLI (RIS)", FR_AT, "Article 10(2)(b)",
        "wenn der Nutzungsberechtigte eine der Körperschaftsbesteuerung unterworfene "
        "Gesellschaft ist, die unmittelbar oder mittelbar über mindestens 10 vom Hundert des "
        "Kapitals [...] verfügt, dürfen diese Dividenden nur in dem Vertragsstaat besteuert "
        "werden, in dem der Nutzungsberechtigte ansässig ist."),
        exclusive=True, ownership_threshold="10")
    for cat, art, word in (("INTEREST", "Article 11", "Zinsen"),
                           ("ROYALTY", "Article 12", "Lizenzgebühren")):
        sd.treaty_rate(t, cat, art, start, Src(
            "DBA Frankreich, synthetisierter Text mit dem MLI (RIS)", FR_AT, f"{art}(1)",
            f"{word} [...] dürfen nur im anderen Staat besteuert werden, wenn diese ansässige "
            "Person nutzungsberechtigter Empfänger ist."), exclusive=True)
    sd.ppt(t, date(2019, 1, 1), Src(
        "DBA Frankreich, synthetisierter Text mit dem MLI (RIS)", FR_AT, "MLI art. 7(1)",
        "ARTIKEL 7 DES MLI – VERHINDERUNG VON ABKOMMENSMISSBRAUCH (Principal Purposes Test) "
        "[...] wenn [...] der Erhalt dieser Vergünstigung einer der Hauptzwecke einer "
        "Gestaltung oder Transaktion war"))

    t = sd.treaty(at, ae, name="Convention between Austria and the UAE (2003, protocol 2021)",
                  signed=date(2003, 9, 22), in_force=date(2004, 9, 1), src=Src(
                      "DBA VAE, BGBl. III 88/2004 (RIS)",
                      RIS + "Dokumente/Bundesnormen/NOR40250562/NOR40250562.html", None,
                      "das Abkommen tritt gemäß seinem Art. 29 Abs. 2 am 1. September 2004 in "
                      "Kraft."))
    start = date(2023, 1, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Abänderungsprotokoll DBA VAE, BGBl. III 211/2022 (RIS)", AT_AE, "Article 10(1)",
        "10 vom Hundert des Bruttobetrags der Dividenden nicht übersteigen"), max_rate="10")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Abänderungsprotokoll DBA VAE, BGBl. III 211/2022 (RIS)", AT_AE, "Article 10(1)",
        "nur im anderen Vertragsstaat besteuert werden, wenn der Nutzungsberechtigte [...] "
        "(ii) eine Gesellschaft (jedoch keine Personengesellschaft) ist, die unmittelbar über "
        "mindestens 10 vom Hundert des Kapitals [...] verfügt."),
        exclusive=True, ownership_threshold="10")
    for cat, art in (("INTEREST", "Article 11"), ("ROYALTY", "Article 12")):
        sd.treaty_rate(t, cat, art, start, Src(
            "DBA VAE (RIS)", RIS + "GeltendeFassung.wxe?Abfrage=Bundesnormen&"
            "Gesetzesnummer=20003488", f"{art}(1)",
            "dürfen, wenn diese Person der Nutzungsberechtigte ist, nur im anderen Staat "
            "besteuert werden."), exclusive=True)
    sd.ppt(t, date(2023, 3, 1), Src(
        "Abänderungsprotokoll DBA VAE, BGBl. III 211/2022 (RIS)", AT_AE, "Article 28A",
        "Artikel 28A ANSPRUCH AUF VERGÜNSTIGUNGEN [...] einer der Hauptzwecke einer Gestaltung "
        "oder Transaktion war"))


def _portugal(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, pt: Jurisdiction, eu: JurisdictionGroup
) -> None:
    # Lisbon 2026: IRC 19% + derrama municipal 1.5% (rate on 2025 profit) + derrama estadual
    # 3% / 5% / 9% above €1.5m / €7.5m / €35m — combined marginal bands.
    sd.cit(pt, date(2026, 1, 1), Src(
        "CIRC art. 87 / 87-A (Portal das Finanças); Ofício Circulado 20288/2026",
        PT_CIRC.format("87"), "CIRC art. 87(1), 87-A; Lei 64/2025 art. 3(2)",
        "Nos períodos de tributação que se iniciem durante o ano de 2026, a taxa prevista nos "
        "n.os 1 e 5 do artigo 87.º do Código do IRC é de 19 % [...] De mais de 1500 000 até "
        "7 500 000 [...] 3 / De mais de 7 500 000 até 35 000 000 [...] 5 / Superior a "
        "35 000 000 [...] 9 — LISBOA [...] Taxa geral 1,50%"),
        brackets=[("0", "1500000", "20.5"), ("1500000", "7500000", "23.5"),
                  ("7500000", "35000000", "25.5"), ("35000000", None, "29.5")],
        end=date(2027, 1, 1))
    wht = Src(
        "CIRC art. 87(4) / 94 (Portal das Finanças)", PT_CIRC.format("87"), "CIRC art. 87(4)",
        "Tratando-se de rendimentos de entidades que não tenham sede nem direcção efectiva em "
        "território português e aí não possuam estabelecimento estável [...] a taxa do IRC é "
        "de 25%")
    for cat in ("DIVIDEND", "INTEREST", "ROYALTY"):
        sd.wht(pt, cat, "25", date(2026, 1, 1), wht)
    sd.exemption(
        pt, "DIVIDEND", eu, date(2026, 1, 1),
        Src("CIRC art. 14 (Portal das Finanças)", PT_CIRC.format("14"), "CIRC art. 14(3)",
            "c) Detenha [...] uma participação não inferior a 10 % do capital social ou dos "
            "direitos de voto [...] d) Detenha a participação [...] de modo ininterrupto, "
            "durante o ano anterior à colocação à disposição"),
        min_holding_pct="10", min_holding_months=12, legal_ref="CIRC art. 14(3)",
        description="Parent-Subsidiary Directive: EU/EEA parent ≥10% for 1 year (treaty-state "
        "parents taxed ≥60% of the IRC rate also qualify — not modelled)",
    )
    ird = Src(
        "CIRC art. 14 (Portal das Finanças)", PT_CIRC.format("14"), "CIRC art. 14(12)-(13)",
        "Detém uma participação direta de, pelo menos, 25 % no capital [...] a participação "
        "seja detida de modo ininterrupto durante um período mínimo de dois anos")
    for cat in ("INTEREST", "ROYALTY"):
        sd.exemption(
            pt, cat, eu, date(2026, 1, 1), ird, min_holding_pct="25", min_holding_months=24,
            legal_ref="CIRC art. 14(12)",
            description="Interest and Royalties Directive: associated EU company (≥25%, 2 years)",
        )
    sd.regime(
        pt, date(2026, 1, 1),
        Src("CIRC art. 51 (Portal das Finanças)", PT_CIRC.format("51"), "CIRC art. 51, 51-C",
            "d) [...] a taxa legal aplicável à entidade não seja inferior a 60 % da taxa do IRC "
            "prevista no n.º 1 do artigo 87.º; e) [...] não tenha residência [...] em país [...] "
            "sujeito a um regime fiscal claramente mais favorável"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=10, min_holding_period_months=12, subject_to_tax_condition=True,
        min_subject_to_tax_rate=11.4, exempt_share_pct=100,
        notes="CIRC art. 51: ≥10% for 1 year, subsidiary's statutory rate ≥60% of 19% (11.4% "
        "in 2026), not blacklisted",
    )
    sd.cfc(
        pt, date(2019, 1, 1),
        Src("CIRC art. 66 (Portal das Finanças)", PT_CIRC.format("66"), "CIRC art. 66",
            "pelo menos 25% das partes de capital, dos direitos de voto [...] O imposto sobre "
            "os lucros efetivamente pago seja inferior a 50 % do imposto que seria devido nos "
            "termos deste Código."),
        control_threshold_pct=25, low_tax_relative_pct=50, legal_ref="CIRC art. 66",
        effect="Profits of an entity ≥25% held and taxed below half the Portuguese tax are "
        "attributed (passive income ≤25% carve-out).",
    )

    t = sd.treaty(fr, pt, name="Convention between France and Portugal (1971)",
                  signed=date(1971, 1, 14), in_force=date(1972, 11, 18), src=Src(
                      "Convention France–Portugal (impots.gouv.fr)", FR_PT, None,
                      "signée à Paris le 14 janvier 1971 [...] entrée en vigueur le 18 novembre "
                      "1972 [...] modifiée par l'Avenant signé le 25 août 2016 à Lisbonne [...] "
                      "entré en vigueur le 1er décembre 2017"))
    start = date(2017, 12, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 11", start, Src(
        "Convention France–Portugal (impots.gouv.fr)", FR_PT, "Article 11(2)",
        "l'impôt ainsi établi ne peut excéder 15 p. cent du montant brut des dividendes."),
        max_rate="15")
    sd.treaty_rate(t, "INTEREST", "Article 12", start, Src(
        "Convention France–Portugal (impots.gouv.fr)", FR_PT, "Article 12(2)",
        "l'impôt ainsi établi ne peut excéder 12 p. cent du montant des intérêts"),
        max_rate="12")
    sd.treaty_rate(t, "ROYALTY", "Article 13", start, Src(
        "Convention France–Portugal (impots.gouv.fr)", FR_PT, "Article 13(2)",
        "l'impôt ainsi établi ne peut excéder 5 p. cent du montant brut des redevances."),
        max_rate="5")
    sd.ppt(t, date(2021, 1, 1), Src(
        "Convention France–Portugal modifiée par la CML (impots.gouv.fr)",
        "https://www.impots.gouv.fr/version-consolidee-de-la-convention-avec-le-portugal-impot-"
        "sur-le-revenu-modifiee-par-la-convention", "MLI art. 7(1)",
        "un avantage au titre de celle-ci ne sera pas accordé [...] s'il est raisonnable de "
        "conclure [...] que l'octroi de cet avantage était l'un des objets principaux d'un "
        "montage ou d'une transaction"))

    t = sd.treaty(pt, ae, name="Convention between Portugal and the UAE (2011)",
                  signed=date(2011, 1, 17), in_force=date(2012, 5, 22), src=Src(
                      "Tabela CDT (Autoridade Tributária)",
                      "https://info.portaldasfinancas.gov.pt/pt/informacao_fiscal/convencoes_"
                      "evitar_dupla_tributacao/convencoes_tabelas_doclib/Documents/"
                      "Tabela_CDT_2023.pdf", None,
                      "Aviso n.º 59/2012 publicado em 11-06-2012 EM VIGOR DESDE 22-05-2012"))
    start = date(2012, 5, 22)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convenção Portugal–EAU (Portal das Finanças)", PT_AE, "Article 10(2)(b)",
        "b) 15 % do montante bruto dos dividendos, nos restantes casos."), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convenção Portugal–EAU (Portal das Finanças)", PT_AE, "Article 10(2)(a)",
        "a) 5 % do montante bruto dos dividendos, se o beneficiário efectivo for uma sociedade "
        "[...] que detenha, directamente, pelo menos 10 % do capital"),
        max_rate="5", ownership_threshold="10")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Convenção Portugal–EAU (Portal das Finanças)", PT_AE, "Article 11(2)",
        "o imposto assim estabelecido não excederá 10 % do montante bruto dos juros."),
        max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Convenção Portugal–EAU (Portal das Finanças)", PT_AE, "Article 12(2)",
        "o imposto assim estabelecido não excederá 5 % do montante bruto das royalties."),
        max_rate="5")


def _italy(
    sd: Seeder, fr: Jurisdiction, ae: Jurisdiction, it: Jurisdiction, eu: JurisdictionGroup
) -> None:
    # The TUIR is replaced by a new consolidated code from 2027 (D.Lgs. 117/2026): rates are
    # seeded to the end of 2026 only.
    ires = Src(
        "TUIR art. 77 (Normattiva, vigente 2026-10-05)", IT_TUIR.format(77), "TUIR art. 77",
        "L'imposta è commisurata al reddito complessivo netto con l'aliquota del 24 per cento.")
    sd.cit(it, date(2017, 1, 1), ires, rate="24", end=date(2027, 1, 1))
    irap = Src(
        "D.Lgs. 446/1997 art. 16 (IRAP, Normattiva)", IT_IRAP, "D.Lgs. 446/1997 art. 5, 6(9), 16",
        "applicando al valore della produzione netta l'aliquota del 3,9 per cento (IRES 24% + "
        "IRAP 3.9% on royalties and net interest of a non-financial holding = 27.9%)")
    for cat in ("ROYALTY", "INTEREST"):
        sd.cit(it, date(2017, 1, 1), irap, rate="27.9", end=date(2027, 1, 1), category=cat)
    dl66 = Src(
        "D.L. 66/2014 art. 3 (Normattiva)", IT_DL66, "D.L. 66/2014 art. 3(1); DPR 600 art. 27",
        "Le ritenute e le imposte sostitutive sugli interessi, premi e ogni altro provento di "
        "cui all'articolo 44 [...] sono stabilite nella misura del 26 per cento.")
    sd.wht(it, "DIVIDEND", "26", date(2014, 7, 1), dl66)
    sd.wht(it, "INTEREST", "26", date(2014, 7, 1), dl66)
    sd.wht(it, "ROYALTY", "30", date(2014, 7, 1), Src(
        "DPR 600/1973 art. 25 (Normattiva)", IT_DPR600.format(25), "DPR 600 art. 25(4)",
        "corrisposti a non residenti sono soggetti ad una ritenuta del trenta per cento a "
        "titolo di imposta sulla parte imponibile del loro ammontare (22.5% where the 25% flat "
        "deduction applies — not modelled)"))
    sd.exemption(
        it, "DIVIDEND", eu, date(2026, 1, 1),
        Src("DPR 600/1973 art. 27(3-ter) (Normattiva)", IT_DPR600.format(27),
            "DPR 600 art. 27(3-ter)",
            "La ritenuta è operata a titolo di imposta e con l'aliquota dell'1,20 per cento "
            "sugli utili corrisposti alle società e agli enti soggetti ad un'imposta sul reddito "
            "delle società negli Stati membri dell'Unione europea"),
        min_holding_pct=None, min_holding_months=None, legal_ref="DPR 600 art. 27(3-ter)",
        description="dividends to EU companies taxed at 1.2%", reduced_rate="1.2",
    )
    sd.exemption(
        it, "DIVIDEND", eu, date(2009, 1, 1),
        Src("DPR 600/1973 art. 27-bis (Normattiva)", IT_DPR600.format("27bis"),
            "DPR 600 art. 27-bis",
            "La percentuale indicata nei commi 1 e 1-bis dell'articolo 27-bis [...] è ridotta "
            "[...] al 10 per cento per quelli distribuiti a decorrere dal 1° gennaio 2009. [...] "
            "d) la partecipazione sia detenuta ininterrottamente per almeno un anno"),
        min_holding_pct="10", min_holding_months=12, legal_ref="DPR 600 art. 27-bis",
        description="Parent-Subsidiary Directive: EU parent ≥10% for 1 year",
    )
    ird = Src(
        "DPR 600/1973 art. 26-quater (Normattiva)", IT_DPR600.format("26quater"),
        "DPR 600 art. 26-quater",
        "detiene direttamente una percentuale non inferiore al 25 per cento dei diritti di voto "
        "[...] (e) le partecipazioni [...] sono detenute ininterrottamente per almeno un anno.")
    for cat in ("INTEREST", "ROYALTY"):
        sd.exemption(
            it, cat, eu, date(2014, 7, 1), ird, min_holding_pct="25", min_holding_months=12,
            legal_ref="DPR 600 art. 26-quater",
            description="Interest and Royalties Directive: associated EU company (≥25%, 1 year)",
        )
    sd.regime(
        it, date(2026, 1, 1),
        Src("TUIR art. 89, 47-bis (Normattiva); D.L. 38/2026 art. 11", IT_TUIR.format(89),
            "TUIR art. 87, 89, 47-bis",
            "non concorrono a formare il reddito [...] per il 95 per cento del loro ammontare. "
            "[...] laddove il livello nominale di tassazione risulti inferiore al 50 per cento "
            "di quello applicabile in Italia"),
        participation_exemption_dividends=True, participation_exemption_capgains=True,
        min_holding_pct=None, min_holding_period_months=None, subject_to_tax_condition=True,
        min_subject_to_tax_rate=12, exempt_share_pct=95,
        notes="95% dividend exclusion with no minimum holding (2026 budget rule repealed by "
        "D.L. 38/2026); non-EU payers taxed nominally below 50% of Italy's (12%) are low-tax; "
        "gains PEX 95% after 12 months",
    )
    sd.cfc(
        it, date(2024, 1, 1),
        Src("TUIR art. 167 (Normattiva)", IT_TUIR.format(167), "TUIR art. 167",
            "i soggetti controllanti devono verificare che i soggetti controllati non residenti "
            "sono assoggettati ad una tassazione effettiva inferiore alla metà di quella a cui "
            "sarebbero stati soggetti qualora residenti in Italia"),
        control_threshold_pct=50, low_tax_relative_pct=50, legal_ref="TUIR art. 167",
        effect="Income of a controlled entity taxed below half the Italian tax with >1/3 "
        "passive income is attributed (15% ETR safe harbour).",
    )

    # Neither treaty is modified by the MLI: Italy has not deposited its ratification.
    t = sd.treaty(fr, it, name="Convention between France and Italy (1989)",
                  signed=date(1989, 10, 5), in_force=date(1992, 5, 1), src=Src(
                      "Convention France–Italie (impots.gouv.fr)", FR_IT, None,
                      "signée à Venise le 5 octobre 1989 [...] entrée en vigeur le 1er mai "
                      "1992"))
    start = date(1992, 5, 1)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Italie (impots.gouv.fr)", FR_IT, "Article 10(2)(b)",
        "15 p. cent du montant brut des dividendes dans tous les autres cas"), max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convention France–Italie (impots.gouv.fr)", FR_IT, "Article 10(2)(a)",
        "5 p. cent [...] si le bénéficiaire effectif est une société passible de l'impôt sur "
        "les sociétés qui a détenu [...] pendant une période d'au moins 12 mois [...] au moins "
        "10 p. cent du capital"), max_rate="5", ownership_threshold="10", min_holding_days=365)
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Convention France–Italie (impots.gouv.fr)", FR_IT, "Article 11(2)",
        "l'impôt ainsi établi ne peut excéder 10 p. cent du montant brut des intérêts"),
        max_rate="10")
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Convention France–Italie (impots.gouv.fr)", FR_IT, "Article 12(2)",
        "ne peut excéder 5 p. cent du montant brut des redevances"), max_rate="5")

    t = sd.treaty(it, ae, name="Convention between Italy and the UAE (1995)",
                  signed=date(1995, 1, 22), in_force=date(1997, 11, 5), src=Src(
                      "Convenzioni per evitare le doppie imposizioni (finanze.gov.it)",
                      "https://www.finanze.gov.it/it/Fiscalita-dellUnione-europea-e-"
                      "internazionale/convenzioni-e-accordi/convenzioni-per-evitare-le-doppie-"
                      "imposizioni/", None,
                      "Firma: Abu Dhabi 22.01.1995; Ratifica: L.28.08.1997, n.309 In vigore "
                      "dal : 05.11.1997"))
    start = date(1997, 11, 5)
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convenzione Italia–EAU, L. 309/1997 (Normattiva)", IT_AE, "Article 10(2)(b)",
        "b) il 15 per cento dell'ammontare lordo dei dividendi in tutti gli altri casi"),
        max_rate="15")
    sd.treaty_rate(t, "DIVIDEND", "Article 10", start, Src(
        "Convenzione Italia–EAU, L. 309/1997 (Normattiva)", IT_AE, "Article 10(2)(a)",
        "a) il 5 per cento [...] se l'effettivo beneficiario possiede, direttamente o "
        "indirettamente, almeno il 25 per cento del capitale"),
        max_rate="5", ownership_threshold="25")
    sd.treaty_rate(t, "INTEREST", "Article 11", start, Src(
        "Convenzione Italia–EAU, L. 309/1997 (Normattiva)", IT_AE, "Article 11(1)",
        "sono imponibili soltanto in detto altro Stato se tale residente ne è l'effettivo "
        "beneficiario"), exclusive=True)
    sd.treaty_rate(t, "ROYALTY", "Article 12", start, Src(
        "Convenzione Italia–EAU, L. 309/1997 (Normattiva)", IT_AE, "Article 12(2)",
        "l'imposta così applicata non può eccedere il 10 per cento dell'ammontare lordo dei "
        "canoni"), max_rate="10")
