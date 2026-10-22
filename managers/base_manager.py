"""Shared CRUD logic for the four dataset managers.

Each manager only declares its file, ID column, category lists and field checks.
"""
from pathlib import Path

import pandas as pd

from utils import validators as v
from utils.data_loader import SCHEMAS, DataError, ValidationError, coerce_types, load_table, save_table
from utils.paths import ACCIDENTS_FILE, get_data_dir


def _none_if_blank(value):
    return None if v.is_blank(value) else (value.strip() if isinstance(value, str) else value)


class BaseManager:
    filename = ""
    id_col = ""
    category_fields: dict = {}   # column -> list of allowed values
    blank_defaults: dict = {}    # column -> value used when blank (e.g. "Unknown")
    links_to_accident = True

    def __init__(self, data_dir=None):
        self.data_dir = Path(get_data_dir() if data_dir is None else data_dir)
        self.columns = SCHEMAS[self.filename]

    @property
    def path(self) -> Path:
        return self.data_dir / self.filename

    # ---- reading -------------------------------------------------------
    def load_data(self) -> pd.DataFrame:
        return load_table(self.path, self.filename)

    def get_all(self) -> pd.DataFrame:
        return self.load_data()

    def get_record(self, record_id):
        df = self.load_data()
        rows = df[df[self.id_col] == str(record_id).strip()]
        return None if rows.empty else self._row_to_dict(rows.iloc[0])

    def _accident_ids(self) -> set:
        return set(load_table(self.data_dir / ACCIDENTS_FILE, ACCIDENTS_FILE)["Accident_ID"])

    @staticmethod
    def _row_to_dict(row) -> dict:
        return {k: (None if pd.isna(val) else val) for k, val in row.items()}

    # ---- cleaning / validation ------------------------------------------
    def _clean(self, record: dict) -> dict:
        """Strip text, turn blanks into None and match categories case-insensitively."""
        clean = {col: _none_if_blank(record.get(col)) for col in self.columns}
        for col, choices in self.category_fields.items():
            value = clean[col]
            if value is None:
                clean[col] = self.blank_defaults.get(col)
                continue
            for choice in choices:
                if str(value).lower() == choice.lower():
                    clean[col] = choice
        if clean.get("Is_Synthetic") is not None:
            clean["Is_Synthetic"] = str(clean["Is_Synthetic"]).lower()
        return clean

    def _field_errors(self, record: dict, unchanged=frozenset()) -> list:
        """Dataset-specific checks (override in subclasses).

        `unchanged` lists columns whose value is identical to the stored row; format checks
        that only apply to newly entered values (e.g. source wording, blank date) skip them.
        """
        return []

    def validate_record(self, record: dict, unchanged=frozenset()) -> list:
        """Return a list of error messages (empty list means the record is valid).

        When editing, `unchanged` names columns the user did not touch. Original source values
        (e.g. 'Slight Injury', a blank Date, '17:02:00') are kept as-is and not re-validated,
        so source-backed rows stay editable without rewriting their raw labels.
        """
        rec = self._clean(record)
        errors = [v.check_id(rec[self.id_col], self.id_col)]
        errors += [v.check_required_text(rec["Data_Source"], "Data_Source"),
                   v.check_bool_like(rec["Is_Synthetic"])]
        for col, choices in self.category_fields.items():
            if col in unchanged:
                continue
            if rec[col] is not None and rec[col] not in choices:
                errors.append(f"{col} must be one of: {', '.join(choices)}.")
        errors += self._field_errors(rec, unchanged)
        if self.links_to_accident:
            err = v.check_id(rec["Accident_ID"], "Accident_ID")
            errors.append(err)
            if err is None and rec["Accident_ID"] not in self._accident_ids():
                errors.append(f"Accident_ID '{rec['Accident_ID']}' does not exist in accidents.csv.")
        return [e for e in errors if e]

    # ---- writing -------------------------------------------------------
    def add_record(self, record: dict) -> dict:
        errors = self.validate_record(record)
        if errors:
            raise ValidationError(errors)
        rec = self._clean(record)
        df = self.load_data()
        if rec[self.id_col] in set(df[self.id_col]):
            raise ValidationError(f"{self.id_col} '{rec[self.id_col]}' already exists.")
        new_row = coerce_types(pd.DataFrame([rec], columns=self.columns))
        df = pd.concat([df, new_row], ignore_index=True) if not df.empty else new_row
        save_table(df, self.path, self.filename)
        return rec

    def update_record(self, record_id, updates: dict) -> dict:
        record_id = str(record_id).strip()
        df = self.load_data()
        match = df.index[df[self.id_col] == record_id]
        if len(match) == 0:
            raise ValidationError(f"{self.id_col} '{record_id}' was not found.")
        merged = self._row_to_dict(df.loc[match[0]])
        merged.update({k: v_ for k, v_ in updates.items() if k != self.id_col})
        merged[self.id_col] = record_id
        original = self._clean(self._row_to_dict(df.loc[match[0]]))
        edited = self._clean(merged)
        unchanged = frozenset(c for c in self.columns if original.get(c) == edited.get(c))
        errors = self.validate_record(merged, unchanged)
        if errors:
            raise ValidationError(errors)
        rec = self._clean(merged)
        # keep any extra (non-schema) source columns on the updated row
        full = {**merged, **rec}
        new_row = pd.DataFrame([full], columns=df.columns)
        pos = match[0]
        df = pd.concat([df.iloc[:pos], new_row, df.iloc[pos + 1:]], ignore_index=True)
        save_table(coerce_types(df), self.path, self.filename)
        return rec

    def delete_record(self, record_id) -> None:
        record_id = str(record_id).strip()
        df = self.load_data()
        keep = df[df[self.id_col] != record_id]
        if len(keep) == len(df):
            raise ValidationError(f"{self.id_col} '{record_id}' was not found.")
        save_table(keep, self.path, self.filename)

    # ---- helpers for linked data ----------------------------------------
    def count_for_accident(self, accident_id) -> int:
        try:
            df = self.load_data()
        except DataError:
            return 0
        return int((df["Accident_ID"] == str(accident_id).strip()).sum())

    def delete_by_accident(self, accident_id) -> int:
        try:
            df = self.load_data()
        except DataError:
            return 0
        keep = df[df["Accident_ID"] != str(accident_id).strip()]
        removed = len(df) - len(keep)
        if removed:
            save_table(keep, self.path, self.filename)
        return removed
