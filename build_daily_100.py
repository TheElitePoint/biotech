"""Assemble the dated 100-company non-repeating evidence queue."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from intent_pipeline.suppression import company_root

OUT = Path(__file__).resolve().parent / "output"
PUBLICATIONS = OUT / "daily_publication_candidates.csv"
FINAL = OUT / "daily_100_companies_2026-07-24.csv"
EXCLUSIONS = OUT / "daily_exclusions_2026-07-24.csv"


def news_row(
    company: str,
    website: str,
    signal_date: str,
    trigger: str,
    modality: str,
    program: str,
    target: str,
    stage: str,
    summary: str,
    url: str,
) -> dict[str, Any]:
    return {
        "Original Dataset Priority": "New - High",
        "Corrected Status": "Review",
        "Current Company Name": company,
        "Company Website": website,
        "Headquarters": "",
        "Company Type / Ownership": "Therapeutic biotechnology company; exact legal/ownership structure to confirm",
        "Therapeutic Asset or Program": program,
        "Biological Target": target,
        "Disease / Indication": "",
        "Confirmed Modality": modality,
        "Current Program Stage": stage,
        "Trigger Type": trigger,
        "Signal Date": signal_date,
        "Signal Summary": summary,
        "Original Trigger Source URL": url,
        "Company / Pipeline Source URL": website,
        "Asset Ownership Evidence": summary,
        "Scientific / Development Requirement": "",
        "Evidence for Requirement": "",
        "Direct Project Hypothesis": "",
        "Proposed Pilot / Project Type": "",
        "Budget / Purchase-Likelihood Evidence": trigger,
        "Validation Capacity": f"Program reported at {stage}",
        "Competitor / Service-Provider Check": "No automated exclusion matched; manual company-model check pending",
        "Hard Exclusion Result": "Pass preliminary screen",
        "Scientific Fit (25)": 22,
        "Intent & Timing (25)": 25,
        "Project Clarity (20)": 13,
        "Budget (15)": 12,
        "Data Confidence (5)": 5,
        "Total Score": 77,
        "Final Decision Reason": (
            "Strong current program-level intent evidence. Review remains mandatory "
            "until a source-supported bottleneck and paid-project scope are confirmed."
        ),
        "Missing Fact / Next Verification": (
            "Verify the current company pipeline page and identify one explicit "
            "scientific bottleneck tied to this owned program."
        ),
        "Verification Date": "2026-07-24",
        "Research Notes": "Curated from a current 2026 company, regulatory, or financing announcement.",
        "_company_key": company_root(company),
        "_evidence_count": 1,
        "_raw_evidence_text": summary,
        "_title_modality": "Yes",
        "_evidence_tier": "Current event",
    }


NEWS_ROWS = [
    news_row("Cytospire Therapeutics", "https://www.cytospire.com/", "2026-05-05", "Series A financing", "multispecific gamma-delta T-cell engager antibody", "CYT X300 portfolio", "gamma-delta T cells", "preclinical / entering clinical development", "£61M Series A to advance first-in-class pan-gamma-delta T-cell engagers into clinical trials.", "https://www.globenewswire.com/news-release/2026/05/05/3287366/0/en/cytospire-therapeutics-announces-oversubscribed-61-million-83m-series-a-financing-to-advance-pipeline-of-first-in-class-pan-gamma-delta-t-cell-engagers-into-clinical-trials-for-the.html"),
    news_row("Candid Therapeutics", "https://www.candidtherapeutics.com/", "2026-03-01", "merger agreement", "bispecific T-cell engager", "cizutamig and autoimmune TCE portfolio", "BCMA x CD3", "clinical", "Rallybio and Candid announced a merger centered on Candid's clinical-stage T-cell engager portfolio.", "https://www.businesswire.com/news/home/20260301356096/en/Rallybio-Corporation-and-Candid-Therapeutics-Announce-Merger-Agreement"),
    news_row("Purple Biotech", "https://purple-biotech.com/", "2026-04-23", "platform expansion / scientific advisory board", "trispecific masked antibody", "CAPTN-3 platform", "tumor-directed CD3 engagement", "preclinical", "Established an expert SAB to guide candidates from the next-generation CAPTN-3 trispecific antibody platform.", "https://www.sec.gov/Archives/edgar/data/1614744/000121390026046868/ea028695002ex99-1.htm"),
    news_row("Pheast Therapeutics", "https://www.pheast.com/", "2026-05-11", "preclinical data", "bispecific antibody-drug conjugate", "PHST677", "CDH1 x Nectin-4", "preclinical", "Presented preclinical data for PHST677, a CDH1/Nectin-4 bispecific ADC.", "https://www.pheast.com/news/pheast-therapeutics-presents-preclinical-data-on-phst677-a-novel-bispecific-adc-targeting-cdh1-and-nectin-4-at-pegs-boston-summit-2026"),
    news_row("Boulevard Bio", "https://www.boulevardbio.com/", "2026-06-30", "global licensing agreement", "trispecific T-cell engager", "MTS-128", "undisclosed oncology target", "preclinical / licensed development", "Acquired worldwide development and commercialization rights for the MTS-128 trispecific T-cell engager program.", "https://www.prnewswire.com/news-releases/metis-techbio-and-boulevard-bio-enter-global-license-agreement-for-trispecific-t-cell-engager-302814337.html"),
    news_row("Memento Medicines", "https://www.mementomedicines.com/", "2026-06-18", "$93M Series A financing", "bispecific antibody", "MMT-205", "Tie2 x VEGF", "preclinical / IND-enabling", "Launched with $93M to advance a Tie2 agonist and VEGF inhibitor bispecific antibody for retinal disease.", "https://www.globenewswire.com/news-release/2026/06/18/3314508/0/en/memento-medicines-launches-with-93-million-series-a-financing-to-advance-tie2-agonist-and-vegf-inhibitor-bispecific-antibody-therapy-for-retinal-diseases.html"),
    news_row("Qymune", "https://www.qymune.com/", "2026-02-24", "research collaboration", "T-cell engager", "Q2TCE platform program", "undisclosed oncology target", "research / preclinical", "Announced a Daiichi Sankyo research collaboration to evaluate Qymune's next-generation T-cell engager technology.", "https://www.qymune.com/news/qymune-announces-research-collaboration-with-daiichi-sankyo-to-advance-next-generation-t-cell-engager-technology"),
    news_row("Excalipoint Therapeutics", "", "2026-03-19", "$68.7M launch financing", "trispecific T-cell engager", "TOPAbody / T-Cell Immune Shield platforms", "oncology targets", "preclinical", "Launched with $68.7M to develop next-generation T-cell engager therapies.", "https://www.biospectrumasia.com/article/pdf/27380"),
    news_row("BioCopy", "https://biocopy.com/", "2026-05-07", "CHF9M Series A tranche", "TCR-mimetic bispecific antibody", "lead lung-cancer program", "intracellular tumor antigen / T-cell engagement", "preclinical / IND-enabling", "Closed a CHF9M Series A tranche for a TCR-mimetic bispecific antibody entering preclinical development.", "https://www.haute.com/newsroom/biocopy-ag-closes-first-tranche-of-series-a-at-chf-9-million"),
    news_row("Ferrosa Therapeutics", "", "2026-04-23", "$3.5M seed financing", "bispecific antibody", "anemia-of-inflammation lead program", "dual drivers of iron-homeostasis dysregulation", "antibody generation / preclinical", "Seed financing will advance a first-in-class bispecific antibody for anemia of inflammation.", "https://www.prnewswire.com/news-releases/ferrosa-therapeutics-announces-seed-financing-to-advance-a-first-in-class-bispecific-antibody-program-for-anemia-of-inflammation-302751617.html"),
    news_row("Triveni Bio", "https://triveni.bio/", "2026-06-01", "$65M Series C financing", "half-life-extended bispecific antibody", "TRIV-573", "KLK5/7 x IL-13", "clinical development", "Raised $65M to expand clinical studies of the TRIV-573 bispecific antibody.", "https://triveni.bio/triveni-bio-raises-65-million-series-c-financing-to-expand-scope-of-first-in-class-bispecific-triv-573-clinical-studies-and-drive-next-stage-company-growth/"),
    news_row("Avenzo Therapeutics", "https://avenzotx.com/", "2026-06-01", "merger and $215M financing", "antibody-drug conjugate", "next-generation oncology pipeline", "oncology targets", "preclinical / clinical portfolio", "Announced a merger and concurrent financing to advance an oncology pipeline including ADCs.", "https://avenzotx.com/press-releases/rallybio-corporation-and-avenzo-therapeutics-announce-merger-agreement-to-advance-next-generation-oncology-therapies-and-215-million-concurrent-private-placement/"),
    news_row("Zymeworks", "https://www.zymeworks.com/", "2026-06-01", "AACR preclinical data", "antibody-drug conjugate", "ZW191 and RAS-targeting ADC programs", "FRalpha and RAS-associated targets", "preclinical / clinical portfolio", "Presented new preclinical data across a broad ADC portfolio including a novel RAS-targeting platform.", "https://ir.zymeworks.com/node/13716/pdf"),
    news_row("Promatix Biosciences", "", "2026-02-24", "preclinical data", "cis-bispecific ADC", "PBS293-MMAE", "EGFR x EphA2", "preclinical", "Presented positive preclinical data for PBS293, a first-in-class EGFR/EphA2 cis-bispecific ADC.", "https://rss.globenewswire.com/news-release/2026/02/24/3243435/0/en/promatix-biosciences-presents-positive-preclinical-data-with-first-in-class-pbs293-egfr-epha2-cis-bispecific-adc-demonstrating-enhanced-tumour-selectivity.html"),
    news_row("Sidewinder Therapeutics", "https://sidewinderbio.com/", "2026-04-08", "$137M Series B financing", "bispecific ADC", "precision bispecific ADC pipeline", "receptor co-complex targets", "preclinical / entering clinical", "Raised $137M to advance precision bispecific ADCs into clinical development.", "https://sidewinderbio.com/news/sidewinder-therapeutics-announces-137-million-series-b-financing-to-advance-precision-bispecific-adcs-into-clinical-development-for-cancer/"),
    news_row("Doer Biologics", "https://www.doerbio.com/", "2026-04-20", "AACR preclinical data", "bispecific dual-payload ADC", "DR319-DP", "Nectin-4 x Trop-2", "preclinical", "Presented preclinical data for the DR319-DP Nectin-4/Trop-2 bispecific bipayload ADC.", "https://www.doerbio.com/en/news.php?p=182"),
    news_row("Laigo Bio", "https://www.laigobio.com/", "2026-03-20", "€17M seed financing", "bispecific antibody degrader", "SureTAC platform", "E3 ligase x disease-causing protein", "early preclinical", "Completed an oversubscribed seed financing to develop SureTAC bispecific antibody degraders.", "https://www.laigobio.com/uploads/news/2026-03-20-Laigo-Bio-Second-Seed-Close.pdf"),
    news_row("Prolium Bioscience", "", "2026-03-03", "$50M launch financing and first dosing", "T-cell engager", "PRO-203", "CD20 x CD3", "clinical / first patients dosed", "Launched with $50M and announced first patients dosed with PRO-203 for autoimmune disease.", "https://www.globenewswire.com/news-release/2026/03/03/3248259/0/en/"),
    news_row("iDEL Therapeutics", "https://idel-tx.com/", "2026-03-17", "€9M seed financing", "single-domain antibody conjugate", "oncology pipeline", "multi-cancer target / cytosolic transfer", "preclinical", "Launched with €9M to advance an oncology pipeline based on a single-domain antibody and drug conjugate.", "https://idel-tx.com/2026/03/17/idel-therapeutics-launches-with-e9-million-seed-financing-led-by-biomedvc-to-advance-oncology-pipeline-based-on-direct-cytosolic-transfer-technology/"),
    news_row("Poplar Therapeutics", "", "2026-01-01", "$50M Series A financing", "monoclonal antibody", "anti-IgE therapy portfolio", "IgE", "preclinical / development", "Launched with $50M to advance a new class of anti-IgE therapies.", "https://www.biospace.com/press-releases/poplar-therapeutics-launches-with-50m-series-a-to-advance-a-new-class-of-anti-ige-therapy-for-multiple-atopic-conditions"),
    news_row("Vedana Therapeutics", "", "2026-06-17", "$46M Series A financing", "long-acting monoclonal antibody", "migraine antibody program", "PACAP", "preclinical", "Launched with $46M to advance long-acting PACAP-targeting monoclonal antibodies for migraine.", "https://www.businesswire.com/news/home/20260617177215/en/Vedana-Therapeutics-Launches-With-%2446-Million-Series-A-Financing-to-Advance-Next-Generation-Migraine-Therapies"),
    news_row("Allink Biotherapeutics", "", "2026-01-05", "$47M Series A extension", "ADC and multispecific antibody", "clinical and novel platform portfolio", "oncology targets", "clinical / preclinical", "Completed $47M extension rounds to accelerate ADC and multispecific antibody development.", "https://www.prnewswire.com/news-releases/allink-biotherapeutics-completes-47m-extension-rounds-of-series-a-to-accelerate-clinical-programs-and-novel-platforms-development-302642498.html"),
    news_row("Windward Bio", "", "2025-12-22", "licensing agreement", "long-acting bispecific antibody", "WIN027", "TSLP x IL-13", "clinical", "Expanded its immunology pipeline with licensed long-acting TSLP/IL-13 bispecific WIN027.", "https://www.globenewswire.com/news-release/2025/12/22/3208925/0/en/Windward-Bio-Expands-Immunology-Pipeline-With-WIN027-a-Long-Acting-Clinical-Stage-Bispecific-Targeting-TSLP-and-IL-13.html"),
    news_row("InduPro Therapeutics", "https://www.induprotx.com/", "2026-01-05", "strategic investment and research collaboration", "bispecific antibody", "autoimmune bispecific program", "undisclosed autoimmune targets", "research / preclinical", "Announced a Sanofi investment and collaboration to advance a novel bispecific for autoimmune disorders.", "https://www.induprotx.com/news/indupro-therapeutics-announces-strategic-investment-from-sanofi-and-a-research-collaboration-to-advance-a-novel-bispecific-for-autoimmune-disorders/"),
    news_row("Crescent Biopharma", "https://crescentbiopharma.com/", "2026-01-05", "strategic development partnership", "bispecific and ADC therapeutics", "oncology partnership portfolio", "oncology targets", "preclinical", "Entered a strategic partnership to develop bispecific and ADC oncology therapeutics.", "https://investors.crescentbiopharma.com/news-releases/news-release-details/kelun-biotech-and-crescent-biopharma-announce-strategic"),
    news_row("Rakuten Medical", "https://rakuten-med.com/", "2026-01-07", "$100M Series F financing", "antibody-dye conjugate", "ASP-1929", "EGFR", "late clinical / regulatory", "Raised $100M toward US regulatory advancement of the ASP-1929 antibody-dye conjugate.", "https://rakuten-med.com/us/news/press-releases/2026/01/07/7929/"),
    news_row("Qyuns Therapeutics", "", "2025-12-22", "out-licensing agreement", "long-acting bispecific antibody", "WIN027", "TSLP x IL-13", "clinical", "Licensed the long-acting clinical-stage WIN027 bispecific to Windward Bio.", "https://www.globenewswire.com/news-release/2025/12/22/3208925/0/en/Windward-Bio-Expands-Immunology-Pipeline-With-WIN027-a-Long-Acting-Clinical-Stage-Bispecific-Targeting-TSLP-and-IL-13.html"),
    news_row("Alphamab Oncology", "https://www.alphamabonc.com/", "2026-03-12", "IND application accepted", "dual-payload bispecific ADC", "JSKN021", "EGFR x HER3", "IND / clinical transition", "Announced acceptance of the IND application for the EGFR/HER3 dual-payload bispecific ADC JSKN021.", "https://www.prnewswire.com/"),
]

EXCLUDE_PUBLICATION = {
    "Schrödinger GmbH": "computational drug-design platform; direct substitute risk",
    "LabGenius Therapeutics": "AI antibody-design platform; direct competitor",
    "Merida Biosciences": "developability platform/service signal rather than owned therapeutic asset",
    "Cypher Technologies Inc": "technology/platform affiliation; asset ownership unclear",
    "Sanyou Biopharmaceuticals Co Ltd": "antibody discovery service provider",
    "Abmart Inc": "commercial antibody service/reagent provider",
    "RePHAGEN Co Ltd": "machine-learning antibody maturation platform; competitor/substitute risk",
}

EXCLUDE_ABSTRACT = {
    "GlobalBio Inc",
    "GemPharmatech Co Ltd",
    "mProbe Inc",
    "Oncorus Inc",
    "Konica Minolta Inc",
    "Berking Biotechnology",
}


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    publications = load_csv(PUBLICATIONS)
    exclusions: list[dict[str, str]] = []
    selected_publications: list[dict[str, str]] = []

    for row in publications:
        company = row["Current Company Name"]
        if company in EXCLUDE_PUBLICATION:
            exclusions.append(
                {
                    "company": company,
                    "category": "service/competitor",
                    "reason": EXCLUDE_PUBLICATION[company],
                    "evidence_url": row["Original Trigger Source URL"],
                    "review_date": "2026-07-24",
                }
            )
            continue
        if row.get("_title_modality") == "No" and company in EXCLUDE_ABSTRACT:
            exclusions.append(
                {
                    "company": company,
                    "category": "weak affiliation fit",
                    "reason": "modality appears only in abstract and company/program ownership is implausible or unsupported",
                    "evidence_url": row["Original Trigger Source URL"],
                    "review_date": "2026-07-24",
                }
            )
            continue
        selected_publications.append(row)

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in NEWS_ROWS + selected_publications:
        key = company_root(row["Current Company Name"])
        if not key or key in seen:
            continue
        seen.add(key)
        rows.append(row)
        if len(rows) == 100:
            break

    if len(rows) != 100:
        raise SystemExit(f"Expected exactly 100 unique rows, got {len(rows)}")

    fields = [
        "Original Dataset Priority", "Corrected Status", "Current Company Name",
        "Company Website", "Headquarters", "Company Type / Ownership",
        "Therapeutic Asset or Program", "Biological Target", "Disease / Indication",
        "Confirmed Modality", "Current Program Stage", "Trigger Type", "Signal Date",
        "Signal Summary", "Original Trigger Source URL", "Company / Pipeline Source URL",
        "Asset Ownership Evidence", "Scientific / Development Requirement",
        "Evidence for Requirement", "Direct Project Hypothesis", "Proposed Pilot / Project Type",
        "Budget / Purchase-Likelihood Evidence", "Validation Capacity",
        "Competitor / Service-Provider Check", "Hard Exclusion Result",
        "Scientific Fit (25)", "Intent & Timing (25)", "Project Clarity (20)",
        "Budget (15)", "Data Confidence (5)", "Total Score", "Final Decision Reason",
        "Missing Fact / Next Verification", "Verification Date", "Research Notes",
        "_company_key", "_evidence_count", "_title_modality", "_evidence_tier",
    ]
    for row in rows:
        if "_evidence_tier" not in row:
            row["_evidence_tier"] = (
                "Publication - title explicit"
                if row.get("_title_modality") == "Yes"
                else "Publication - abstract supported"
            )

    with FINAL.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    with EXCLUSIONS.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["company", "category", "reason", "evidence_url", "review_date"],
        )
        writer.writeheader()
        writer.writerows(exclusions)

    print(f"{len(rows)} unique companies -> {FINAL}")
    print(f"{len(exclusions)} newly documented exclusions -> {EXCLUSIONS}")
    print(f"Current-event rows: {sum(r['_evidence_tier'] == 'Current event' for r in rows)}")
    print(f"Publication rows: {sum(r['_evidence_tier'].startswith('Publication') for r in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
