from __future__ import annotations

from pathlib import Path

from warehouse.generator.render_ods_merge_sql import render


class SqlGeneratorService:
    def render_ods_merge(self, metadata: dict) -> str:
        return render(metadata)

    def write_ods_merge(self, metadata: dict, output_dir: str | Path) -> Path:
        output = Path(output_dir) / f"merge_{metadata['ods_table']}.sql"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.render_ods_merge(metadata), encoding="utf-8")
        return output

