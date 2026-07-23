# Element Properties and Enthalpy Data

This folder contains the elemental-property datasets used by the descriptor calculation pipeline in `calc_descriptors/`.

The data were converted from `Supplementary Datasets.xlsx` (prepared for the *Nature Communications* submission) into plain-text CSV files so they are version-control friendly and easy to inspect.

## Files

| File | Description |
|---|---|
| `elemental_properties.csv` | Main elemental properties table (English). Each row is one physical/chemical property; columns are the 15 HEA elements plus reference IDs and full citations. |
| `enthalpy.csv` | Binary mixing-enthalpy matrix (kJ/mol) for the 15 HEA elements. |
| `elemental_properties_full.csv` | Extended version that also contains Chinese property names and URLs/literature references. |

## Reference

These tables are the source data used to compute the descriptors stored in the `descriptor/` lakehouse. For the original formatted tables and the complete reference list, please refer to the supplementary materials of the paper.
