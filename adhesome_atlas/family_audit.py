"""Expose audited family decisions without changing the source screening labels."""
import pandas as pd


SUPPORTED_DECISIONS = {'Retain family assignment', 'Retain; resolves competing family'}
PROVISIONAL_DECISIONS = {'Retain provisionally', 'Family-level provisional only'}


def apply_family_audit(frame):
    out = frame.copy()
    if 'family_decision' in out:
        decision = out.family_decision.fillna('')
        out['audit_classification'] = decision.map(
            lambda value: 'Supported' if value in SUPPORTED_DECISIONS else
            'Provisional' if value in PROVISIONAL_DECISIONS else
            'Ambiguous' if value.startswith('Ambiguous') else 'Unassigned'
        )
        accepted = out.audit_classification.isin(['Supported', 'Provisional'])
        out['reviewed_family'] = out.family.where(accepted)
        out['family_assignment_basis'] = out.family_decision
    elif 'recommended_family' in out:
        out['audit_classification'] = out.grade.map({'A': 'Supported', 'B': 'Supported', 'C': 'Provisional', 'D': 'Unassigned'}).fillna('Unassigned')
        out['reviewed_family'] = out.recommended_family.where(out.audit_classification.ne('Unassigned'))
        out['family_assignment_basis'] = out.rationale
    else:
        out['audit_classification'] = 'Screening hypothesis'
        out['reviewed_family'] = pd.NA
        out['family_assignment_basis'] = 'No family audit supplied for this collection'
    return out
