"""Human-readable and machine-readable views of the same audit."""

from .validator import Report


def markdown(report: Report) -> str:
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")

    s = report.structural_validation
    ling = report.linguistic_validation
    lines = [
        "# Fleng curriculum validation report",
        "",
        "DRAFT — human review required. This report does not authorize publication.",
        "",
        f"Raw file SHA-256: `{report.raw_sha256}`.",
        "",
        f"Publication SHA (existing importer): `{report.publication_sha256}`.",
        "",
        "## Structural validation",
        "",
        "| Metric | Count/status |",
        "| --- | --- |",
    ]
    lines += [f"| {cell(k)} | {cell(v)} |" for k, v in s.items()]
    lines += [
        "",
        "## Linguistic validation",
        "",
        "A dataset match is evidence of attestation, not proof of the intended sense. "
        "No vocabulary entry is automatically marked verified. "
        "No grammar correctness claim follows from structural success.",
        "",
        "```json",
        __import__("json").dumps(ling, ensure_ascii=False, indent=2),
        "```",
        "",
        f"Sources: `{report.sources}`. AI review: `{report.ai_review}`.",
        "",
        f"Severity counts: `{report.severity_counts}`.",
        "",
        f"Safe normalization proposals: {len(report.proposed_fixes)}.",
        "",
        "## Courses",
        "",
        "| Course | Level | Issues | Recommendation |",
        "| --- | --- | --- | --- |",
    ]
    lines += [
        f"| {c['course_id']} | {c['level']} | {c['issues']} | {c['recommendation']} |"
        for c in report.courses
    ]
    lines += [
        "",
        "## Issues and review queue",
        "",
        "All translation/source statuses and provenance are in the companion JSON. "
        "Missing datasets mean every translation still needs human review. "
        "The following entries distinguish reproducible defects from advisory observations.",
        "",
        "| ID | Course / lesson / item | Category / severity | Source / confidence | "
        "Evidence | Suggested fix | Review |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for i in report.issues:
        lines.append(
            "| "
            + " | ".join(
                map(
                    cell,
                    [
                        i.issue_id,
                        f"{i.course_id} / {i.lesson_id} / {i.item_id}",
                        f"{i.category} / {i.severity}",
                        f"{i.source['type']} / {i.confidence}",
                        i.evidence,
                        i.suggested_fix,
                        i.review_status,
                    ],
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"
