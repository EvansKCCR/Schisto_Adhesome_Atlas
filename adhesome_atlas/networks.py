"""Session networks are created by users through STRING query/import."""
import pandas as pd

def mapping_export(code):
    return pd.DataFrame(columns=['queryItem','stringId','identity','bitscore','mapping_source'])
