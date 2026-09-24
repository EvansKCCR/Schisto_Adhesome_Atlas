"""Atlas display groups; source orthogroups and inferred trees remain intact."""
INTEGRIN_ALPHA_GROUP = 'Integrin alpha (OG0000401 + OG0001220)'

def atlas_group(orthogroup):
    return INTEGRIN_ALPHA_GROUP if orthogroup in {'OG0000401','OG0001220'} else orthogroup


def merge_memberships(frame):
    data=frame.copy()
    data['Source orthogroups']=data.Orthogroup
    data['Orthogroup']=data.Orthogroup.map(atlas_group)
    def union(values):
        return ', '.join(sorted({token.strip() for value in values for token in str(value).split(',') if token.strip()}))
    return data.groupby('Orthogroup',as_index=False,sort=True).agg({c:union for c in data if c!='Orthogroup'})
